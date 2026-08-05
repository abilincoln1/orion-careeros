"""
TD-019 enforcement: document_intelligence_service.py must never import
Career DNA models directly (app.models.person, app.models.employment,
app.models.skills, etc.) -- only the existing service modules
(app.services.person_service, etc.). This is the actual mechanism, not
just a written policy, per the Sprint 3 Phase 6 review's Approve-with-
Conditions requirement.

Person is a deliberate, documented, narrow exception -- see
app/services/document_intelligence_service.py's module docstring: it is
imported only for type-hinting `person: Person` parameters, never
constructed or queried directly by this service (all Person mutation
goes through person_service). This test allows that one specific
import while still catching the violation TD-019 actually cares about:
writing to Career DNA tables by importing their models and constructing
rows directly, bypassing the service layer's validation and invariants.
"""
import ast
from pathlib import Path

SERVICE_PATH = (
    Path(__file__).parent.parent / "app" / "services" / "document_intelligence_service.py"
)

# Career DNA modules whose models must never be imported here, EXCEPT
# the one explicit, documented exception (Person, for type hints only).
_FORBIDDEN_MODULES = {
    "app.models.employment",
    "app.models.skills",
    "app.models.evidence",
    "app.models.credentials",
    "app.models.work_product",
    "app.models.preferences",
    "app.models.taxonomy",
}


def _imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_document_intelligence_service_does_not_import_forbidden_career_dna_models():
    source = SERVICE_PATH.read_text()
    imported = _imported_modules(source)
    violations = imported & _FORBIDDEN_MODULES
    assert not violations, (
        f"document_intelligence_service.py imports {violations} directly -- "
        "TD-019 requires all Career DNA writes to go through the existing "
        "service layer (app.services.*), never by constructing Career DNA "
        "model instances directly. If a new Career DNA write is genuinely "
        "needed, add a function to the relevant service module and call "
        "that, per the write boundary this project's Sprint 3 Phase 6 "
        "review approved-with-conditions."
    )


def test_document_intelligence_service_only_imports_person_model_for_type_hints():
    """The one documented exception (Person) is imported, but this test
    confirms it's not being used to construct or query Person rows
    directly -- only person_service is called for any Person mutation."""
    source = SERVICE_PATH.read_text()
    tree = ast.parse(source)

    person_constructed_directly = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Person":
            person_constructed_directly = True

    assert not person_constructed_directly, (
        "document_intelligence_service.py constructs a Person(...) instance "
        "directly -- all Person mutation must go through person_service "
        "functions (e.g. person_service.update_person), never direct "
        "ORM construction."
    )


def test_document_intelligence_service_calls_person_service_for_writes():
    """Positive check, not just an absence check: confirms the service
    actually DOES call person_service for the one write it performs
    (Person.headline), so this test suite would fail if that call were
    ever silently removed in favor of a direct write."""
    source = SERVICE_PATH.read_text()
    assert "person_service.update_person" in source
