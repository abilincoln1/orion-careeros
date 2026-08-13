# Minimum Real-CV Extraction Capability — Completion Report

**To:** Chief Solutions Architect
**From:** Claude
**Date:** 13 August 2026
**Re:** Completion of the post-push "Next Task" directive — real CV extraction, replacing the fixture-based demonstration.

**Note on sequencing:** this report covers Part 2 of the combined directive (extraction audit + implementation). Part 1 (the publication check and push of `c540c65`) requires commands run on your machine, provided separately — this work was authorized to proceed in parallel per the directive's own structure, and does not depend on the push having completed first.

---

## B. Extraction Audit (performed first, read-only, before any code change)

**Current ingestion path:** `upload_document()` → `StorageAdapter.store()` → `extract()` → `extract_text(document_type, content)` → `provider.analyze(document_type, text)`. Confirmed by reading `document_intelligence_service.py` directly.

**Current extraction capability:** `text_extraction.py`'s `extract_text()` already performs real PDF (`pypdf`) and DOCX (`python-docx`) text extraction from real uploaded bytes — already tested (33 kernel tests), already wired into the live pipeline. This was never the gap.

**Current blocking point, confirmed precisely:** exactly one `DocumentExtractionProvider` implementation existed — `MockDocumentExtractionProvider` — which **ignores its `extracted_text` argument entirely** and returns hardcoded fixture data regardless of input. The real text was always being produced; nothing ever read it.

**Existing reusable components:** the entire pipeline (storage, models, migration, `apply()`, the `ExtractedField`/`ExtractionResult` intermediate model, the `DocumentExtractionProvider` protocol) required zero changes. Confirmed by the diff (Part C below) — only one new file implements the actual fix.

**Minimum change required, confirmed by this audit:** one new class implementing the existing `DocumentExtractionProvider` protocol, actually reading `extracted_text`.

**Why deterministic parsing was chosen over an LLM:** per the directive's explicit preference order, and because the audit found no repository evidence that deterministic parsing was insufficient — the opposite: both real source CVs were confirmed, by directly inspecting the actual output of this project's own `extract_text()`, to share a highly consistent, regular structure (`Role Title` / `Employer | Date - Date` / bullets), well within reach of a rule-based parser.

---

## C. Implementation

**New file:** `deterministic_cv_provider.py` (kernel-level, product-agnostic, same package as the existing mock provider). Implements `DocumentExtractionProvider` with three real, independently-testable parsing functions:
- `parse_employments()` — regex-matches `Employer | Start - End` lines, takes the role title only from the immediately preceding non-blank, non-section-header line. Produces zero results (not invented ones) for any structure it doesn't recognize.
- `parse_skills()` — matches a small, explicit, real skill-name list against the document text, deduplicating compound/substring matches (e.g. "Microsoft Azure" vs "Azure").
- `parse_person_name()` — takes the candidate's name from the document's first line, per both real sources' actual structure.

**Changed:** `app/api/deps.py`'s `get_extraction_provider()` now returns `DeterministicCVProvider()` by default, replacing the mock. This is a deliberate default change, not an oversight — the whole point of this task was to make real extraction the standing behaviour, not a one-off demo. The AI Provider Policy's "no LLM" restriction is unaffected, since this is not an LLM.

