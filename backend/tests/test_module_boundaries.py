import ast
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "bgpkb"
CANONICAL_PACKAGES = {
    "domain",
    "infrastructure",
    "ingestion",
    "indexing",
    "publishing",
    "retrieval",
    "api",
    "workflows",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_modular_monolith_exposes_all_canonical_packages():
    for package in CANONICAL_PACKAGES:
        assert (PACKAGE_ROOT / package / "__init__.py").is_file(), package


def test_canonical_modules_never_depend_on_legacy_service_package():
    offenders = []
    for package in CANONICAL_PACKAGES:
        for path in (PACKAGE_ROOT / package).glob("*.py"):
            if any(name == "bgpkb.service" or name.startswith("bgpkb.service.") for name in _imports(path)):
                offenders.append(path.relative_to(PACKAGE_ROOT).as_posix())
    assert offenders == []


def test_ingestion_owns_docling_cleaning_implementation():
    cleaning = PACKAGE_ROOT / "ingestion" / "cleaning_v2"

    assert (cleaning / "runtime_pipeline.py").is_file()
    assert (cleaning / "transformations.py").is_file()


def test_offline_implementations_live_in_responsibility_packages():
    expected = {
        "ingestion": "parse_documents.py",
        "indexing": "build_chunks.py",
        "publishing": "build_standard_exports.py",
        "retrieval": "query_hybrid_rag.py",
        "workflows": "run_pipeline.py",
    }
    for package, module in expected.items():
        assert (PACKAGE_ROOT / package / module).is_file(), f"{package}/{module}"


def test_canonical_packages_do_not_import_legacy_pipeline_package():
    offenders = []
    for package in CANONICAL_PACKAGES:
        for path in (PACKAGE_ROOT / package).glob("*.py"):
            if any(name == "bgpkb.pipeline" or name.startswith("bgpkb.pipeline.") for name in _imports(path)):
                offenders.append(path.relative_to(PACKAGE_ROOT).as_posix())
    assert offenders == []


def test_domain_has_no_io_web_or_application_dependencies():
    forbidden = ("fastapi", "sqlite3", "urllib", "bgpkb.api", "bgpkb.infrastructure", "bgpkb.retrieval")
    offenders = []
    for path in (PACKAGE_ROOT / "domain").glob("*.py"):
        for imported in _imports(path):
            if imported == forbidden or any(imported == item or imported.startswith(f"{item}.") for item in forbidden):
                offenders.append(f"{path.name}: {imported}")
    assert offenders == []


def test_api_does_not_read_runtime_artifact_paths_directly():
    offenders = []
    forbidden_names = {"DATA_DIR", "PUBLISHED_DIR", "CORPUS_DIR", "CHUNKS_DIR"}
    for path in (PACKAGE_ROOT / "api").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        used_names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        if used_names & forbidden_names:
            offenders.append(path.name)
    assert offenders == []
