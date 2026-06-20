from pathlib import Path
import sqlite3
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "published" / "bgp_knowledge_base.sqlite"
SERVICE_NAME = "bgp-knowledge-base-service"
SERVICE_VERSION = "0.1.0"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    uri = f"file:{quote(str(db_path), safe='/')}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def health_status(db_path: Path = DB_PATH) -> dict:
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
