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

> **Superseded (added post-Phase-6, Chief Architect redirect):** this
> section, and the related items in Section 9, are superseded by
> `docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md` and
> `docs/adr/0006-document-intelligence-engine.md`. The Chief Architect
> redirected this capability from a CareerOS-local "CV Intelligence"
> parser to a genuine Platform Kernel "Document Intelligence Engine,"
> reusable by future ORION products and extensible to document types
> beyond CVs. Left below unedited, per this project's convention of
> superseding rather than silently rewriting already-independently-
> reviewed design documents (this section was itself part of what
> `docs/SPRINT-3-ARCHITECTURE-REVIEW.md` approved with conditions).
- **CVDocument**: `id`, `person_id`, `original_filename`, `storage_ref`
  (opaque string, meaningful only to the `StorageAdapter` implementation
  in use -- never parsed or interpreted outside it), `mime_type`,
  `uploaded_at`, `status`
  (`pending` / `processed` / `failed`), `error_detail`.

  **Storage abstraction, per Chief Architect Decision 1:** a
  `StorageAdapter` interface, not a bare field:
  ```python
  class StorageAdapter(Protocol):
      async def store(self, person_id: uuid.UUID, filename: str, content: bytes) -> str:
          """Returns the opaque storage_ref to persist on CVDocument."""

      async def retrieve(self, storage_ref: str) -> bytes: ...

      async def delete(self, storage_ref: str) -> None: ...
  ```
  Sprint 3 implements exactly one `StorageAdapter`: a CareerOS-local
  filesystem (or local-object-store) implementation, per Decision 1's
  explicit instruction not to build a Platform Kernel File Storage
  capability yet. The interface itself is what makes a later migration
  to a shared Platform capability a swap of the adapter, not a rewrite
  of CV Intelligence -- this was the whole point of Decision 1's
  "design behind an interface" instruction, and the original design
  omitted it; this is the independent Phase 6 review's Must-fix #1.
- **CVExtractionRun**: `id`, `cv_document_id`, `started_at`,
  `completed_at`, `model_used` (which extraction model/version, for
  reproducibility and future re-extraction), `extraction_confidence`
  (overall, 0-1), `raw_extraction_json` (the full structured output
  before it's written into Career DNA, kept for audit/debugging --
  **never itself the source of truth once written**, see below).

