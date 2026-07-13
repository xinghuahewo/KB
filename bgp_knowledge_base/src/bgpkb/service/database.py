from pathlib import Path

from bgpkb import paths
import sqlite3
from urllib.parse import quote


ROOT = paths.PROJECT_ROOT
DB_PATH = paths.PUBLISHED_DIR / "bgp_knowledge_base.sqlite"
DB_FILENAME = "bgp_knowledge_base.sqlite"
SERVICE_NAME = "bgp-knowledge-base-service"
SERVICE_VERSION = "0.1.0"


def runtime_database_path() -> Path:
    """Return the SQLite file from the explicitly configured release artifact."""
    return paths.require_runtime_data_dir() / "published" / DB_FILENAME


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or runtime_database_path()
    uri = f"file:{quote(str(db_path), safe='/')}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def health_status(db_path: Path | None = None) -> dict:
    try:
        db_path = db_path or runtime_database_path()
    except paths.RuntimeDataUnavailable as exc:
        return {
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "database_path": None,
            "database_exists": False,
            "integrity_check": None,
            "error": str(exc),
        }
    status = {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "database_path": str(db_path),
        "database_exists": db_path.exists(),
        "integrity_check": None,
    }
    if not db_path.exists():
        status["error"] = "database file not found"
        return status

    try:
        with connect(db_path) as conn:
            status["integrity_check"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.Error as exc:
        status["error"] = str(exc)
    return status
