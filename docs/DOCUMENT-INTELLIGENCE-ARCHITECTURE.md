# Document Intelligence Engine -- Architecture (Design Only)

**Status: DESIGN ONLY. Supersedes the "CV Intelligence" section of
`docs/SPRINT-3-ARCHITECTURE.md` Section 2 and Section 9's related
items, per Chief Architect Decision (Sprint 3 Stage 1, Document
Intelligence Engine directive). No implementation authorized by this
document.**

This is a reusable ORION Platform-level capability, not a CareerOS
feature that happens to read CVs. CareerOS is its first consumer.
Future ORION products ingesting any professional document (not just
CVs) reuse this engine without modification.

## 1. System Architecture

```
Upload Document
      |
      v
Secure Storage (StorageAdapter, per ADR 0005 Decision 1 -- unchanged)
      |
      v
Document Intelligence Engine
      |
      +--> Extract Text (format-specific: PDF, DOCX, ...)
      |
      +--> DocumentExtractionProvider.analyze() --> Structured
      |    Extraction Model (provider-agnostic)
      |
      v
Validation
      |
      v
Career DNA Services (person_service, employment_service,
skill_service, evidence_service -- Sprint 2, unchanged, sole write path)
      |
      v
Career Profile
```

**Placement:** the engine itself (`DocumentExtractionProvider`
interface, provider implementations, the intermediate extraction
model, text-extraction utilities) lives under `platform/kernel/
orion_kernel/document_intelligence/` -- a genuine Platform Kernel
capability, not a CareerOS-local one, matching the "future ORION
products reuse it without modification" requirement. The **decision of
what to do with extracted data** (map it onto Career DNA, via which
services, with which validation) remains CareerOS-specific and lives in
`products/careeros/backend/app/services/document_intelligence_service.py`
-- the engine extracts and structures; CareerOS decides what that means
for a career profile. This mirrors the existing kernel/product split
(`orion_kernel` provides primitives, `app/services` provides domain
behavior) rather than inventing a new boundary shape.

