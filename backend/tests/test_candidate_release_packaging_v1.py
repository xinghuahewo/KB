import hashlib
import json
from pathlib import Path

import pytest


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _candidate(tmp_path: Path, *, verified: bool = True) -> Path:
    candidate = tmp_path / "candidate-release-a"
    _write_json(
        candidate / ".pipeline" / "candidate.json",
        {
            "schema_version": "pipeline_candidate_state_v1",
            "status": "verified" if verified else "candidate",
            "reader_selectable": verified,
        },
    )
    published = candidate / "data" / "published"
    _write_json(
        published / "publish_index_manifest_v1.json",
        {
            "schema_version": "publish_index_manifest_v1",
            "release_id": candidate.name,
            "status": "complete",
            "artifact_count": 1,
            "artifacts": {
                "serving_sqlite": {
                    "path": "published/serving.sqlite",
                    "release_id": candidate.name,
                    "sha256": "sha256:" + "1" * 64,
                    "record_count": 1,
                }
            },
            "identity_closure": {"retrieval_document_count": 1},
        },
    )
    _write_json(
        published / "release_verification_report_v1.json",
        {
            "schema_version": "release_verification_report_v1",
            "status": "passed",
            "exit_code": 0,
            "candidate": {"release_id": candidate.name},
            "gates": [
                {"gate_id": "api_contract", "status": "pass"},
                {"gate_id": "artifact_integrity", "status": "pass"},
            ],
        },
    )
    _write_json(
        published / "chunk_id_migration_report_v1.json",
        {
            "schema_version": "chunk_id_migration_report_v1",
            "status": "passed",
            "old_chunk_count": 10,
            "new_chunk_count": 7,
        },
    )
    _write_json(
        published / "evidence_governance_migration_diff_v1.json",
        {
            "schema_version": "evidence_governance_migration_diff_v1",
            "blockers": [],
            "statistics": {"record_count": 7, "ineligible": 2},
        },
    )
    (published / "serving.sqlite").write_bytes(b"sqlite fixture")
    return candidate


def test_package_candidate_release_is_atomic_and_binds_pair_and_reports(
    monkeypatch, tmp_path
):
    from bgpkb.publishing import package_candidate_release as packaging

    candidate = _candidate(tmp_path)
    output_root = tmp_path / "artifact-releases"
    code_release = tmp_path / "code-releases" / "code-a"
    code_release.mkdir(parents=True)
    _write_json(
        code_release / "release-manifest.json",
        {
            "schema_version": 1,
            "release_id": "code-a",
            "git_commit": "a" * 40,
            "frontend_sha256": "b" * 64,
        },
    )
    previous_code = tmp_path / "code-releases" / "code-previous"
    previous_artifact = tmp_path / "artifact-releases" / "artifact-previous"
    previous_code.mkdir()
    previous_artifact.mkdir(parents=True)
    monkeypatch.setattr(
        packaging,
        "verify_publish_index_manifest",
        lambda data_dir, manifest_path: {
            "status": "complete",
            "release_id": candidate.name,
        },
    )

    result = packaging.package_candidate_release(
        candidate_dir=candidate,
        output_root=output_root,
        code_release_dir=code_release,
        previous_code_release=previous_code,
        previous_artifact_release=previous_artifact,
        deploy_root=Path("/home/wbt/DB"),
    )

    release_root = output_root / candidate.name
    assert result["release_root"] == str(release_root.resolve())
    assert result["release_id"] == candidate.name
    assert result["code_commit"] == "a" * 40
    assert release_root.is_dir()
    assert not list(output_root.glob(f".{candidate.name}.next-*"))

    compatibility = json.loads(
        (release_root / "data/published/compatibility_report_v1.json").read_text(
            encoding="utf-8"
        )
    )
    migration = json.loads(
        (release_root / "data/published/migration_summary_v1.json").read_text(
            encoding="utf-8"
        )
    )
    rollback = json.loads(
        (release_root / "data/published/paired_rollback_plan_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert compatibility["status"] == "passed"
    assert compatibility["api_contract"] == "向后兼容扩展"
    assert migration["chunk_migration"]["old_chunk_count"] == 10
    assert rollback["automatic_switch"] is False
    assert str(previous_code.resolve()) in rollback["previous_pair"]["code_release"]
    assert str(previous_artifact.resolve()) in rollback["previous_pair"]["artifact_release"]
    assert "scripts/deployment.py rollback /home/wbt/DB" in rollback["commands"]["rollback"]

    checksum_lines = (release_root / "SHA256SUMS").read_text(
        encoding="utf-8"
    ).splitlines()
    registered = {}
    for line in checksum_lines:
        digest, relative = line.split("  ", 1)
        registered[relative] = digest
    actual_files = sorted(
        path.relative_to(release_root).as_posix()
        for path in (release_root / "data").rglob("*")
        if path.is_file()
    )
    assert sorted(registered) == actual_files
    for relative, expected in registered.items():
        assert hashlib.sha256((release_root / relative).read_bytes()).hexdigest() == expected

    package_manifest = json.loads(
        (release_root / "release-package-manifest.json").read_text(encoding="utf-8")
    )
    assert package_manifest["sha256sums_sha256"] == hashlib.sha256(
        (release_root / "SHA256SUMS").read_bytes()
    ).hexdigest()


def test_package_candidate_release_fails_closed_for_unverified_candidate(
    monkeypatch, tmp_path
):
    from bgpkb.publishing import package_candidate_release as packaging

    candidate = _candidate(tmp_path, verified=False)
    code_release = tmp_path / "code-a"
    code_release.mkdir()
    _write_json(
        code_release / "release-manifest.json",
        {
            "schema_version": 1,
            "release_id": "code-a",
            "git_commit": "a" * 40,
            "frontend_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(
        packaging,
        "verify_publish_index_manifest",
        lambda data_dir, manifest_path: {"status": "complete"},
    )

    with pytest.raises(packaging.CandidateReleasePackagingError, match="verified"):
        packaging.package_candidate_release(
            candidate_dir=candidate,
            output_root=tmp_path / "releases",
            code_release_dir=code_release,
            previous_code_release=tmp_path / "previous-code",
            previous_artifact_release=tmp_path / "previous-artifact",
            deploy_root=Path("/home/wbt/DB"),
        )

    assert not (tmp_path / "releases" / candidate.name).exists()


def test_package_candidate_release_never_overwrites_existing_release(
    monkeypatch, tmp_path
):
    from bgpkb.publishing import package_candidate_release as packaging

    candidate = _candidate(tmp_path)
    output_root = tmp_path / "releases"
    destination = output_root / candidate.name
    destination.mkdir(parents=True)
    sentinel = destination / "sentinel"
    sentinel.write_text("keep", encoding="utf-8")
    code_release = tmp_path / "code-a"
    code_release.mkdir()
    _write_json(
        code_release / "release-manifest.json",
        {
            "schema_version": 1,
            "release_id": "code-a",
            "git_commit": "a" * 40,
            "frontend_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(
        packaging,
        "verify_publish_index_manifest",
        lambda data_dir, manifest_path: {"status": "complete"},
    )

    with pytest.raises(packaging.CandidateReleasePackagingError, match="不可覆盖"):
        packaging.package_candidate_release(
            candidate_dir=candidate,
            output_root=output_root,
            code_release_dir=code_release,
            previous_code_release=tmp_path / "previous-code",
            previous_artifact_release=tmp_path / "previous-artifact",
            deploy_root=Path("/home/wbt/DB"),
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"
