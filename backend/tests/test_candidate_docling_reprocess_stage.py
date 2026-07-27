from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shlex
import subprocess

import pytest


IMAGE_DIGEST = "sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2"


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _write_inputs(tmp_path: Path, *, count: int = 27) -> dict[str, object]:
    candidate = tmp_path / "candidate"
    source_store = candidate / "source-store"
    source_manifest = candidate / "data" / "manifests" / "source_ingest.json"
    plan_path = candidate / "data" / "manifests" / "docling_reprocess_plan_v1.json"
    policy_path = tmp_path / "canonical_reprocess_policy_v1.yaml"
    source_manifest.parent.mkdir(parents=True)
    sources = []
    plan_sources = []
    source_ids = [f"html-{index:02d}" for index in range(count)]
    for source_id in source_ids:
        raw = (
            f"<html><article><h1>{source_id}</h1>"
            "<p>Providers authorize customer relationships.</p></article></html>"
        ).encode()
        digest = _sha256(raw)
        object_path = f"objects/sha256/{digest.removeprefix('sha256:')}"
        target = source_store / object_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        snapshot = {
            "schema_version": "source_snapshot_v1",
            "source_id": source_id,
            "snapshot_id": "snapshot_" + hashlib.sha256(source_id.encode()).hexdigest(),
            "registry_version": "test-v1",
            "object_digest": digest,
            "object_path": object_path,
            "byte_size": len(raw),
            "mime_type": "text/html",
            "acquired_at": "2026-07-27T00:00:00Z",
            "acquisition_status": "imported",
            "origin_locator": f"https://example.test/{source_id}",
            "license": {"status": "known", "identifier": "MIT", "notes": "fixture"},
            "http": {"status_code": None, "etag": None, "last_modified": None},
        }
        sources.append(
            {
                "source_id": source_id,
                "required": True,
                "status": "imported",
                "snapshot": snapshot,
            }
        )
        plan_sources.append(
            {
                "source_id": source_id,
                "snapshot_id": snapshot["snapshot_id"],
                "object_digest": digest,
                "object_path": object_path,
                "byte_size": len(raw),
                "mime_type": "text/html",
                "reason": "policy_affected",
            }
        )
    source_manifest.write_text(
        json.dumps(
            {
                "schema_version": "source_ingest_manifest_v1",
                "status": "complete",
                "registry_version": "test-v1",
                "sources": sources,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": "docling_reprocess_plan_v1",
                "release_id": candidate.name,
                "status": "ready",
                "source_ingest_manifest_sha256": _sha256(source_manifest.read_bytes()),
                "summary": {"requested": count},
                "sources": plan_sources,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    policy_path.write_text(
        "\n".join(
            [
                "schema_version: canonical_reprocess_policy_v1",
                "policy_version: test-v1",
                "affected_source_ids:",
                *[f"  - {source_id}" for source_id in source_ids],
                "docling:",
                "  ssh_target: root@10.99.8.28",
                "  gpu_index: 1",
                "  device: nvidia.com/gpu=1",
                "  network: none",
                "  image: bgpkb-docling-v2:2.107.0-cu128",
                f"  image_digest: {IMAGE_DIGEST}",
                "  pipeline_revision: docling-html-reprocess-v1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["reprocess_policy"] = {
        "policy_version": "test-v1",
        "sha256": _sha256(policy_path.read_bytes()),
        "affected_source_ids": source_ids,
    }
    plan_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
    return {
        "candidate": candidate,
        "source_store": source_store,
        "source_manifest": source_manifest,
        "plan_path": plan_path,
        "policy_path": policy_path,
        "source_ids": source_ids,
    }


def _payload(source_id: str) -> dict:
    return {
        "body": {"children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}]},
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "title",
                "text": source_id,
                "orig": source_id,
                "level": 1,
            },
            {
                "self_ref": "#/texts/1",
                "label": "text",
                "text": "Providers authorize customer relationships.",
                "orig": "Providers authorize customer relationships.",
            },
        ],
    }


class MockRemoteRunner:
    def __init__(self, *, mutate_receipt=None, failed_source: str | None = None):
        self.calls: list[dict] = []
        self.mutate_receipt = mutate_receipt
        self.failed_source = failed_source

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        payload_root = Path(kwargs["payload_root"])
        payload_root.mkdir(parents=True, exist_ok=True)
        documents = []
        for row in kwargs["plan"]["sources"]:
            source_id = row["source_id"]
            payload_path = payload_root / f"{source_id}.json"
            payload_path.write_text(json.dumps(_payload(source_id)) + "\n", encoding="utf-8")
            documents.append(
                {
                    "source_id": source_id,
                    "status": "failed" if source_id == self.failed_source else "complete",
                    "source_sha256": row["object_digest"],
                    "payload_path": payload_path.name,
                    "payload_sha256": _sha256(payload_path.read_bytes()),
                    "parser_version": "2.107.0",
                    "pipeline_revision": "docling-html-reprocess-v1",
                    "diagnostics": (
                        [{"code": "conversion_failed"}]
                        if source_id == self.failed_source
                        else []
                    ),
                }
            )
        receipt = {
            "schema_version": "docling_payload_manifest_v1",
            "release_id": kwargs["release_id"],
            "status": "failed" if self.failed_source else "complete",
            "runtime": kwargs["runtime_identity"],
            "model_evidence": [
                {
                    "name": f"model-{index}",
                    "expected_sha256": f"hash-{index}",
                    "actual_sha256": f"hash-{index}",
                }
                for index in range(5)
            ],
            "summary": {
                "requested": len(documents),
                "complete": len(documents) - bool(self.failed_source),
                "failed": int(bool(self.failed_source)),
            },
            "documents": documents,
        }
        if self.mutate_receipt:
            self.mutate_receipt(receipt)
        return receipt


def _run(inputs: dict[str, object], *, execution_mode="remote", remote_runner=None):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        run_candidate_docling_reprocess,
    )

    candidate = Path(inputs["candidate"])
    return run_candidate_docling_reprocess(
        candidate_dir=candidate,
        plan_path=Path(inputs["plan_path"]),
        source_manifest_path=Path(inputs["source_manifest"]),
        source_store_root=Path(inputs["source_store"]),
        payload_root=candidate / "data" / "derived" / "docling_payloads",
        output_root=candidate / "data" / "corpus" / "docling_reprocessed",
        manifest_path=(
            candidate
            / "data"
            / "corpus"
            / "docling_reprocessed"
            / "docling_reprocess_manifest_v1.json"
        ),
        policy_path=Path(inputs["policy_path"]),
        release_id=candidate.name,
        execution_mode=execution_mode,
        remote_runner=remote_runner,
    )


def test_explicit_remote_mode_orchestrates_all_27_policy_affected_sources(tmp_path):
    inputs = _write_inputs(tmp_path)
    runner = MockRemoteRunner()

    result = _run(inputs, remote_runner=runner)

    assert len(runner.calls) == 1
    assert [row["source_id"] for row in runner.calls[0]["plan"]["sources"]] == inputs["source_ids"]
    assert result["status"] == "complete"
    assert result["summary"] == {"requested": 27, "materialized": 27, "failed": 0}
    assert len(result["documents"]) == 27
    assert all(row["status"] == "complete" for row in result["documents"])
    assert all(row["source_sha256"].startswith("sha256:") for row in result["documents"])
    assert all(row["canonical_sha256"].startswith("sha256:") for row in result["documents"])
    assert all(row["parser_version"] == "2.107.0" for row in result["documents"])
    assert all(row["model_revision_sha256"].startswith("sha256:") for row in result["documents"])


def test_remote_docling_is_never_implicit(tmp_path):
    inputs = _write_inputs(tmp_path, count=1)
    runner = MockRemoteRunner()

    with pytest.raises(Exception, match="显式启用"):
        _run(inputs, execution_mode="disabled", remote_runner=runner)

    assert runner.calls == []


def test_single_document_failure_closes_the_candidate(tmp_path):
    inputs = _write_inputs(tmp_path, count=2)
    runner = MockRemoteRunner(failed_source=inputs["source_ids"][1])

    with pytest.raises(Exception, match="部分失败"):
        _run(inputs, remote_runner=runner)

    assert not (
        Path(inputs["candidate"])
        / "data"
        / "corpus"
        / "docling_reprocessed"
        / "docling_reprocess_manifest_v1.json"
    ).exists()


@pytest.mark.parametrize(
    ("mutate_receipt", "message"),
    [
        (
            lambda receipt: receipt["documents"][0].update(
                {"source_sha256": "sha256:" + "0" * 64}
            ),
            "source hash",
        ),
        (
            lambda receipt: receipt["documents"][0].update(
                {"payload_sha256": "sha256:" + "0" * 64}
            ),
            "输出 hash",
        ),
        (
            lambda receipt: receipt["documents"][0].update(
                {"payload_path": "../escape.json"}
            ),
            "越界",
        ),
    ],
)
def test_receipt_hash_and_path_mismatch_fail_closed(
    tmp_path, mutate_receipt, message
):
    inputs = _write_inputs(tmp_path, count=1)

    with pytest.raises(Exception, match=message):
        _run(
            inputs,
            remote_runner=MockRemoteRunner(mutate_receipt=mutate_receipt),
        )


def test_candidate_output_paths_must_remain_inside_candidate(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        run_candidate_docling_reprocess,
    )

    inputs = _write_inputs(tmp_path, count=1)
    candidate = Path(inputs["candidate"])
    with pytest.raises(CandidateDoclingReprocessError, match="路径越界"):
        run_candidate_docling_reprocess(
            candidate_dir=candidate,
            plan_path=Path(inputs["plan_path"]),
            source_manifest_path=Path(inputs["source_manifest"]),
            source_store_root=Path(inputs["source_store"]),
            payload_root=tmp_path / "outside-payloads",
            output_root=candidate / "data" / "corpus" / "docling_reprocessed",
            manifest_path=(
                candidate
                / "data"
                / "corpus"
                / "docling_reprocessed"
                / "docling_reprocess_manifest_v1.json"
            ),
            policy_path=Path(inputs["policy_path"]),
            release_id=candidate.name,
            execution_mode="remote",
            remote_runner=MockRemoteRunner(),
        )


def test_remote_preflight_uses_fixed_ssh_gpu1_offline_image_and_five_models(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import SSHDoclingRunner
    from bgpkb.ingestion.canonicalize_candidate import load_reprocess_policy

    inputs = _write_inputs(tmp_path, count=1)
    calls = []
    responses = iter(_successful_preflight_responses())

    def command_runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, next(responses), "")

    policy = load_reprocess_policy(Path(inputs["policy_path"]))
    result = SSHDoclingRunner(
        command_runner=command_runner,
        local_address_resolver=lambda _host: set(),
        transport_override="remote",
    )._preflight(policy=policy)

    assert result["gpu"]["index"] == 1
    assert len(result["preflight"]["models"]) == 5
    assert result["execution_transport"] == "remote"
    assert all(
        command[:8]
        == [
            "ssh",
            "-F",
            "/dev/null",
            "-o",
            "ProxyCommand=none",
            "-o",
            "ProxyJump=none",
            "root@10.99.8.28",
        ]
        for command, _kwargs in calls
    )
    docker_preflight = calls[-1][0][-1]
    assert "--device nvidia.com/gpu=1" in docker_preflight
    assert "--network none" in docker_preflight
    assert "bgpkb-docling-v2:2.107.0-cu128" in docker_preflight


def _successful_preflight_responses():
    return [
        "1, GPU-test-1, 3, 11264, 0\n",
        "",
        IMAGE_DIGEST + "\n",
        json.dumps(
            {
                "ok": True,
                "errors": [],
                "gpu": {"cuda_available": True},
                "models": [
                    {
                        "name": f"model-{index}",
                        "expected_sha256": f"hash-{index}",
                        "actual_sha256": f"hash-{index}",
                    }
                    for index in range(5)
                ],
            }
        ),
    ]


def test_target_host_runs_locked_commands_locally_without_ssh_or_environment(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import SSHDoclingRunner
    from bgpkb.ingestion.canonicalize_candidate import load_reprocess_policy

    inputs = _write_inputs(tmp_path, count=1)
    calls = []
    responses = iter(_successful_preflight_responses())

    def command_runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, next(responses), "")

    policy = load_reprocess_policy(Path(inputs["policy_path"]))
    result = SSHDoclingRunner(
        command_runner=command_runner,
        local_address_resolver=lambda _host: {"10.99.8.28"},
    )._preflight(policy=policy)

    assert result["execution_transport"] == "local"
    assert all(command[0] != "ssh" for command, _kwargs in calls)
    assert calls[0][0][0] == "nvidia-smi"
    assert calls[-1][0][:3] == ["docker", "run", "--rm"]
    assert all("env" not in kwargs for _command, kwargs in calls)
    flattened = "\n".join(" ".join(command) for command, _kwargs in calls)
    assert "DEEPSEEK" not in flattened
    assert "runtime.env" not in flattened


def test_explicit_local_transport_rejects_wrong_host_before_running_command(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        SSHDoclingRunner,
    )
    from bgpkb.ingestion.canonicalize_candidate import load_reprocess_policy

    inputs = _write_inputs(tmp_path, count=1)
    policy = load_reprocess_policy(Path(inputs["policy_path"]))
    calls = []

    with pytest.raises(CandidateDoclingReprocessError, match="本机地址不匹配"):
        SSHDoclingRunner(
            command_runner=lambda command, **kwargs: calls.append((command, kwargs)),
            local_address_resolver=lambda _host: {"10.99.8.99"},
            transport_override="local",
        )._preflight(policy=policy)

    assert calls == []


def test_local_and_remote_transports_execute_equivalent_locked_commands(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import SSHDoclingRunner
    from bgpkb.ingestion.canonicalize_candidate import load_reprocess_policy

    inputs = _write_inputs(tmp_path, count=1)
    policy = load_reprocess_policy(Path(inputs["policy_path"]))

    def collect(transport, addresses):
        calls = []
        responses = iter(_successful_preflight_responses())

        def command_runner(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, next(responses), "")

        SSHDoclingRunner(
            command_runner=command_runner,
            local_address_resolver=lambda _host: addresses,
            transport_override=transport,
        )._preflight(policy=policy)
        return calls

    local_calls = collect("local", {"10.99.8.28"})
    remote_calls = collect("remote", set())
    assert [shlex.split(command[-1]) for command in remote_calls] == local_calls


def test_container_worker_uses_snapshot_hash_and_writes_auditable_receipt(tmp_path):
    from bgpkb.ingestion.docling_payload_worker import run_payload_worker

    inputs = _write_inputs(tmp_path, count=1)
    candidate = Path(inputs["candidate"])
    runtime_evidence = candidate / "data" / "manifests" / "runtime.json"
    runtime_evidence.write_text(
        json.dumps(
            {
                "runtime": {
                    "pipeline_revision": "docling-html-reprocess-v1",
                    "parser_version": "2.107.0",
                    "image": "bgpkb-docling-v2:2.107.0-cu128",
                    "image_digest": IMAGE_DIGEST,
                    "gpu_index": 1,
                    "device": "nvidia.com/gpu=1",
                    "network": "none",
                },
                "preflight": {
                    "models": [
                        {
                            "name": f"model-{index}",
                            "expected_sha256": f"hash-{index}",
                            "actual_sha256": f"hash-{index}",
                        }
                        for index in range(5)
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    output_root = candidate / "data" / "derived" / "docling_payloads"
    input_work_root = candidate / ".pipeline" / "tmp" / "docling" / "inputs"
    receipt_path = output_root / "docling_payload_manifest_v1.json"

    result = run_payload_worker(
        plan_path=Path(inputs["plan_path"]),
        source_manifest_path=Path(inputs["source_manifest"]),
        source_store_root=Path(inputs["source_store"]),
        output_root=output_root,
        input_work_root=input_work_root,
        receipt_path=receipt_path,
        runtime_evidence_path=runtime_evidence,
        release_id=candidate.name,
        parser=lambda source: _payload(source.stem),
    )

    assert result["status"] == "complete"
    assert result["summary"] == {"requested": 1, "complete": 1, "failed": 0}
    assert result["documents"][0]["source_sha256"].startswith("sha256:")
    assert result["documents"][0]["payload_sha256"].startswith("sha256:")
    assert (input_work_root / f"{inputs['source_ids'][0]}.html").is_file()
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == result
