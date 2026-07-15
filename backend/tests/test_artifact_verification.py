import hashlib
import json
from pathlib import Path
import sqlite3
import shutil
import yaml

import pytest

from bgpkb import artifact_verification
from bgpkb.artifact_verification import ArtifactVerificationError, verify_artifact_release
from bgpkb.infrastructure.fast_vector_index import build_fast_vector_index


def _write_release(tmp_path: Path) -> Path:
    release_root = tmp_path / "2026-07-10-93a4c97"
    data_dir = release_root / "data"
    published_dir = data_dir / "published"
    datasets_dir = data_dir / "derived" / "datasets"
    published_dir.mkdir(parents=True)
    datasets_dir.mkdir(parents=True)

    with sqlite3.connect(published_dir / "bgp_knowledge_base.sqlite") as conn:
        conn.execute("CREATE TABLE chunks (chunk_id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO chunks VALUES ('chunk-1')")
    (published_dir / "chunk_catalog.jsonl").write_text('{"chunk_id":"chunk-1"}\n', encoding="utf-8")
    (published_dir / "source_catalog.jsonl").write_text('{"source_id":"rfc4271"}\n', encoding="utf-8")
    (published_dir / "entity_catalog.jsonl").write_text('{"entity_id":"route-leak"}\n', encoding="utf-8")
    (published_dir / "bge_m3_vector_index.jsonl").write_text(
        '{"kind":"chunk","metadata":{"chunk_id":"chunk-1"},"vector":[0.1,0.2]}\n',
        encoding="utf-8",
    )
    (published_dir / "bge_m3_embedding_manifest.json").write_text(
        json.dumps({"status": "complete", "record_count": 1, "dimensions": 2}) + "\n",
        encoding="utf-8",
    )
    (datasets_dir / "entity_source_evidence.jsonl").write_text("", encoding="utf-8")
    (datasets_dir / "section_catalog.jsonl").write_text("", encoding="utf-8")
    build_fast_vector_index(published_dir / "bge_m3_vector_index.jsonl")

    checksum_lines = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            checksum_lines.append(f"{digest}  {path.relative_to(release_root).as_posix()}")
    (release_root / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return data_dir


def _rewrite_checksums(data_dir: Path) -> None:
    release_root = data_dir.parent
    checksum_lines = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            checksum_lines.append(f"{digest}  {path.relative_to(release_root).as_posix()}")
    (release_root / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def test_verify_artifact_release_checks_hashes_sqlite_and_index_metadata(tmp_path):
    data_dir = _write_release(tmp_path)

    result = verify_artifact_release(data_dir)

    assert result["release_id"] == "2026-07-10-93a4c97"
    assert result["file_count"] == 11
    assert result["sqlite_integrity"] == "ok"
    assert result["vector_index_status"] == "complete"
    assert result["vector_index_mode"] == "fast_numpy"


def test_verify_artifact_release_requires_fast_vector_artifacts(tmp_path):
    data_dir = _write_release(tmp_path)
    artifacts = build_fast_vector_index(data_dir / "published" / "bge_m3_vector_index.jsonl")
    artifacts.matrix_path.unlink()
    artifacts.metadata_path.unlink()
    artifacts.manifest_path.unlink()
    _rewrite_checksums(data_dir)

    with pytest.raises(ArtifactVerificationError, match="bge_m3_vector_matrix"):
        verify_artifact_release(data_dir)


def test_verify_artifact_release_rejects_stale_fast_vector_manifest(tmp_path):
    data_dir = _write_release(tmp_path)
    vector_path = data_dir / "published" / "bge_m3_vector_index.jsonl"
    artifacts = build_fast_vector_index(vector_path)
    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    manifest["source_index_sha256"] = "sha256:" + "0" * 64
    artifacts.manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    _rewrite_checksums(data_dir)

    with pytest.raises(ArtifactVerificationError, match="过期"):
        verify_artifact_release(data_dir)


def test_verify_artifact_release_compares_fast_index_with_chunk_records_only(tmp_path):
    data_dir = _write_release(tmp_path)
    published_dir = data_dir / "published"
    vector_path = published_dir / "bge_m3_vector_index.jsonl"
    vector_path.write_text(
        '{"kind":"chunk","metadata":{"chunk_id":"chunk-1"},"vector":[0.1,0.2]}\n'
        '{"kind":"entity","doc_id":"entity-1","vector":[0.2,0.1]}\n',
        encoding="utf-8",
    )
    (published_dir / "bge_m3_embedding_manifest.json").write_text(
        json.dumps({"status": "complete", "record_count": 2, "dimensions": 2}) + "\n",
        encoding="utf-8",
    )
    build_fast_vector_index(vector_path)
    _rewrite_checksums(data_dir)

    result = verify_artifact_release(data_dir)

    assert result["vector_record_count"] == 2
    assert result["fast_vector_record_count"] == 1


def test_verify_artifact_release_fails_closed_on_checksum_mismatch(tmp_path):
    data_dir = _write_release(tmp_path)
    (data_dir / "published" / "chunk_catalog.jsonl").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ArtifactVerificationError, match="SHA-256"):
        verify_artifact_release(data_dir)


def test_verify_artifact_release_rejects_incomplete_or_extra_file_sets(tmp_path):
    data_dir = _write_release(tmp_path / "missing")
    checksum_path = data_dir.parent / "SHA256SUMS"
    checksum_path.write_text(
        "\n".join(checksum_path.read_text(encoding="utf-8").splitlines()[1:]) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ArtifactVerificationError, match="文件集合"):
        verify_artifact_release(data_dir)

    data_dir = _write_release(tmp_path / "extra")
    (data_dir / "unregistered.tmp").write_text("extra", encoding="utf-8")
    with pytest.raises(ArtifactVerificationError, match="文件集合"):
        verify_artifact_release(data_dir)


def test_verify_artifact_release_checks_vector_records_and_dimensions(tmp_path):
    data_dir = _write_release(tmp_path)
    (data_dir / "published" / "bge_m3_vector_index.jsonl").write_text(
        '{"kind":"chunk","metadata":{"chunk_id":"chunk-1"},"vector":[0.1]}\n',
        encoding="utf-8",
    )
    _rewrite_checksums(data_dir)

    with pytest.raises(ArtifactVerificationError, match="向量维度"):
        verify_artifact_release(data_dir)


def test_artifact_workspace_must_be_exact_copy_of_verified_source(tmp_path):
    data_dir = _write_release(tmp_path / "source")
    workspace = tmp_path / "workspace"
    shutil.copytree(data_dir, workspace)

    artifact_verification.verify_artifact_workspace(data_dir, workspace)
    (workspace / "published" / "chunk_catalog.jsonl").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ArtifactVerificationError, match="测试工作区"):
        artifact_verification.verify_artifact_workspace(data_dir, workspace)


def test_registered_release_must_match_registry_identity_count_hash_and_path(tmp_path):
    data_dir = _write_release(tmp_path / "releases")
    verified = verify_artifact_release(data_dir)
    registry_path = tmp_path / "artifacts" / "releases.yaml"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(yaml.safe_dump({
        "schema_version": 1,
        "current_release_id": verified["release_id"],
        "releases": [{
            "release_id": verified["release_id"],
            "source_commit": "93a4c97",
            "file_count": verified["file_count"] + 1,
            "sha256sums_sha256": verified["sha256sums_sha256"],
            "data_path": str(data_dir),
            "status": "current",
        }],
    }, sort_keys=False), encoding="utf-8")

    with pytest.raises(ArtifactVerificationError, match="file_count"):
        artifact_verification.verify_registered_artifact_release(
            data_dir,
            release_id=verified["release_id"],
            registry_path=registry_path,
        )


def test_verify_artifacts_cli_uses_configured_data_root(monkeypatch, tmp_path, capsys):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setattr(
        artifact_verification,
        "verify_registered_artifact_release",
        lambda candidate: {"data_dir": str(candidate), "release_id": "release"},
    )

    assert artifact_verification.main() == 0
    assert '"release_id": "release"' in capsys.readouterr().out
