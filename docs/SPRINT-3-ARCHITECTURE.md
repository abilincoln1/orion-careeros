# Sprint 3 Architecture -- Job Intelligence Platform (Design Only)

**Status: DESIGN ONLY. No implementation authorized by this document.**
Per the Sprint 3 directive, Phase 5, this covers System Architecture,
Module Diagram, Domain Model, Database Design, Service Boundaries, and
Provider Interface Specification for all five required components: CV
Intelligence, Job Intelligence, Matching Engine, Recruiter Watchlist,
and Interview Pipeline. Career DNA (Sprint 2, `v0.2.0-sprint2`) is used
as-is -- no redesign proposed here, per the directive's explicit
instruction.

## 1. System Architecture

```
                         Career DNA (Sprint 2, accepted)
                                    |
                    (read by every service below via person_id)
                                    |
   +----------------+   +----------------+   +------------------+
   | CV Intelligence|   |Job Intelligence|   |    Matching      |
   |    Service     |-->|    Service     |-->|     Engine       |
   +----------------+   +----------------+   +------------------+
           |                     |                     |
           v                     v                     v
     writes to Career DNA   Job / JobListing      MatchResult
     (Skill, Employment,    (provider-agnostic)   (explainable score)
     Education, etc. via
     the EXISTING Sprint 2
     write paths -- no new
     write path invented)
                                                          |
                                                          v
                                              +------------------------+
                                              |  Recruiter Watchlist   |
                                              |  (user-managed CRM)    |
                                              +------------------------+
                                                          |
                                                          v
                                              +------------------------+
                                              |   Interview Pipeline   |
                                              |  (workflow + reports)  |
                                              +------------------------+
```

Every new service reads Career DNA through the existing Sprint 2 API
(`/career-dna/*`) or, for backend-to-backend calls within the same
process, the existing service-layer functions directly -- no service
below is authorized to write to Career DNA tables through any path
other than the services `app/services/{person,employment,skill,
evidence}_service.py` already expose. This is a hard boundary: it means
CV Intelligence's extraction output becomes Career DNA data only by
calling those existing functions (e.g. `skill_service.add_person_skill`),
never by inserting rows directly. This keeps every Architecture Review
must-fix guarantee from ADR 0004 (taxonomy dedup, derived
attribution_source, orphan cleanup) automatically enforced for
AI-extracted data too, with zero new code needed to re-implement them.

## 2. Domain model additions

All new tables are `person_id`-scoped (foreign key to `person.id`,
`ondelete="CASCADE"`), following the exact pattern established in
ADR 0004, with `UUIDPrimaryKeyMixin`/`TimestampMixin` reused, not
reinvented.

### CV Intelligence
- **CVDocument**: `id`, `person_id`, `original_filename`, `storage_ref`
  (not the raw bytes -- see `platform/shared_services` File Storage
  capability, currently reserved/not implemented; this service is
  blocked on that or an interim local-storage shim, see Open Question 1
  below), `mime_type`, `uploaded_at`, `status`
  (`pending` / `processed` / `failed`), `error_detail`.
- **CVExtractionRun**: `id`, `cv_document_id`, `started_at`,
  `completed_at`, `model_used` (which extraction model/version, for
  reproducibility and future re-extraction), `extraction_confidence`
  (overall, 0-1), `raw_extraction_json` (the full structured output
  before it's written into Career DNA, kept for audit/debugging --
  **never itself the source of truth once written**, see below).

### Job Intelligence
- **JobProvider**: `id`, `name` (e.g. "reed", "totaljobs"),
  `provider_type` (`api` / `rss` / `manual_import`), `is_active`,
  `credentials_ref` (pointer to a secret, never the secret itself in
  this table).
- **JobListing**: `id`, `provider_id`, `provider_external_id` (the
  listing's ID in the source system, unique per provider -- this is the
  actual dedup key, not job title/company matching), `title`,
  `company_name_raw`, `company_id` (nullable FK to a future Company
  Intelligence entity, out of scope this sprint), `description_raw`,
  `location_raw`, `salary_min`, `salary_max`, `salary_period`, `posted_at`,
  `expires_at`, `source_url`, `ingested_at`, `raw_payload_json` (the
  provider's original response, for re-parsing if extraction logic
  improves later).
- **JobListingSkill** / **JobListingTechnology**: association tables,
  extracted from `description_raw` the same way CV Intelligence extracts
  from a CV -- deliberately reusing the same extraction service (see
  Service Boundaries) rather than building a second, parallel extractor.

### Matching Engine
- **MatchResult**: `id`, `person_id`, `job_listing_id`, `overall_score`
  (0-100), `computed_at`, `model_version` (the scoring model/weights
  version -- required for the "why did this score change" question that
  is certain to come up).
