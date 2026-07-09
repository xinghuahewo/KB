import json

import pytest

from bgpkb.cleaning_v2 import release


def _manifest(version, root):
    return {
        "version": version,
        "authority": str(root / f"cleaned_{version}"),
        "markdown": str(root / f"markdown_{version}"),
        "chunks": str(root / f"chunks_{version}"),
        "input_snapshot": f"sha256:{version}",
    }


def test_failed_gates_cannot_change_release_pointer(tmp_path):
    pointer = tmp_path / "pointer.json"
    release.write_pointer(pointer, _manifest("v1", tmp_path), reason="初始版本")
    before = pointer.read_bytes()

    with pytest.raises(release.ReleaseGateError):
        release.switch_release(
            pointer, _manifest("v2", tmp_path),
            gate_result={"passed": False, "blocking_issues": ["gold_annotations_incomplete"]},
            reason="尝试切换",
        )

    assert pointer.read_bytes() == before


def test_switch_is_atomic_and_downstream_resolves_versioned_paths(tmp_path):
    pointer = tmp_path / "pointer.json"
    release.write_pointer(pointer, _manifest("v1", tmp_path), reason="初始版本")

    release.switch_release(
        pointer, _manifest("v2", tmp_path), gate_result={"passed": True, "blocking_issues": []},
        reason="门禁通过",
    )
    resolved = release.resolve_release(pointer)

    assert resolved["version"] == "v2"
    assert resolved["chunks"].endswith("chunks_v2")
    assert not list(tmp_path.glob("*.tmp"))


def test_verified_rollback_restores_v1_and_preserves_v2_manifest(tmp_path):
    pointer = tmp_path / "pointer.json"
    v1 = _manifest("v1", tmp_path)
    v2 = _manifest("v2", tmp_path)
    release.write_pointer(pointer, v2, reason="已切换")
    v2_manifest = tmp_path / "v2_manifest.json"
    v2_manifest.write_text(json.dumps(v2), encoding="utf-8")

    release.rollback_to_v1(pointer, v1, reason="回滚演练")

    assert release.resolve_release(pointer)["version"] == "v1"
    assert json.loads(v2_manifest.read_text())["version"] == "v2"
    assert release.load_pointer(pointer)["history"][-1]["reason"] == "回滚演练"