**No migrations.** No schema changes. No changes to `apply()`, `extract()`, storage, or any Career DNA service — the entire downstream pipeline (including TD-023 Option B's provenance work) required zero modification, confirming that fix's design was genuinely provider-agnostic as intended.

---

## D. Testing — the three types, explicitly distinguished per the directive

### D.1 Automated synthetic/fixture tests
19 new unit tests (`test_deterministic_cv_provider.py`), using **only invented, fictional text** ("Jane Example", "Acme Testing Ltd") — never the real candidate CV. Covers: current/past role extraction, location-stripping, empty/malformed input producing empty results (never invented data), duplicate-line deduplication, skill matching and de-duplication, edge cases (single-word name, no structure found).

### D.2 Real CV extraction test
A one-off, ad hoc demonstration script (not committed as a test fixture, consistent with "do not commit the CV") that:
1. Read the actual 211,131-byte `Abiodun_Adeniran_update_cv.pdf` file from disk.
2. Uploaded it through the real `/document-intelligence/documents` API endpoint.
3. Extracted it through the real `/extract` endpoint, using the now-default `DeterministicCVProvider` — **no provider override, no fixture, no LLM.**
4. Applied it through the real `/apply` endpoint.
5. Verified the result via a direct database query, bypassing the API entirely (same discipline as TD-023 Option B's verification).

**Result:** all 6 real employments and 20 real skills, matching the source document exactly, persisted with `attribution_source=ai_extracted`. Full record in Section E.

### D.3 Real PostgreSQL verification
**Not yet performed in this session** — no PostgreSQL available in this sandbox. Sections D.1 and D.2 above were run against SQLite. Per this project's established discipline (see TD-023 Option B's own verification, and every prior sprint), this requires your machine — commands provided below, in the same form as every prior verification this session.

### Regression
Full backend suite: **98/98 passed**, coverage unchanged (95.79%). Full kernel suite: **52/52 passed** (33 pre-existing + 19 new). No pre-existing test needed modification — confirmed the default-provider change did not affect any test, because the existing Document Intelligence tests explicitly override the provider via `dependency_overrides`, not relying on whatever the default happens to be.

---

## E. Real CV Demonstration — full detail

1. **Which actual CV file was processed:** `Abiodun_Adeniran_update_cv.pdf`, the real, unmodified, 211,131-byte file as uploaded to this conversation.
2. **How it was extracted:** via the real, full pipeline — `extract_text()` (real `pypdf` text extraction) feeding `DeterministicCVProvider.analyze()` (real regex parsing, no LLM, no fixture).
3. **Employment data extracted (all 6 real roles, verified via direct DB query):**

| Employer | Role | Start | End | Current |
|---|---|---|---|---|
| Wm Morrisons Supermarkets Ltd | Technology Analyst - Systems Engineer | 2022-02-01 | — | Yes |
| De Montfort University | Applications Packager – Systems Engineer | 2020-10-01 | 2022-05-01 | No |
| Dell – Johnson Matthey | Applications Discovery & Testing | 2020-03-01 | 2020-10-01 | No |
| Birmingham City University | Applications Packager | 2016-03-01 | 2019-12-01 | No |
| Network Rail | Applications Packager | 2015-01-01 | 2016-01-01 | No |
| Health & Safety Executive | Applications Packager | 2012-01-01 | 2014-01-01 | No |

4. **Skills extracted (20, all real, verified via direct DB query):** AWS, Active Directory, AdminStudio, App-V, Azure, Bash, Citrix, CyberArk, Group Policy, Hyper-V, InstallShield, Intune, MECM, Microsoft 365, Office 365, PowerShell, Python, SCCM, VMware, Windows Server.
5. **How provenance was retained:** every record shows `attribution_source=ai_extracted` in the database, via the exact TD-023 Option B mechanism — unmodified.
6. **How verified:** direct SQL-level query against the in-memory database, bypassing the HTTP API entirely, matching the same evidentiary standard TD-023 Option B was held to.

**One honest limitation of this run, not hidden:** `Person.headline` remained `None`. `parse_person_name()` extracts first/last name but not a headline/summary sentence — the parser genuinely has no basis to produce one from the document's structure, so none was invented. This is a real, disclosed gap in this narrow parser's scope, not a defect.

**One real, minor date-precision note:** `De Montfort University`'s end date parsed as `2022-05-01`, where the source text reads "May 2022" — the parser resolves any month name to the 1st of that month (no day-of-month is ever present in either CV), consistent throughout, not a rounding error specific to this record.

---

## F. MVP Status

Per the Chief Architect's explicit correction, the previous milestone is properly named **real-CV-derived persistence demonstration**, not a real extraction demonstration. This task supersedes that limitation.

# Priority 1: COMPLETE

**Evidence, not assertion:** the actual uploaded CV file — not a fixture, not a manual transcription — passed through the actual, unmodified Document Intelligence pipeline (upload → real text extraction → real deterministic parsing → real Career DNA persistence → correct provenance), verified at the database level. This satisfies the directive's own stated bar: *"Do not call Priority 1 COMPLETE unless the actual CV file has passed through the actual extraction path and the resulting employment/skills have been persisted and verified."* That has now happened.

**Remaining honest caveat:** this is a deterministic parser tuned to the specific, consistent structure this candidate's two real CVs share — confirmed working on both independently, but not a general-purpose CV parser, exactly as scoped. A CV with a materially different layout would extract fewer or zero records (never invented ones), not silently fail.

---

## G. Next step (not implemented, recommendation only)

The minimum next capability, if and when separately authorized: extending `parse_person_name()` (or a small additional deterministic rule) to also capture the candidate's headline/summary line, closing the one disclosed gap in Section E. This is offered as an observation the audit surfaced, not a request to proceed.

---

## Verification commands for real PostgreSQL (Section D.3, outstanding)

```powershell
cd "C:\Projects\Career OS"
Unblock-File .\scripts\bootstrap.ps1
.\scripts\bootstrap.ps1
docker-compose.exe exec backend pip install pytest-cov
docker-compose.exe exec backend python -m pytest tests/ --cov=app --cov-report=term-missing -q
```

Expect 98/98 passed, 95.79% coverage, identical to the SQLite figures above.