### Job Intelligence
- **JobProvider**: `id`, `name` (e.g. "reed", "totaljobs"),
  `provider_type` (`api` / `rss` / `manual_import`), `is_active`,
  `credentials_ref` (an opaque string identifying an entry in the
  runtime environment's secret store -- for Sprint 3, this means an
  environment-variable name, e.g. `"REED_API_KEY"`, resolved at request
  time by the provider client, never persisted in the database or
  logged. This is intentionally the simplest mechanism that satisfies
  "never the secret itself in this table"; migrating to a real secrets
  manager later only changes how `credentials_ref` is resolved, not its
  meaning. Independent Phase 6 review Must-fix #4: the original design
  left this undefined.).
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
  `offer` / `accepted` / `rejected`), `status_changed_at`.

  **Status history, per independent Phase 6 review Must-fix #2:** the
  original design used a `status_history_json` blob on `Application`
  for the dashboard/reporting requirement. This directly contradicts
  this project's own established principle from ADR 0004 Decision 3 --
  "history is preserved as new records, not overwritten or embedded in
  a mutable blob" -- the exact defect the Employment-promotion-chaining
  fix (must-fix #1 in Sprint 2's own review) corrected. A JSON blob is
  also unindexed and unqueryable at the database level, and this
  project has already been bitten once by JSON-serialization edge cases
  (TD-R10, the validation-handler crash). Corrected design: a separate
  **ApplicationStatusTransition** table instead:
  - **ApplicationStatusTransition**: `id`, `application_id`,
    `from_status` (nullable, null for the initial `applied` row),
    `to_status`, `occurred_at`, `notes` (optional). `Application.status`
    remains as a denormalized "current state" column for fast reads
    (updated in the same transaction as the new transition row is
    inserted -- never edited independently of one), but the
    authoritative history is this table, queryable like any other data
    ("average time in `interview_1`" becomes a real aggregate query, not
    a JSON-parsing exercise).
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
        """Returns one page of listings. See ProviderFetchResult below --
        independent Phase 6 review Must-fix #3: the original design
        referenced this type without defining it, and left the
        RSS-vs-API pagination question as an unresolved footnote instead
        of a real contract."""

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


@dataclass
class ProviderFetchResult:
    raw_listings: list[dict]
    next_cursor: str | None
    """None means this page is the last -- true for both an
    exhausted API pagination sequence AND a fully-read RSS feed. There
    is exactly one exhaustion signal, not two, so calling code never
    needs to know which kind of provider it's talking to."""

    @property
    def is_exhausted(self) -> bool:
        return self.next_cursor is None


# Pagination contract, resolved explicitly (was previously left
# ambiguous -- see above):
# - API-style providers: cursor is that API's real pagination token.
# - RSS-style providers: cursor is the ISO timestamp of the newest
#   item processed so far. On the next call, an RSS provider filters
#   out anything at or before that timestamp and returns next_cursor as
#   the new newest timestamp, or None once nothing newer than `since`
#   remains in the feed. This means RSS providers implement genuine
#   (if coarse) pagination against the interface, rather than a special
#   case -- callers never branch on provider_type to decide how to call
#   fetch_listings.
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

## 7. Architectural decisions (resolved by Chief Architect Directive, Sprint 3 v1.1)

The four open questions originally posed here are resolved. Full
reasoning is recorded in **ADR 0005**; summarized here for this
document's own completeness:

1. **File storage for CVDocument** -- CareerOS-local `StorageAdapter`
   (Section on CVDocument above), not a Platform Kernel capability, per
   Decision 1. Interface designed so a later migration is an adapter
   swap, not a rewrite.
2. **Scheduling for provider ingestion** -- built as a reusable Platform
   Kernel capability, per Decision 2, since recurring ingestion is
   infrastructure, not CareerOS-specific logic.
3. **CV-extracted attribution** -- a fourth (in fact, per Decision 3, a
   broader) set of `AttributionSource` values is introduced:
   user-entered, AI-extracted-from-documents, imported-from-external-
   systems, and verified-manually. AI-extracted data is explicitly never
   classified as `self_reported`. This changes `app/models/enums.py`'s
   `AttributionSource` enum for Career DNA itself, not just new Sprint 3
   tables -- flagged as a real Sprint 2 schema touch-point despite
   Career DNA being otherwise "use as-is, no redesign" (see Section 9
   below).
4. **JobListing lifecycle** -- soft-delete/expiry (`expires_at`/
   `is_active`), per Decision 4, to preserve historical `MatchResult`,
   `Application`, and `RecruiterContact` references.

## 8. Independent Phase 6 review -- findings

Performed as an adversarial third-party-PR review, per the Sprint 3 v1.1
directive, not a self-review. Full findings, resolutions, and the ARB
recommendation are in `docs/SPRINT-3-ARCHITECTURE-REVIEW.md`. The
Must-fix items found (status-history-as-JSON contradicting ADR 0004's
own history-preservation principle; an undefined `ProviderFetchResult`
type; unresolved RSS/API pagination ambiguity; an unspecified
`credentials_ref` mechanism; a File Storage field with no interface
behind it) are already resolved directly in this document, above,
following this project's established convention (see
`docs/SPRINT-2-ARCHITECTURE-REVIEW.md`) of fixing the spec in place
rather than only describing the fix in a separate report.

## 9. Remaining items for Stage 1 (CV Intelligence) implementation to address

Not blocking Phase 6 approval, but must be satisfied before Stage 1 is
considered done, per `orion-governance/engineering/DefinitionOfDone.md`:

- **Enforcing the CV Intelligence -> Career DNA write boundary
  (Section 4).** Stating "CV Intelligence only writes through existing
  service functions" is not self-enforcing. Stage 1 must include either
  a lint/import-boundary check (e.g. forbidding
  `app.services.cv_intelligence` from importing `app.models.person`,
  `app.models.employment`, `app.models.skills` directly) or, at minimum,
  a code-review checklist item, and a test that would fail if the
  boundary were violated.
- **Provider test fixtures.** No provider implementation should be
  tested against a real external API in CI. Stage 2 (Job Provider
  Framework) needs a `MockProviderClient` implementing
  `JobProviderClient` against fixture data, established before the
  first real provider is built, not after.
- **`MatchResult`/`MatchScoreComponent` cascade behavior.** Both should
  cascade-delete from `Person` (`ondelete="CASCADE"`, consistent with
  every other Career-DNA-adjacent table), independent of the
  deliberately-NOT-cascading-from-`JobListing` behavior already
  specified in Section 5.
- **`MatchScoreComponent.explanation`, AI-readiness.** Currently
  specified as free text. Recommend pairing it with a structured
  `reason_code` enum (e.g. `strong_skill_overlap`,
  `salary_below_range`) alongside the human-readable string, so a
  future AI consumer (or the dashboard itself) can reason over match
  quality without parsing prose. Not a blocker; a Worth-fixing item for
  Stage 3.
