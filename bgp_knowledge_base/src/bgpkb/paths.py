from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]
PIPELINE_DIR = PACKAGE_DIR / "pipeline"
SERVICE_DIR = PACKAGE_DIR / "service"

DATA_DIR = PROJECT_ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
RAW_DIR = SOURCES_DIR / "raw"
INVENTORY_DIR = SOURCES_DIR / "inventory"

CORPUS_DIR = DATA_DIR / "corpus"
PARSED_DIR = CORPUS_DIR / "parsed"
CLEANED_DIR = CORPUS_DIR / "cleaned"
CHUNKS_DIR = CORPUS_DIR / "chunks"

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
ENTITIES_DIR = KNOWLEDGE_DIR / "entities"
RELATIONSHIPS_DIR = KNOWLEDGE_DIR / "relationships"

REVIEW_INPUTS_DIR = DATA_DIR / "review_inputs"
DERIVED_DIR = DATA_DIR / "derived"
DATASETS_DIR = DERIVED_DIR / "datasets"
PUBLISHED_DIR = DATA_DIR / "published"
REPORTS_DIR = DATA_DIR / "reports"
GENERATED_DIR = DATA_DIR / "generated"
GENERATED_REPORTS_DIR = GENERATED_DIR / "reports"

METADATA_DIR = PROJECT_ROOT / "metadata"
CONFIG_DIR = METADATA_DIR / "config"
SCHEMAS_DIR = METADATA_DIR / "schemas"
REPORT_POLICY_PATH = CONFIG_DIR / "report_policy.yaml"

DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"

_REPORT_POLICY_CACHE = None


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def report_policy() -> dict:
    global _REPORT_POLICY_CACHE
    if _REPORT_POLICY_CACHE is None:
        import yaml

        data = yaml.safe_load(REPORT_POLICY_PATH.read_text(encoding="utf-8"))
        _REPORT_POLICY_CACHE = data.get("reports", {})
    return _REPORT_POLICY_CACHE


def report_path(report_id: str) -> Path:
    try:
        path = report_policy()[report_id]["path"]
    except KeyError as exc:
        raise KeyError(f"Unknown report_id in {REPORT_POLICY_PATH}: {report_id}") from exc
    return PROJECT_ROOT / path


def generated_report_dir(category: str) -> Path:
    return GENERATED_REPORTS_DIR / category


def pipeline_module(script_name: str) -> str:
    return f"bgpkb.pipeline.{Path(script_name).stem}"


def pipeline_command(script_name: str, *args: str) -> str:
    return " ".join(["python3", "-m", pipeline_module(script_name), *args])