**Architecture Review note (per this project's checklist):** placing a
brand-new capability directly in the kernel is exactly what
`ArchitecturePrinciples.md`'s "don't over-generalize speculatively"
principle warns against (see ADR 0005 Decision 1's reasoning for File
Storage, which reached the opposite conclusion). The difference here:
unlike File Storage, this capability's entire purpose per the
directive is explicit cross-product reuse ("Document Intelligence
Engine... designed so future ORION products can reuse it without
modification"), stated as the reason for the rename itself -- so the
speculative-generalization concern doesn't apply the same way. This
distinction is significant enough that it should be written into ADR
0006 explicitly, not left implicit -- see Section 7.

## 2. Document Types

**Stage 1 supports exactly two:** `pdf`, `docx`. Represented as a
`DocumentType` enum on `Document`, not inferred solely from file
extension (a `.pdf` with corrupt content should fail validation, not
silently misroute).

**Extensibility, without redesign:** adding cover letters,
certificates, degrees, licences, LinkedIn exports, job descriptions,
references, performance reviews, or skills assessments later means:
(a) a new `DocumentType` enum value, (b) a new (or reused) text
extractor for that format if not already covered, and (c) a new
CareerOS-side mapping in `document_intelligence_service.py` for what
that document type's extracted fields mean for a career profile. No
change to the engine's core pipeline, provider interface, or storage
model is required -- this is the actual test of whether the
"without redesign" requirement is met, not just an aspiration.

## 3. Provider Interface Specification

```python
class DocumentExtractionProvider(Protocol):
    provider_name: str

    async def analyze(
        self, document_type: DocumentType, extracted_text: str
    ) -> ExtractionResult:
        """Takes already-extracted plain text (text extraction from the
        PDF/DOCX binary is the engine's own responsibility, upstream of
        any provider -- providers never see raw file bytes) and returns
        a structured ExtractionResult. This keeps every provider
        implementation format-agnostic; only the engine's text-
        extraction layer needs to know about PDF/DOCX internals."""

    async def health_check(self) -> bool: ...
```

**Initial implementation:** `LLMDocumentExtractionProvider`, calling
Claude's API (matching this project's own AI provider, and avoiding a
second AI vendor relationship for a Sprint 3 first pass) with a
structured-output prompt. `provider_name = "anthropic-claude"`.

**Future providers**, requiring zero changes to callers: OpenAI,
local OCR (for scanned/image-based documents this project doesn't yet
support), Azure AI Document Intelligence, Google Document AI, Amazon
Textract, Affinda, Sovren -- each a new class implementing the same
Protocol, selected via configuration (`config/config.example.yaml`'s
existing pattern for pluggable provider selection, the same mechanism
Job Intelligence's `JobProviderClient` uses).

**Multiple extraction runs on the same document, multiple providers:**
`DocumentExtractionRun` (Section 5) is keyed by `(document_id,
provider_name, run_number)`, not assumed to be one-run-per-document --
this is what makes "compare providers" and "re-run when the model
improves" possible without any schema change later.

## 4. Structured Extraction Model (the extraction/Career-DNA contract)

The engine **never** writes to Career DNA. It produces this
intermediate model; CareerOS's `document_intelligence_service.py`
consumes it and calls existing Sprint 2 services. This is the load-
bearing boundary TD-019 exists to enforce.

```python
@dataclass
class ExtractionResult:
    persons: list[ExtractedPerson]
    employments: list[ExtractedEmployment]
    educations: list[ExtractedEducation]
    skills: list[ExtractedSkill]
    technologies: list[ExtractedTechnology]
    certifications: list[ExtractedCertification]
    projects: list[ExtractedProject]
    achievements: list[ExtractedAchievement]
    overall_confidence: float  # 0-1

@dataclass
class ExtractedField(Generic[T]):
    """Every extracted value is wrapped, not returned bare -- so
    confidence and provenance travel WITH the data from the moment it's
    extracted, not bolted on afterward."""
    value: T
    confidence: float  # 0-1, per-field, per Future Expansion requirement

@dataclass
class ExtractedPerson:
    first_name: ExtractedField[str]
    last_name: ExtractedField[str]
    headline: ExtractedField[str] | None

@dataclass
class ExtractedEmployment:
    employer_name: ExtractedField[str]
    role_title: ExtractedField[str]
    start_date: ExtractedField[date] | None
    end_date: ExtractedField[date] | None
    is_current: ExtractedField[bool]
    description: ExtractedField[str] | None

@dataclass
class ExtractedSkill:
    skill_name: ExtractedField[str]
    skill_type: ExtractedField[SkillType] | None  # provider may not always classify confidently

# ExtractedEducation, ExtractedTechnology, ExtractedCertification,
# ExtractedProject, ExtractedAchievement follow the same shape:
# every field is an ExtractedField[T], mirroring the corresponding
# Career DNA entity's Create schema shape (see app/schemas/career_dna.py)
# field-for-field, so the mapping in document_intelligence_service.py
# is a mechanical wrap/unwrap, not a redesign of Career DNA's own shape.
```

## 5. Database changes

Two tables (generalizing `CVDocument`/`CVExtractionRun` from the prior
design, per the rename):

- **Document**: `id`, `person_id`, `document_type` (`pdf`/`docx`),
  `original_filename`, `storage_ref` (via `StorageAdapter`, ADR 0005
  Decision 1, unchanged), `mime_type`, `uploaded_at`, `status`
  (`pending`/`processed`/`failed`), `error_detail`. Both the original
  document AND every extraction run's structured output are retained
  (per the directive's explicit "do not discard either") -- the
  original via `storage_ref`, extractions via the table below.
- **DocumentExtractionRun**: `id`, `document_id`, `provider_name`,
  `run_number` (per Section 3, supports multiple runs/providers per
  document), `started_at`, `completed_at`, `status`
  (`pending`/`completed`/`failed`), `overall_confidence`,
  `raw_extraction_json` (the full `ExtractionResult`, serialized --
  audit trail, never itself read as source of truth once Career DNA
  has been written to), `reviewed_at` (nullable -- see Section 6, human
  review workflow), `reviewed_by_person_id` (nullable), `applied_at`
  (nullable -- when this run's data was actually written to Career DNA,
  distinct from when it was reviewed, since a review could reject it).

**`AttributionSource` values, per ADR 0005 Decision 3 -- standardized
naming for implementation:** `USER_ENTERED`, `AI_EXTRACTED`,
`IMPORTED`, `VERIFIED`. Every Career DNA write originating from this
engine sets `AI_EXTRACTED`, never `USER_ENTERED` -- this is the actual
enforcement point for ADR 0005 Decision 3 and RB-03's mitigation, not
just a database column that could theoretically be misused.

## 6. API specification

| Method | Path | Purpose |
|---|---|---|
| POST | `/document-intelligence/documents` | Upload a document (multipart), returns `Document` with `status=pending` |
| GET | `/document-intelligence/documents` | List the caller's documents |
| GET | `/document-intelligence/documents/{id}` | Get one, including its extraction runs |
| POST | `/document-intelligence/documents/{id}/extract` | Trigger a new `DocumentExtractionRun` (which provider defaults to config; explicit `provider_name` optional for the multi-provider-comparison case) |
| GET | `/document-intelligence/documents/{id}/runs/{run_id}` | Get one extraction run's full structured result, for the human review workflow (Section 8) |
| POST | `/document-intelligence/documents/{id}/runs/{run_id}/apply` | **Human review gate:** applies this run's `ExtractionResult` to Career DNA via existing services, setting `applied_at`. Nothing is written to Career DNA before this call -- extraction and application are explicitly separate steps. |
| DELETE | `/document-intelligence/documents/{id}` | Delete (cascades extraction runs; does NOT retroactively remove already-applied Career DNA data -- that's a normal Career DNA delete, a separate concern) |

**Why "extract" and "apply" are separate endpoints, not one:** per the
Future Expansion requirement for a human review workflow and confidence
thresholds. A low-confidence extraction should be reviewable (and
editable, in a future iteration) before it touches Career DNA at all --
collapsing extraction and application into one call would make
"AI read this, but the user should confirm it before it becomes their
career profile" impossible to build later without an API break.

## 7. Sequence diagram

See `docs/diagrams/document-intelligence-sequence.mmd`.

## 8. Human review workflow (Stage 1 minimum viable version)

Full "review UI with inline editing" is future work, but Stage 1 must
support the minimum viable version of the workflow this architecture
requires: a caller can `GET` a run's structured `ExtractionResult`
(with per-field confidence) before deciding whether to `POST .../apply`.
Nothing enforces a UI review actually happens in Stage 1 -- that's a
product/UX decision, out of this architecture's scope -- but the API
must not make review impossible by auto-applying on extraction.

## 9. What is explicitly NOT in Stage 1 scope

- OCR for scanned/image-based PDFs (Stage 1 assumes machine-readable
  text layers).
- Any provider other than `LLMDocumentExtractionProvider`.
- Document types other than `pdf`/`docx`.
- An actual review UI (only the API surface enabling one later).
- Confidence-threshold-based auto-apply (every application is an
  explicit `apply` call in Stage 1; automatic application above a
  confidence threshold is named in Future Expansion but not built now).
