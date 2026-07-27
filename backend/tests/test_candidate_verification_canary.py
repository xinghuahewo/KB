import json
import hashlib
import os
from pathlib import Path

import pytest

from bgpkb.infrastructure import serving_bundle
from bgpkb.workflows import candidate_verification_canary


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


CODE_COMMIT = "a" * 40
PROMPT_VERSION = "grounded_answer_prompt_v1"
MODEL_REVISIONS = {
    "embedding": "embedding-revision",
    "reranker": "reranker-revision",
    "llm": "llm-revision",
}
PIPELINE_RUN_ID = "run-" + "1" * 32


def _candidate(tmp_path: Path, *, failed_stage: str | None = "verify-release") -> Path:
    candidate = tmp_path / "candidate-release"
    _write_json(
        candidate / ".pipeline" / "candidate.json",
        {
            "status": "failed",
            "reader_selectable": False,
            "failed_stage": failed_stage,
        },
    )
    _write_json(
        candidate / ".pipeline" / "manifests" / "publish-index.json",
        {"stage": "publish-index", "status": "complete"},
    )
    _write_json(
        candidate / ".pipeline" / "checkpoints" / "publish-index.json",
        {"stage": "publish-index", "status": "complete"},
    )
    _write_json(
        candidate / "data" / "published" / "publish_index_manifest_v1.json",
        {
            "release_id": candidate.name,
            "status": "complete",
            "model_revisions": {"embedding": MODEL_REVISIONS["embedding"]},
        },
    )
    (candidate / "data" / "published" / serving_bundle.SERVING_DB_FILENAME).write_bytes(
        b"candidate database"
    )
    return candidate


def _binding(candidate: Path) -> dict:
    publish_path = candidate / "data" / "published" / "publish_index_manifest_v1.json"
    checkpoint_path = candidate / ".pipeline" / "checkpoints" / "publish-index.json"
    return {
        "candidate_root": str(candidate),
        "release_id": candidate.name,
        "publish_manifest_hash": "sha256:" + hashlib.sha256(publish_path.read_bytes()).hexdigest(),
        "publish_checkpoint_hash": "sha256:" + hashlib.sha256(
            checkpoint_path.read_bytes()
        ).hexdigest(),
        "pipeline_run_id": PIPELINE_RUN_ID,
        "code_commit": CODE_COMMIT,
        "prompt_version": PROMPT_VERSION,
        "model_revisions": MODEL_REVISIONS,
        "chat_db_path": str(
            candidate
            / ".pipeline"
            / "tmp"
            / "canary-chat"
            / PIPELINE_RUN_ID
            / "history.sqlite3"
        ),
    }


def _configure_reader(monkeypatch, candidate: Path, code_manifest: Path) -> dict:
    binding = _binding(candidate)
    monkeypatch.setattr(serving_bundle, "CODE_RELEASE_MANIFEST_PATH", code_manifest)
    monkeypatch.setattr(candidate_verification_canary, "CODE_RELEASE_MANIFEST_PATH", code_manifest)
    monkeypatch.setenv(
        serving_bundle.VERIFICATION_CANDIDATE_BINDING_ENV,
        json.dumps(binding),
    )
    monkeypatch.setenv("BGP_CHAT_DB_PATH", binding["chat_db_path"])
    monkeypatch.setenv("BGPKB_CODE_COMMIT", CODE_COMMIT)
    monkeypatch.setenv("BGP_GROUNDED_PROMPT_VERSION", PROMPT_VERSION)
    monkeypatch.setenv("BGP_EMBEDDING_MODEL_REVISION", MODEL_REVISIONS["embedding"])
    monkeypatch.setenv("BGP_RERANKER_MODEL_REVISION", MODEL_REVISIONS["reranker"])
    monkeypatch.setenv("BGP_LLM_MODEL_REVISION", MODEL_REVISIONS["llm"])
    return binding


@pytest.fixture
def code_manifest(tmp_path):
    path = tmp_path / "release-manifest.json"
    _write_json(path, {"git_commit": CODE_COMMIT})
    return path


def test_candidate_reader_requires_exact_verification_scope(monkeypatch, tmp_path, code_manifest):
    candidate = _candidate(tmp_path)
    data_dir = candidate / "data"

    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(data_dir)

    binding = _configure_reader(monkeypatch, candidate, code_manifest)
    assert serving_bundle.resolve_serving_database_path(data_dir) == (
        data_dir / "published" / serving_bundle.SERVING_DB_FILENAME
    )

    binding["candidate_root"] = str(tmp_path / "other-candidate")
    monkeypatch.setenv(
        serving_bundle.VERIFICATION_CANDIDATE_BINDING_ENV,
        json.dumps(binding),
    )
    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(data_dir)


