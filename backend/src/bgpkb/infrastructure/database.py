from pathlib import Path

from bgpkb import paths
from bgpkb.infrastructure import serving_bundle
import sqlite3


ROOT = paths.PROJECT_ROOT
DB_PATH = paths.PUBLISHED_DIR / serving_bundle.SERVING_DB_FILENAME
DB_FILENAME = serving_bundle.SERVING_DB_FILENAME
SERVICE_NAME = "bgp-knowledge-base-service"
SERVICE_VERSION = "0.1.0"


def runtime_database_path() -> Path:
    """Return the SQLite file from the explicitly configured release artifact."""
    return serving_bundle.resolve_serving_database_path(paths.require_runtime_data_dir())


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or runtime_database_path()
    return serving_bundle.connect_serving_database(
        db_path,
        allow_legacy=serving_bundle.legacy_reader_enabled(),
    )


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
        reader = serving_bundle.inspect_serving_database(
            db_path,
            allow_legacy=serving_bundle.legacy_reader_enabled(),
        )
        with connect(db_path) as conn:
            status["integrity_check"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
        status.update(
            {
                "reader_mode": reader["mode"],
                "degraded": reader["degraded"],
                "schema_version": reader["schema_version"],
                "minimum_reader_version": reader["minimum_reader_version"],
                "release_id": reader["release_id"],
            }
        )
    except (sqlite3.Error, serving_bundle.ServingBundleError) as exc:
        status["error"] = str(exc)
    return status
