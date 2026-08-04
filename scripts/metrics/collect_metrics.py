#!/usr/bin/env python3
"""
ORION Platform metrics collection.

Produces a machine-readable snapshot (metrics.json) of the engineering
metrics tracked in docs/METRICS.md: code coverage, cyclomatic complexity,
dependency counts, migration count, API endpoint count, technical debt
count, and a basic architecture-compliance check (the platform kernel
must never import product code).

Run from the repository root:
    python3 scripts/metrics/collect_metrics.py

Requires (dev-only, not part of the application's runtime dependencies):
    pip install radon pytest-cov pip-audit
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "products" / "careeros" / "backend"
KERNEL_DIR = REPO_ROOT / "platform" / "kernel" / "orion_kernel"
FRONTEND_DIR = REPO_ROOT / "products" / "careeros" / "frontend"


def run(cmd, cwd=None, timeout=120):
    return subprocess.run(cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True, timeout=timeout)


def count_python_loc(paths):
    total = 0
    for p in paths:
        for f in Path(p).rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            total += sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
    return total


def migration_count():
    versions_dir = BACKEND_DIR / "alembic" / "versions"
    return len(list(versions_dir.glob("*.py"))) if versions_dir.exists() else 0


def api_endpoint_count():
    pattern = re.compile(r'@router\.(get|post|put|patch|delete)\(')
    count = 0
    for f in (BACKEND_DIR / "app").rglob("*.py"):
        count += len(pattern.findall(f.read_text(encoding="utf-8", errors="ignore")))
    return count


def dependency_count():
    backend_reqs = (BACKEND_DIR / "requirements.txt").read_text().splitlines()
    backend_count = sum(1 for line in backend_reqs if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("-e"))
    frontend_pkg = json.loads((FRONTEND_DIR / "package.json").read_text())
    frontend_count = len(frontend_pkg.get("dependencies", {})) + len(frontend_pkg.get("devDependencies", {}))
    return {"backend_python": backend_count, "frontend_npm": frontend_count}


def technical_debt_count():
    td_path = REPO_ROOT / "docs" / "TechnicalDebt.md"
    if not td_path.exists():
        return {"open": None, "resolved": None}
    text = td_path.read_text()
    open_section = text.split("## Resolved")[0]
    resolved_section = text.split("## Resolved")[1] if "## Resolved" in text else ""
    open_count = len(re.findall(r"^\| TD-\d+ \|", open_section, re.MULTILINE))
    resolved_count = len(re.findall(r"^\| TD-R\d+ \|", resolved_section, re.MULTILINE))
    return {"open": open_count, "resolved": resolved_count}


def architecture_compliance():
    """Kernel must never import product (app.*) code. Cheap, real check."""
    violations = []
    for f in KERNEL_DIR.rglob("*.py"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'^\s*(from|import)\s+app\b', text, re.MULTILINE):
            violations.append(str(f.relative_to(REPO_ROOT)))
    return {"kernel_imports_product_code": violations, "compliant": len(violations) == 0}


def cyclomatic_complexity():
    r = run(["radon", "cc", "-a", "-j", str(BACKEND_DIR / "app"), str(KERNEL_DIR)])
    if r.returncode != 0:
        return {"error": r.stderr.strip()[:500]}
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "could not parse radon output"}
    all_complexities = []
    for file_results in data.values():
        for item in file_results:
            all_complexities.append(item.get("complexity", 0))
    if not all_complexities:
        return {"average": 0, "max": 0, "count": 0}
    return {
        "average": round(sum(all_complexities) / len(all_complexities), 2),
        "max": max(all_complexities),
        "count": len(all_complexities),
    }


def code_coverage():
    r = run(
        ["python3", "-m", "pytest", "--cov=app", "--cov-report=json:/tmp/coverage.json", "-q"],
        cwd=BACKEND_DIR,
        timeout=120,
    )
    cov_path = Path("/tmp/coverage.json")
    if not cov_path.exists():
        return {"error": (r.stdout + r.stderr)[-800:]}
    data = json.loads(cov_path.read_text())
    return {"percent_covered": round(data["totals"]["percent_covered"], 2)}


def security_findings():
    """
    Runs pip-audit against a pinned snapshot of CareerOS's actual pinned
    dependencies (products/careeros/backend/requirements.txt, minus the
    local editable orion-kernel line, which isn't a published package and
    would confuse pip-audit's resolver). --no-deps keeps this fast and
    avoids resolving unrelated transitive versions; it will under-count
    vulnerabilities in transitive dependencies not pinned explicitly --
    see docs/TechnicalDebt.md for that caveat.
    """
    pinned = []
    for line in (BACKEND_DIR / "requirements.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-e"):
            continue
        pinned.append(line.replace("[cryptography]", "").replace("[bcrypt]", "").replace("[standard]", ""))
    tmp_req = Path("/tmp/_careeros_metrics_frozen_reqs.txt")
    tmp_req.write_text("\n".join(pinned))

    r = run(["pip-audit", "-r", str(tmp_req), "--format", "json", "--no-deps"], timeout=60)
    try:
        data = json.loads(r.stdout)
        deps = data.get("dependencies", data if isinstance(data, list) else [])
        vulnerable_packages = [
            {"name": d["name"], "version": d["version"], "vuln_ids": [v["id"] for v in d.get("vulns", [])]}
            for d in deps if d.get("vulns")
        ]
        finding_count = sum(len(d["vuln_ids"]) for d in vulnerable_packages)
        return {"vulnerabilities_found": finding_count, "vulnerable_packages": vulnerable_packages}
    except Exception as e:
        return {"error": str(e), "stderr_tail": r.stderr[-500:]}


def main():
    metrics = {
        "code_coverage": code_coverage(),
        "cyclomatic_complexity": cyclomatic_complexity(),
        "dependencies": dependency_count(),
        "migration_count": migration_count(),
        "api_endpoint_count": api_endpoint_count(),
        "docker_image_size_mb": None,  # requires Docker daemon; not available in this environment
        "security_findings": security_findings(),
        "technical_debt": technical_debt_count(),
        "architecture_compliance": architecture_compliance(),
        "lines_of_code": {
            "backend_app": count_python_loc([BACKEND_DIR / "app"]),
            "kernel": count_python_loc([KERNEL_DIR]),
            "tests": count_python_loc([BACKEND_DIR / "tests"]),
        },
    }
    out_path = REPO_ROOT / "docs" / "metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
