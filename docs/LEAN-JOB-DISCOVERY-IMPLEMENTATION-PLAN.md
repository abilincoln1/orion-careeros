# Lean Job Discovery Implementation Plan

**Per directive Section 13.** Existing architecture (`docs/SPRINT-3-ARCHITECTURE.md`) inspected first; this plan states what's built now, reused, deferred, or rejected — not a redesign.

## Build now
- `JobProvider` — minimal: `id`, `name`, `is_active`. No `provider_type`/`credentials_ref` yet — one provider, no auth needed (Arbeitnow's public API requires no key), so those fields would be speculative until a second, authenticated provider is actually added.
- `JobListing` — `id`, `provider_id`, `provider_external_id` (dedup key), `title`, `company_name_raw`, `location_raw`, `is_remote`, `salary_min`, `salary_max`, `salary_currency`, `salary_disclosed` (bool — explicit, not inferred, per Section 4's "mark salary as unknown" instruction), `description_raw`, `source_url`, `posted_at`, `discovered_at`, `raw_payload_json`.
- `JobProviderClient` protocol + one real implementation: `ArbeitnowProvider`.
- `job_discovery_service.py` — derives search criteria from Career DNA (current/most recent `Employment.role_title_raw`, `PersonSkill` names) plus request-level overrides for location/salary/remote (see "Rejected" below for why), calls the provider, upserts listings (dedup on `provider_external_id`).
- One API endpoint: `POST /job-discovery/discover`.
- Tests per Section 14's four categories.

## Reuse, unmodified
- Career DNA's existing `Person`, `Employment`, `PersonSkill` — read-only, via existing service functions where they exist, direct read queries where they don't (no new write path to Career DNA from this feature at all).
- The `DocumentExtractionProvider`/`MockDocumentExtractionProvider` pattern as the template for `JobProviderClient`'s shape — same abstraction style, not the same code (different domain).
- `config/config.example.yaml`'s existing (stale) salary placeholder — corrected to £40,000–£110,000 and wired to actual settings, not left as unused documentation.

## Deferred (not technical debt — explicit scope control, per Section 20)
- `JobListingSkill`/`JobListingTechnology` association tables and description-text skill extraction — the original design's "reuse the CV extraction service" idea is sound but not required for a first discovery slice; deferred until ranking/filtering by skill-overlap is actually built.
- `company_id` FK to a future Company entity — nullable and unused until Company Intelligence exists.
- Full CRUD API for `CareerGoal`/`LocationPreference`/`SalaryPreference`/`WorkPreference` — these remain schema-only. **Decision, stated explicitly:** rather than build a full preference-management API (real scope expansion, not part of Job Discovery's own job), the discovery endpoint accepts optional per-request overrides (`location`, `remote_ok`, `salary_min`, `salary_max`); when omitted, defaults come from `DiscoverySettings` (new, config-driven — see Section 4 compliance below), *and* from any existing `SalaryPreference`/`LocationPreference` row for the person, read directly (a plain `SELECT`, not a new write path) if one exists. Career DNA remains the sole source of truth; no second profile model is created.
- `JobProvider.provider_type`/`credentials_ref` — deferred until a second, authenticated provider is actually added (Arbeitnow needs neither).

## Rejected as unnecessary for this slice
- Multi-provider framework — one provider only, per the directive.
- Any scoring/ranking beyond the provider's own result order — no Matching Engine.
- LinkedIn/Indeed integration — no authorized access route exists; rejected outright, not worked around.

## Section 4 (salary) compliance, stated explicitly
`DiscoverySettings.SALARY_MIN`/`SALARY_MAX` (default £40,000/£110,000) live in `app/core/config.py` as real, overridable settings — not a literal buried in logic. Listings with no disclosed salary are retained with `salary_disclosed=False`, never assigned an invented figure.
