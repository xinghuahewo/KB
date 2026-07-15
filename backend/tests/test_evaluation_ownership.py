import json

from bgpkb.domain.evaluation_ownership import load_ownership, release_ownership_status
from bgpkb import paths


CONFIG = paths.CONFIG_DIR / "rag_eval_ownership.yaml"


def test_unassigned_gold_dataset_owner_is_release_blocking():
    ownership = load_ownership(CONFIG)

    assert ownership["retrieval_gold"]["owner_status"] == "assigned"
    assert ownership["answer_gold"]["owner_status"] == "assigned"
    for record in ownership.values():
        assert record["owner"] == "吴柏橦"
        assert record["reviewers"] == ["兴华"]
        evidence = paths.PROJECT_ROOT / record["approval_evidence"]
        assert evidence.is_file()
    assert release_ownership_status(ownership, project_root=paths.PROJECT_ROOT) == {
        "status": "ready",
        "datasets": [],
    }


def test_assigned_owners_require_review_and_change_control_fields():
    ownership = {
        "retrieval_gold": {
            "owner_status": "assigned",
            "owner": "routing-quality-team",
            "reviewers": ["data-governance"],
            "change_control": "pull_request",
        },
        "answer_gold": {
            "owner_status": "assigned",
            "owner": "answer-quality-team",
            "reviewers": ["routing-quality-team"],
            "change_control": "pull_request",
        },
    }

    assert release_ownership_status(ownership) == {"status": "ready", "datasets": []}


def test_assigned_owner_cannot_self_approve_or_use_missing_evidence(tmp_path):
    base = {
        "owner_status": "assigned",
        "owner": "吴柏橦",
        "reviewers": ["兴华"],
        "change_control": "pull_request",
        "approval_evidence": "metadata/evaluation/reviews/approval.json",
    }
    ownership = {"retrieval_gold": dict(base), "answer_gold": dict(base)}

    missing = release_ownership_status(ownership, project_root=tmp_path)
    assert missing == {
        "status": "skipped_blocking",
        "reason": "evaluation_approval_evidence_invalid",
        "datasets": ["answer_gold", "retrieval_gold"],
    }

    evidence = tmp_path / base["approval_evidence"]
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({
        "schema_version": "rag_gold_approval_evidence_v1",
        "owner": "吴柏橦",
        "reviewer": "兴华",
        "datasets": ["answer_gold", "retrieval_gold"],
        "authorization_method": "user_instruction",
    }, ensure_ascii=False), encoding="utf-8")
    ownership["answer_gold"]["reviewers"] = ["吴柏橦"]
    self_review = release_ownership_status(ownership, project_root=tmp_path)
    assert self_review == {
        "status": "skipped_blocking",
        "reason": "evaluation_owner_self_approval",
        "datasets": ["answer_gold"],
    }
