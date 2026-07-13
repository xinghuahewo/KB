import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
PIPELINE_DIR = PACKAGE_DIR / "pipeline"
API_DIR = PACKAGE_DIR / "api"
SERVICE_DIR = API_DIR  # 兼容旧调用方；新代码使用 API_DIR。

_CONFIGURED_DATA_DIR = os.environ.get("BGPKB_DATA_DIR")
DATA_DIR = (
    Path(_CONFIGURED_DATA_DIR).expanduser().resolve()
    if _CONFIGURED_DATA_DIR
    else PROJECT_ROOT / "data"
)
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

DOCS_DIR = REPOSITORY_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"

_REPORT_POLICY_CACHE = None


class RuntimeDataUnavailable(RuntimeError):
    """Raised when an operation requiring a published artifact has no data root."""


def runtime_data_dir() -> Path | None:
    """Return the explicitly configured published-artifact data directory, if any."""
    configured = os.environ.get("BGPKB_DATA_DIR")
    if not configured:
        return None
    return Path(configured).expanduser().resolve()


def require_runtime_data_dir() -> Path:
    """Return the runtime data directory or explain how to provide a release artifact."""
    data_dir = runtime_data_dir()
    if data_dir is None:
        raise RuntimeDataUnavailable(
            "未配置 BGPKB_DATA_DIR；需要发布制品的操作请设置为 "
            "/srv/bgpkb/artifacts/releases/<release-id>/data。"
        )
    if not data_dir.is_dir():
        raise RuntimeDataUnavailable(f"BGPKB_DATA_DIR 不是可用目录：{data_dir}")
    return data_dir


def rel(path: Path) -> str:
    path = Path(path)
    if path.is_relative_to(DATA_DIR):
        return (Path("data") / path.relative_to(DATA_DIR)).as_posix()
    if path.is_relative_to(DOCS_DIR):
        return (Path("docs") / path.relative_to(DOCS_DIR)).as_posix()
    return path.relative_to(PROJECT_ROOT).as_posix()


def resolve_logical_path(path: str | Path) -> Path:
    """Resolve a repository-logical path, routing ``data/`` through DATA_DIR."""
    logical = Path(path)
    if logical.is_absolute() or ".." in logical.parts:
        raise ValueError(f"逻辑路径必须是仓库内相对路径：{path}")
    if logical.parts and logical.parts[0] == "data":
        resolved = (DATA_DIR / Path(*logical.parts[1:])).resolve()
        resolved.relative_to(DATA_DIR.resolve())
        return resolved
    if logical.parts and logical.parts[0] == "docs":
        resolved = (REPOSITORY_ROOT / logical).resolve()
        resolved.relative_to(REPOSITORY_ROOT.resolve())
        return resolved
    resolved = (PROJECT_ROOT / logical).resolve()
    resolved.relative_to(PROJECT_ROOT.resolve())
    return resolved


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
    return resolve_logical_path(path)


def generated_report_dir(category: str) -> Path:
    return GENERATED_REPORTS_DIR / category


def pipeline_module(script_name: str) -> str:
    return f"bgpkb.pipeline.{Path(script_name).stem}"


def pipeline_command(script_name: str, *args: str) -> str:
    return " ".join(["python3", "-m", pipeline_module(script_name), *args])