def test_candidate_reader_allows_only_verify_release_building_state(
    monkeypatch, tmp_path, code_manifest
):
    candidate = _candidate(tmp_path)
    data_dir = candidate / "data"
    binding = _configure_reader(monkeypatch, candidate, code_manifest)
    state_path = candidate / ".pipeline" / "candidate.json"
    _write_json(
        state_path,
        {
            "status": "building",
            "reader_selectable": False,
            "failed_stage": None,
            "active_target_stage": "verify-release",
            "active_run_id": PIPELINE_RUN_ID,
        },
    )
    assert serving_bundle.resolve_serving_database_path(data_dir).is_file()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["active_target_stage"] = "publish-index"
    _write_json(state_path, state)
    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(data_dir)

    state["active_target_stage"] = "verify-release"
    state["active_run_id"] = "run-" + "2" * 32
    _write_json(state_path, state)
    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(data_dir)

    assert binding["publish_manifest_hash"].startswith("sha256:")


def test_candidate_reader_rejects_failure_before_verify_release(
    monkeypatch, tmp_path, code_manifest
):
    candidate = _candidate(tmp_path, failed_stage="canonicalize")
    binding = _configure_reader(monkeypatch, candidate, code_manifest)

    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(candidate / "data")
    with pytest.raises(
        candidate_verification_canary.CandidateVerificationCanaryError,
        match="publish-index",
    ):
        candidate_verification_canary.validate_candidate(
            candidate,
            release_id=candidate.name,
            publish_manifest_hash=binding["publish_manifest_hash"],
            publish_checkpoint_hash=binding["publish_checkpoint_hash"],
            code_commit=CODE_COMMIT,
            prompt_version=PROMPT_VERSION,
            model_revisions=MODEL_REVISIONS,
        )


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("release_id", "other-release"),
        ("publish_manifest_hash", "sha256:" + "0" * 64),
        ("publish_checkpoint_hash", "sha256:" + "0" * 64),
        ("code_commit", "b" * 40),
        ("prompt_version", ""),
    ],
)
def test_candidate_validation_rejects_identity_binding_mismatch(
    monkeypatch, tmp_path, code_manifest, field, wrong_value
):
    candidate = _candidate(tmp_path)
    binding = _configure_reader(monkeypatch, candidate, code_manifest)
    binding[field] = wrong_value

    with pytest.raises(candidate_verification_canary.CandidateVerificationCanaryError):
        candidate_verification_canary.validate_candidate(
            candidate,
            release_id=binding["release_id"],
            publish_manifest_hash=binding["publish_manifest_hash"],
            publish_checkpoint_hash=binding["publish_checkpoint_hash"],
            code_commit=binding["code_commit"],
            prompt_version=binding["prompt_version"],
            model_revisions=binding["model_revisions"],
        )


@pytest.mark.parametrize("role", ["embedding", "reranker", "llm"])
def test_candidate_reader_rejects_model_revision_mismatch(
    monkeypatch, tmp_path, code_manifest, role
):
    candidate = _candidate(tmp_path)
    binding = _configure_reader(monkeypatch, candidate, code_manifest)
    binding["model_revisions"] = {**MODEL_REVISIONS, role: "wrong-revision"}
    monkeypatch.setenv(
        serving_bundle.VERIFICATION_CANDIDATE_BINDING_ENV,
        json.dumps(binding),
    )

    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(candidate / "data")


def test_candidate_canary_rejects_production_chat_database(monkeypatch, tmp_path):
    candidate = _candidate(tmp_path)
    production_chat_db = tmp_path / "production.sqlite3"
    monkeypatch.setenv("BGP_CHAT_DB_PATH", str(production_chat_db))

    with pytest.raises(
        candidate_verification_canary.CandidateVerificationCanaryError,
        match="生产会话库",
    ):
        candidate_verification_canary.validate_chat_db_path(
            candidate,
            production_chat_db,
            PIPELINE_RUN_ID,
        )