- **MatchScoreComponent**: `id`, `match_result_id`, `dimension`
  (enum: `skills` / `technologies` / `employment_history` / `industry` /
  `salary` / `location` / `work_preference`), `score` (0-100),
  `weight`, `explanation` (a short, generated human-readable string --
  see Section 6, Matching Engine, for why this table exists as its own
  entity rather than a JSON blob on `MatchResult`).

### Recruiter Watchlist
- **Recruiter**: `id`, `person_id` (the CareerOS user who owns this CRM
  entry, not the recruiter's own account -- this is explicitly a
  user-managed CRM, not a two-sided platform), `full_name`, `agency_id`
  (nullable FK to `Agency`), `email`, `phone`, `linkedin_url`, `notes`.
- **Agency**: `id`, `name`, `website`.
- **RecruiterContact**: `id`, `recruiter_id`, `contact_type`
  (`call`/`email`/`message`/`meeting`), `occurred_at`, `notes`,
  `follow_up_due_at` (nullable).
- **RecruiterCompanyRelation**: association table, `recruiter_id` +
  `company_id` (which companies a recruiter is known to work with).

### Interview Pipeline
- **Application**: `id`, `person_id`, `job_listing_id` (nullable --
  an application can exist for a job not sourced through Job
  Intelligence, e.g. a direct application), `recruiter_id` (nullable),
  `status` (enum, the exact workflow from the directive: `applied` /
  `recruiter_contact` / `interview_1` / `interview_2` / `technical` /
  `offer` / `accepted` / `rejected`), `status_changed_at`,
  `status_history_json` (append-only log of every transition with
  timestamp -- required for the dashboard/reporting requirement; a
  single `status` column alone cannot answer "how long did each stage
  take").
- **InterviewEvent**: `id`, `application_id`, `stage` (mirrors the
  `Application.status` enum values that represent actual interview
  stages), `scheduled_at`, `completed_at`, `notes`, `outcome`
  (`passed`/`failed`/`pending`/`cancelled`).

## 3. Provider Interface Specification (Job Intelligence)

Every job provider (Reed, TotalJobs, CV-Library, JobServe, Indeed, or a
future manual-import "provider") implements one interface:

```python
class JobProviderClient(Protocol):
    provider_name: str  # matches JobProvider.name

    async def fetch_listings(
        self, since: datetime | None, cursor: str | None
    ) -> ProviderFetchResult:
        """Returns a page of raw listings plus a cursor for the next
        page, or None if this page is the last. Providers using RSS
        return the same shape -- 'cursor' may just be a timestamp for
        RSS providers with no real pagination token."""

    def normalize(self, raw_listing: dict) -> JobListingCreate:
        """Maps this provider's raw shape onto the provider-agnostic
        JobListingCreate schema. This is the ONLY place provider-specific
        field names are known anywhere in the codebase -- Matching
        Engine, dashboards, and every other consumer only ever see the
        normalized shape."""

    async def health_check(self) -> bool:
        """Used by an operational dashboard to show which providers are
        currently reachable, independent of the last successful ingest
        time."""
```

**Explicit constraint, per the directive:** an implementation may only
use a provider's official API, an RSS feed the provider explicitly
permits, or user-authorized/manual import. No implementation of this
interface may scrape a page not intended for programmatic access, or
automate a workflow a provider's terms of service prohibit. This is not
a soft guideline -- a provider client that violates it is a rejected PR,
not a technical-debt entry.

**Ingestion boundary:** a scheduled job (mechanism TBD -- likely the
Platform Kernel's reserved `shared_services` Scheduling capability, see
Open Question 2) calls `fetch_listings` per active provider, runs
`normalize`, and **upserts** into `JobListing` keyed on
`(provider_id, provider_external_id)` -- never a blind insert, since
providers re-list/refresh postings.

## 4. Service Boundaries

- **CV Intelligence** owns: parsing, extraction, and the *decision* of
  what to write into Career DNA. It does NOT own the write itself -- it
  calls the existing `person_service`/`employment_service`/
  `skill_service` functions, meaning every Sprint 2 invariant (dedup,
  ownership scoping, derived attribution) applies automatically. A
  CV-extracted skill starts at `attribution_source = self_reported`
  (or a new value, see Open Question 3) -- it is explicitly NOT
  automatically `verified`; only linked Evidence does that, per ADR 0004
  Decision 6, and nothing about this sprint changes that guarantee.
- **Job Intelligence** owns: provider integration, normalization,
  storage, and skill/technology extraction from listings (reusing the
  same extraction service CV Intelligence uses -- one extraction
  capability, two call sites, not two implementations).
- **Matching Engine** owns: reading Career DNA + a `JobListing` and
  producing a `MatchResult`. It is read-only with respect to both --
  it never writes to Career DNA or Job Intelligence tables, only to its
  own `MatchResult`/`MatchScoreComponent` tables. This keeps the
  matching model swappable/re-computable without touching source data.
- **Recruiter Watchlist** owns: `Recruiter`, `Agency`,
  `RecruiterContact`. It is explicitly NOT connected to any automated
  outreach capability -- there is no service boundary here for sending
  messages, by design, per the directive.
- **Interview Pipeline** owns: `Application`, `InterviewEvent`, and the
  status-transition workflow. It reads (does not own) `JobListing` and
  `Recruiter` via nullable FKs.

## 5. Database design notes

- Every new table continues the `orion-governance/architecture/
  ArchitectureReviewChecklist.md` conventions already validated in
  Sprint 2: real FKs wherever the relationship isn't genuinely
  polymorphic, DB-level uniqueness for anything requiring dedup
  (`(provider_id, provider_external_id)` on `JobListing`), and
  `ondelete="CASCADE"` from `person_id` throughout.
- `MatchResult`/`MatchScoreComponent` are NOT `ondelete="CASCADE"` from
  `JobListing` -- a listing expiring or being removed should not
  silently delete historical match data a user may still want to see
  ("here's a job I matched well with, that's now gone"). Explicit
  soft-delete/expiry on `JobListing` instead of hard delete is
  recommended (Open Question 4).
- Migration sequencing: Career DNA schema (Sprint 2) is a hard
  prerequisite (already satisfied); no new migration in this sprint's
  design touches `platform/kernel` or any Sprint 2 table.

## 6. Matching Engine -- scoring design

A transparent, explainable model, not a black-box score:

1. For each dimension (skills, technologies, employment history,
   industry, salary, location, work preference), compute a 0-100
   sub-score using a dimension-specific, independently-testable
   function (e.g. skills: Jaccard-style overlap between the person's
   `PersonSkill` set and the listing's extracted `JobListingSkill` set,
   weighted by `PersonSkill.proficiency`).
2. Combine sub-scores via a configurable weight vector (see
   `config/config.example.yaml`'s existing placeholder for "matching
   weights" -- this sprint's design is the first real consumer of that
   placeholder, closing TD-010).
3. Store each dimension's score AND a short generated explanation
   string in `MatchScoreComponent` -- this is why it's a separate table
   from a JSON blob: it must be independently queryable ("show me
   everyone who matched well on skills but poorly on salary") for the
   dashboard requirement, not just displayable.
4. `MatchResult.model_version` lets a future re-scoring (new weights,
   new algorithm) be computed alongside old results without
   overwriting history -- the same "don't overwrite, create a new
   record" principle ADR 0004 established for Employment promotions.

## 7. Open questions requiring Chief Architect input before Phase 6 review can close

Per the directive's working principle "raise uncertainties instead of
making assumptions," these are named explicitly rather than resolved by
guessing:

1. **File storage for CVDocument.** `platform/shared_services` lists a
   File Storage capability as reserved/not implemented. CV Intelligence
   needs *somewhere* to store uploaded CVs. Options: (a) implement a
   minimal File Storage kernel capability now, ahead of its originally
   planned sprint, or (b) an interim CareerOS-local storage shim, later
   migrated. Recommend (a) if any other near-term product need exists,
   otherwise (b) to avoid speculative platform work (per
   `ArchitecturePrinciples.md` principle 7).
2. **Scheduling for provider ingestion.** Same situation --
   `shared_services` Scheduling is reserved/not implemented. A cron-like
   mechanism is needed. Recommend using this as the actual trigger to
   implement the Scheduling kernel capability, since (unlike File
   Storage) there's no reasonable CareerOS-local substitute for
   recurring background jobs that wouldn't itself become throwaway code.
3. **CV-extracted skill attribution_source.** Should AI-extracted (not
   user-typed, not evidence-linked) data use the existing
   `self_reported` value, or does this sprint need a fourth
   `AttributionSource` value (e.g. `ai_extracted`) to distinguish "the
   user typed this" from "AI read this off a CV the user uploaded"?
   This is a real product-truth question, not just a technical one --
   recommend Chief Architect + a product decision, not an engineering
   default.
4. **JobListing lifecycle.** Hard delete vs. soft-delete/expiry when a
   provider stops returning a listing. Recommend soft-delete
   (`expires_at`/`is_active`) to preserve historical `MatchResult` data,
   but flagging for explicit confirmation since it has real storage-growth
   implications at scale.

## 8. What Phase 6 (Architecture Review) should independently check

Per `orion-governance/architecture/ArchitectureReviewChecklist.md`, an
independent reviewer (not this document's author) should specifically
verify: whether the CV Intelligence -> Career DNA write boundary
(Section 4) is actually enforceable in code review, not just stated
here; whether `MatchScoreComponent` as a separate table vs. embedding in
`MatchResult` is the right call at real scale; and whether the Provider
Interface (Section 3) actually accommodates RSS-only providers cleanly,
or whether `fetch_listings`'s cursor semantics silently assume
API-style pagination.
