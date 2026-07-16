from pathlib import Path

import pytest

from bgpkb.artifact_registry import ArtifactRegistryError, load_release_registry, validate_release_registry


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_repository_registry_records_current_external_release():
    registry = load_release_registry(REPOSITORY_ROOT / "artifacts" / "releases.yaml")

    assert registry["schema_version"] == 1
    assert registry["current_release_id"] == "rag-evidence-pipeline-v2-11.1-20260715T073006Z"
    assert registry["releases"][-1] == {
        "release_id": "rag-evidence-pipeline-v2-11.1-20260715T073006Z",
        "source_commit": "2f1957839673f7ef65e1f6dfec332abfcef69972",
        "file_count": 209,
        "sha256sums_sha256": "f78d26fd9347617783cebefeec9e17b89e7196b42aadc0d990654dbf581cbfb7",
        "data_path": "/srv/bgpkb/artifacts/releases/rag-evidence-pipeline-v2-11.1-20260715T073006Z/data",
        "status": "current",
    }


def test_registry_accepts_versioned_pipeline_release_id():
    release_id = "rag-evidence-pipeline-v2-11.1-20260715T073006Z"

    payload = validate_release_registry({
        "schema_version": 1,
        "current_release_id": release_id,
        "releases": [{
            "release_id": release_id,
            "source_commit": "2f1957839673f7ef65e1f6dfec332abfcef69972",
            "file_count": 209,
            "sha256sums_sha256": "f" * 64,
            "data_path": f"/srv/bgpkb/artifacts/releases/{release_id}/data",
            "status": "current",
        }],
    })

    assert payload["current_release_id"] == release_id


@pytest.mark.parametrize("release_id", ["../escape", "nested/release", "release id", "-release"])
def test_registry_rejects_unsafe_release_id(release_id):
    with pytest.raises(ArtifactRegistryError, match="release_id 非法"):
        validate_release_registry({
            "schema_version": 1,
            "current_release_id": release_id,
            "releases": [{
                "release_id": release_id,
                "source_commit": "2f19578",
                "file_count": 1,
                "sha256sums_sha256": "f" * 64,
                "data_path": f"/srv/bgpkb/artifacts/releases/{release_id}/data",
                "status": "current",
            }],
        })


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