def test_verification_environment_is_process_scoped_and_cleans_chat_files(
    monkeypatch, tmp_path
):
    candidate = _candidate(tmp_path)
    binding = _binding(candidate)
    chat_db = Path(binding["chat_db_path"])
    monkeypatch.setenv("BGPKB_DATA_DIR", "/production/data")
    monkeypatch.delenv(serving_bundle.VERIFICATION_CANDIDATE_BINDING_ENV, raising=False)

    with candidate_verification_canary.verification_environment(
        binding=binding,
        chat_db_path=chat_db,
    ):
        chat_db.write_bytes(b"chat")
        Path(str(chat_db) + "-wal").write_bytes(b"wal")
        assert os.environ["BGPKB_DATA_DIR"] == str(candidate / "data")
        assert serving_bundle.VERIFICATION_CANDIDATE_BINDING_ENV in os.environ

    assert os.environ["BGPKB_DATA_DIR"] == "/production/data"
    assert serving_bundle.VERIFICATION_CANDIDATE_BINDING_ENV not in os.environ
    assert not chat_db.exists()
    assert not Path(str(chat_db) + "-wal").exists()


def test_cleanup_chat_database_is_idempotent(tmp_path):
    candidate = tmp_path / "candidate"
    chat_db = (
        candidate
        / ".pipeline"
        / "tmp"
        / "canary-chat"
        / PIPELINE_RUN_ID
        / "verification.sqlite3"
    )
    chat_db.parent.mkdir(parents=True)
    for suffix in ("", "-wal", "-shm"):
        Path(str(chat_db) + suffix).write_bytes(b"temporary")

    candidate_verification_canary.cleanup_chat_database(
        candidate, chat_db, PIPELINE_RUN_ID
    )
    candidate_verification_canary.cleanup_chat_database(
        candidate, chat_db, PIPELINE_RUN_ID
    )

    assert not any(Path(str(chat_db) + suffix).exists() for suffix in ("", "-wal", "-shm"))


def test_cleanup_chat_database_rejects_path_outside_candidate(tmp_path):
    candidate = tmp_path / "candidate"
    production_chat = tmp_path / "production.sqlite3"
    production_chat.write_bytes(b"do not delete")

    with pytest.raises(
        candidate_verification_canary.CandidateVerificationCanaryError,
        match="拒绝清理",
    ):
        candidate_verification_canary.cleanup_chat_database(
            candidate,
            production_chat,
            PIPELINE_RUN_ID,
        )

    assert production_chat.read_bytes() == b"do not delete"


def test_verification_environment_cleans_on_exception(tmp_path):
    candidate = _candidate(tmp_path)
    binding = _binding(candidate)
    chat_db = Path(binding["chat_db_path"])

    with pytest.raises(RuntimeError, match="evaluation failed"):
        with candidate_verification_canary.verification_environment(
            binding=binding,
            chat_db_path=chat_db,
        ):
            chat_db.write_bytes(b"chat")
            Path(str(chat_db) + "-wal").write_bytes(b"wal")
            Path(str(chat_db) + "-shm").write_bytes(b"shm")
            raise RuntimeError("evaluation failed")

    assert not any(Path(str(chat_db) + suffix).exists() for suffix in ("", "-wal", "-shm"))


def test_run_server_timeout_sets_exit_and_cancels_timer(monkeypatch):
    events: list[str] = []

    class FakeTimer:
        daemon = False

        def __init__(self, seconds, callback):
            assert seconds == 7
            self.callback = callback

        def start(self):
            events.append("start")
            self.callback()

        def cancel(self):
            events.append("cancel")

    class FakeServer:
        should_exit = False

        def run(self):
            assert self.should_exit is True
            events.append("run")

    monkeypatch.setattr(candidate_verification_canary.threading, "Timer", FakeTimer)
    candidate_verification_canary.run_server_with_timeout(FakeServer(), 7)

    assert events == ["start", "run", "cancel"]


def test_run_server_exception_still_cancels_timer(monkeypatch):
    events: list[str] = []

    class FakeTimer:
        daemon = False

        def __init__(self, _seconds, _callback):
            pass

        def start(self):
            events.append("start")

        def cancel(self):
            events.append("cancel")

    class FailingServer:
        def run(self):
            raise RuntimeError("server failed")

    monkeypatch.setattr(candidate_verification_canary.threading, "Timer", FakeTimer)
    with pytest.raises(RuntimeError, match="server failed"):
        candidate_verification_canary.run_server_with_timeout(FailingServer(), 7)

    assert events == ["start", "cancel"]


@pytest.mark.parametrize("host", ["0.0.0.0", "10.99.8.28", "example.com", "localhost"])
def test_candidate_verification_canary_rejects_non_loopback_host(host):
    assert candidate_verification_canary.is_loopback_host(host) is False


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_candidate_verification_canary_accepts_loopback_host(host):
    assert candidate_verification_canary.is_loopback_host(host) is True
