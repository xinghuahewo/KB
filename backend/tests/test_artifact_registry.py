from pathlib import Path

import pytest

from bgpkb.artifact_registry import ArtifactRegistryError, load_release_registry, validate_release_registry


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_repository_registry_records_current_external_release():
    registry = load_release_registry(REPOSITORY_ROOT / "artifacts" / "releases.yaml")

    assert registry["schema_version"] == 1
    assert registry["current_release_id"] == "2026-07-10-93a4c97"
    assert registry["releases"][0] == {
        "release_id": "2026-07-10-93a4c97",
        "source_commit": "93a4c97",
        "file_count": 1293,
        "sha256sums_sha256": "97400ef06e8ef20c3d363918b79d2540d4e513e6fe5be4ea9e84e9c870f9a04b",
        "data_path": "/srv/bgpkb/artifacts/releases/2026-07-10-93a4c97/data",
        "status": "current",
    }


def test_registry_rejects_duplicate_release_ids():
    release = {
        "release_id": "2026-07-10-93a4c97",
        "source_commit": "93a4c97",
        "file_count": 1293,
        "sha256sums_sha256": "9" * 64,
        "data_path": "/srv/bgpkb/artifacts/releases/2026-07-10-93a4c97/data",
        "status": "current",
    }

    with pytest.raises(ArtifactRegistryError, match="重复"):
        validate_release_registry({
            "schema_version": 1,
            "current_release_id": release["release_id"],
            "releases": [release, dict(release)],
        })
