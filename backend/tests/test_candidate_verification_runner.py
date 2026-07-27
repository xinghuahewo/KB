import json
from pathlib import Path

import pytest


MODEL_REVISIONS = {
    "embedding": "embedding-revision",
    "reranker": "reranker-revision",
    "llm": "llm-revision",
}


def _binding(tmp_path: Path) -> dict:
    return {
        "candidate_root": str(tmp_path / "candidate"),
        "release_id": "candidate",
        "publish_manifest_hash": "sha256:" + "a" * 64,
        "publish_checkpoint_hash": "sha256:" + "b" * 64,
        "pipeline_run_id": "run-" + "1" * 32,
        "code_commit": "c" * 40,
        "prompt_version": "grounded_answer_prompt_v1",
        "model_revisions": MODEL_REVISIONS,
        "chat_db_path": str(
            tmp_path / "candidate" / ".pipeline/tmp/canary-chat"
            / ("run-" + "1" * 32) / "verification.sqlite3"
        ),
    }


def test_stable_runner_builds_actual_bgp_revision_environment(tmp_path):
    from bgpkb.workflows.candidate_verification_runner import (
        build_verification_environment,
    )

    environment = build_verification_environment(_binding(tmp_path))

    assert environment["BGP_GROUNDED_PROMPT_VERSION"] == "grounded_answer_prompt_v1"
    assert environment["BGP_EMBEDDING_MODEL_REVISION"] == "embedding-revision"
    assert environment["BGP_RERANKER_MODEL_REVISION"] == "reranker-revision"
    assert environment["BGP_LLM_MODEL_REVISION"] == "llm-revision"
    assert "BGPKB_EMBEDDING_MODEL_REVISION" not in environment
    assert environment["BGPKB_CODE_COMMIT"] == "c" * 40


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("code_commit",), ""),
        (("prompt_version",), ""),
        (("model_revisions", "embedding"), ""),
        (("model_revisions", "reranker"), ""),
        (("model_revisions", "llm"), ""),
    ],
)
def test_runner_rejects_incomplete_binding_before_commands(
    tmp_path, path, value
):
    from bgpkb.workflows.candidate_verification_runner import (
        CandidateVerificationRunnerError,
        validate_runner_binding,
    )

    binding = _binding(tmp_path)
    if len(path) == 1:
        binding[path[0]] = value
    else:
        binding[path[0]] = {**binding[path[0]], path[1]: value}

    with pytest.raises(CandidateVerificationRunnerError):
        validate_runner_binding(binding)


def test_runner_rejects_canary_health_binding_mismatch(tmp_path):
    from bgpkb.workflows.candidate_verification_runner import (
        CandidateVerificationRunnerError,
        validate_canary_health,
    )

    binding = _binding(tmp_path)
    health = {
        "release_id": binding["release_id"],
        "degraded": False,
        "retrieval_runtime": {
            "ready": True,
            "status": "ready",
            "index_mode": "fast_numpy",
        },
        "verification_binding": json.loads(json.dumps(binding)),
    }
    health["verification_binding"]["model_revisions"]["llm"] = "wrong"

    with pytest.raises(CandidateVerificationRunnerError, match="binding"):
        validate_canary_health(health, binding)

