# Document Intelligence Engine -- Test Strategy

## Unit tests (`platform/kernel`, provider-agnostic)
- Text extraction: PDF and DOCX fixtures (a handful of real, small,
  hand-crafted sample files checked into `tests/fixtures/`, not
  generated at test time) -- confirm plain text comes out correctly,
  including at least one deliberately malformed/corrupt file per format
  to confirm graceful failure (not a crash) with a clear `error_detail`.
- `ExtractedField`/`ExtractionResult` (de)serialization -- round-trip
  through `raw_extraction_json` storage and back.

## Provider tests -- `MockDocumentExtractionProvider`, established before `LLMDocumentExtractionProvider`
Per this project's existing TD-020 precedent (Job Intelligence's
`MockProviderClient` requirement, same reasoning applies here): no test
may call a real LLM API. `MockDocumentExtractionProvider` implements
`DocumentExtractionProvider` against fixture inputs, returning
deterministic `ExtractionResult`s, including:
- A high-confidence, clean extraction (happy path).
- A low-confidence extraction (tests the review-gate behavior actually
  matters, not just exists).
- A partial extraction (some fields present, others `None`) -- confirms
  the pipeline doesn't assume every field is always populated.
- A provider `health_check()` failure -- confirms the API surfaces this
  usefully rather than a bare 500.

`LLMDocumentExtractionProvider` itself gets a **separate, explicitly
manual/opt-in** test tier (not run in the default suite, not part of
the coverage number that gates Stage 1's Definition of Done) that
exercises it against the real Claude API with one real sample CV, run
deliberately by a human before considering the provider implementation
done -- this is a real external dependency and cost, not something to
silently run on every `pytest` invocation.

## Integration tests (CareerOS `document_intelligence_service`)
- Full pipeline against `MockDocumentExtractionProvider`: upload ->
  extract -> review (GET) -> apply -> confirm the resulting Career DNA
  records exist, are correctly attributed (`AI_EXTRACTED`, never
  `USER_ENTERED`), and pass through Sprint 2's existing invariants
  (taxonomy dedup, ownership scoping) automatically -- i.e., a
  Sprint-2-level test like `test_skill_taxonomy_deduplicated_across_persons`
  should also hold true for AI-extracted skills, and a test should
  confirm this directly rather than assume it.
- **The TD-019 write-boundary test**, specifically: assert (via
  `ast`-based static inspection of `document_intelligence_service.py`'s
  imports, or an equivalent import-boundary check) that no Career DNA
  model (`app.models.person`, `app.models.employment`,
  `app.models.skills`, etc.) is imported directly -- only the service
  modules. This is the actual enforcement mechanism TD-019 asked for,
  not just a written policy.
- Apply-without-extract-first must 404/409, not silently no-op.
- Deleting a `Document` cascades its `DocumentExtractionRun`s but does
  NOT retroactively delete already-applied Career DNA data (confirmed
  by a real test, not just asserted in the architecture doc).

## API tests
- Standard CRUD/ownership-scoping pattern this project has already
  established for every Career DNA router (cross-user isolation,
  auth-required, 404-not-found) applied identically to the new
  `/document-intelligence/*` endpoints.
- Multipart upload validation: reject non-PDF/DOCX content types with
  422, not a downstream crash during text extraction.

## Coverage target
Matching this project's now-standard bar: ≥90% on
`document_intelligence_service.py` and the kernel's
`document_intelligence` package, measured with the existing
`.coveragerc` `concurrency = greenlet` configuration (already proven
necessary for this codebase's async services, per TD-R11 -- must be
confirmed to also apply correctly to any new kernel-level async code
before Stage 1 is considered done, not assumed to carry over).
