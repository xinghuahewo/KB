from __future__ import annotations

import hashlib
import json
import os
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


def _set_original_inputs_private(inputs):
    paths = [
        Path(inputs["plan_path"]),
        Path(inputs["source_manifest"]),
        *Path(inputs["source_store"]).rglob("*"),
    ]
    regular_files = [path for path in paths if path.is_file()]
    for path in regular_files:
        path.chmod(0o600)
    return {path: path.stat().st_mode & 0o777 for path in regular_files}


def _runtime_evidence(candidate, runtime_identity):
    path = candidate / "data" / "manifests" / "docling_runtime_evidence_v1.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "docling_runtime_evidence_v1",
                "release_id": candidate.name,
                "status": "complete",
                "runtime": runtime_identity,
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
    path.chmod(0o600)
    return path


def test_staging_copies_only_declared_hash_bound_inputs_and_keeps_original_0600(
    tmp_path,
):
    from bgpkb.ingestion.candidate_docling_reprocess import _stage_container_inputs

    inputs = _write_inputs(tmp_path, count=2)
    candidate = Path(inputs["candidate"])
    plan_path = Path(inputs["plan_path"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["sources"] = plan["sources"][:1]
    plan["summary"]["requested"] = 1
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    runtime_identity = {
        "pipeline_revision": "docling-html-reprocess-v1",
        "parser_version": "2.107.0",
        "image": "bgpkb-docling-v2:2.107.0-cu128",
        "image_digest": IMAGE_DIGEST,
        "gpu_index": 1,
        "device": "nvidia.com/gpu=1",
        "network": "none",
    }
    evidence = _runtime_evidence(candidate, runtime_identity)
    original_modes = _set_original_inputs_private(inputs)

    staged = _stage_container_inputs(
        candidate_dir=candidate,
        runtime_tmp=candidate / ".pipeline" / "tmp" / "run-test" / "input",
        source_manifest_path=Path(inputs["source_manifest"]),
        source_store_root=Path(inputs["source_store"]),
        plan_path=plan_path,
        runtime_evidence_path=evidence,
        plan=plan,
    )

    staged_manifest = json.loads(staged["source_manifest"].read_text(encoding="utf-8"))
    assert [row["source_id"] for row in staged_manifest["sources"]] == [
        inputs["source_ids"][0]
    ]
    staged_objects = [path for path in staged["source_store"].rglob("*") if path.is_file()]
    assert len(staged_objects) == 1
    assert all(path.stat().st_mode & 0o777 == 0o444 for path in staged_objects)
    assert staged["root"].stat().st_mode & 0o777 == 0o555
    assert all(path.stat().st_mode & 0o777 == mode for path, mode in original_modes.items())


@pytest.mark.parametrize("link_kind", ["symlink", "hardlink"])
def test_staging_rejects_linked_source_objects(tmp_path, link_kind):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        _stage_container_inputs,
    )

    inputs = _write_inputs(tmp_path, count=1)
    candidate = Path(inputs["candidate"])
    plan = json.loads(Path(inputs["plan_path"]).read_text(encoding="utf-8"))
    object_path = (
        Path(inputs["source_store"]) / plan["sources"][0]["object_path"]
    )
    if link_kind == "symlink":
        target = tmp_path / "linked-source"
        target.write_bytes(object_path.read_bytes())
        object_path.unlink()
        object_path.symlink_to(target)
        message = "symlink"
    else:
        os.link(object_path, tmp_path / "second-link")
        message = "独立普通文件"
    evidence = _runtime_evidence(candidate, {
        "pipeline_revision": "docling-html-reprocess-v1",
        "parser_version": "2.107.0",
        "image": "bgpkb-docling-v2:2.107.0-cu128",
        "image_digest": IMAGE_DIGEST,
        "gpu_index": 1,
        "device": "nvidia.com/gpu=1",
        "network": "none",
    })

    with pytest.raises((CandidateDoclingReprocessError, ValueError), match=message):
        _stage_container_inputs(
            candidate_dir=candidate,
            runtime_tmp=candidate / ".pipeline" / "tmp" / "run-test" / "input",
            source_manifest_path=Path(inputs["source_manifest"]),
            source_store_root=Path(inputs["source_store"]),
            plan_path=Path(inputs["plan_path"]),
            runtime_evidence_path=evidence,
            plan=plan,
        )


def test_staging_rejects_hash_change_before_copy(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import _stage_container_inputs

    inputs = _write_inputs(tmp_path, count=1)
    candidate = Path(inputs["candidate"])
    plan = json.loads(Path(inputs["plan_path"]).read_text(encoding="utf-8"))
    object_path = Path(inputs["source_store"]) / plan["sources"][0]["object_path"]
    object_path.write_bytes(object_path.read_bytes() + b"changed")
    evidence = _runtime_evidence(candidate, {
        "pipeline_revision": "docling-html-reprocess-v1",
        "parser_version": "2.107.0",
        "image": "bgpkb-docling-v2:2.107.0-cu128",
        "image_digest": IMAGE_DIGEST,
        "gpu_index": 1,
        "device": "nvidia.com/gpu=1",
        "network": "none",
    })

    with pytest.raises(Exception, match="hash"):
        _stage_container_inputs(
            candidate_dir=candidate,
            runtime_tmp=candidate / ".pipeline" / "tmp" / "run-test" / "input",
            source_manifest_path=Path(inputs["source_manifest"]),
            source_store_root=Path(inputs["source_store"]),
            plan_path=Path(inputs["plan_path"]),
            runtime_evidence_path=evidence,
            plan=plan,
        )


def test_staging_rejects_duplicate_declared_targets(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        _stage_container_inputs,
    )

    inputs = _write_inputs(tmp_path, count=2)
    candidate = Path(inputs["candidate"])
    plan_path = Path(inputs["plan_path"])
    manifest_path = Path(inputs["source_manifest"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_snapshot = manifest["sources"][0]["snapshot"]
    second_snapshot = manifest["sources"][1]["snapshot"]
    for field in ("object_path", "object_digest", "byte_size"):
        second_snapshot[field] = first_snapshot[field]
        plan["sources"][1][field] = first_snapshot[field]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    plan["source_ingest_manifest_sha256"] = _sha256(manifest_path.read_bytes())
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    evidence = _runtime_evidence(candidate, _locked_runtime_identity())

    with pytest.raises(CandidateDoclingReprocessError, match="目标重复"):
        _stage_container_inputs(
            candidate_dir=candidate,
            runtime_tmp=candidate / ".pipeline" / "tmp" / "run-test" / "input",
            source_manifest_path=manifest_path,
            source_store_root=Path(inputs["source_store"]),
            plan_path=plan_path,
            runtime_evidence_path=evidence,
            plan=plan,
        )


def test_atomic_payload_publish_cleans_failure_and_success_staging(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        _publish_payloads_atomically,
    )

    candidate = tmp_path / "candidate"
    staged = candidate / ".pipeline" / "tmp" / "run" / "output"
    staged.mkdir(parents=True)
    payload = staged / "source.json"
    payload.write_text('{"ok": true}\n', encoding="utf-8")
    receipt = {
        "documents": [
            {
                "source_id": "source",
                "payload_path": "source.json",
                "payload_sha256": "sha256:" + "0" * 64,
            }
        ]
    }
    formal = candidate / "data" / "derived" / "docling_payloads"

    with pytest.raises(CandidateDoclingReprocessError, match="hash"):
        _publish_payloads_atomically(
            candidate_dir=candidate,
            receipt=receipt,
            staged_payload_root=staged,
            payload_root=formal,
        )
    assert not formal.exists()
    assert not list(formal.parent.glob(".incoming-docling-payloads-*"))

    receipt["documents"][0]["payload_sha256"] = _sha256(payload.read_bytes())
    _publish_payloads_atomically(
        candidate_dir=candidate,
        receipt=receipt,
        staged_payload_root=staged,
        payload_root=formal,
    )
    assert (formal / "docling_payload_manifest_v1.json").is_file()
    assert not list(formal.parent.glob(".incoming-docling-payloads-*"))


def test_atomic_payload_publish_reuses_only_exact_existing_closure(tmp_path):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        _publish_payloads_atomically,
    )

    candidate = tmp_path / "candidate"
    staged = candidate / ".pipeline" / "tmp" / "run" / "output"
    staged.mkdir(parents=True)
    payload = staged / "source.json"
    payload.write_text('{"ok": true}\n', encoding="utf-8")
    receipt = {
        "documents": [
            {
                "source_id": "source",
                "payload_path": "source.json",
                "payload_sha256": _sha256(payload.read_bytes()),
            }
        ]
    }
    formal = candidate / "data" / "derived" / "docling_payloads"

    _publish_payloads_atomically(
        candidate_dir=candidate,
        receipt=receipt,
        staged_payload_root=staged,
        payload_root=formal,
    )
    original_payload = (formal / "source.json").read_bytes()

    _publish_payloads_atomically(
        candidate_dir=candidate,
        receipt=receipt,
        staged_payload_root=staged,
        payload_root=formal,
    )
    assert (formal / "source.json").read_bytes() == original_payload
    assert not list(formal.parent.glob(".incoming-docling-payloads-*"))

    (formal / "unexpected.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(CandidateDoclingReprocessError, match="不一致"):
        _publish_payloads_atomically(
            candidate_dir=candidate,
            receipt=receipt,
            staged_payload_root=staged,
            payload_root=formal,
        )
    assert (formal / "unexpected.json").is_file()
    assert not list(formal.parent.glob(".incoming-docling-payloads-*"))


def _locked_runtime_identity():
    return {
        "pipeline_revision": "docling-html-reprocess-v1",
        "parser_version": "2.107.0",
        "image": "bgpkb-docling-v2:2.107.0-cu128",
        "image_digest": IMAGE_DIGEST,
        "gpu_index": 1,
        "device": "nvidia.com/gpu=1",
        "network": "none",
    }


def _preflight_evidence():
    return {
        "execution_transport": "local",
        "target_host": "10.99.8.28",
        "gpu": {
            "index": 1,
            "uuid": "GPU-test-1",
            "memory_used_mib": 3,
            "memory_total_mib": 11264,
            "utilization_percent": 0,
            "active_compute_processes": 0,
        },
        "image_id": IMAGE_DIGEST,
        "preflight": {
            "ok": True,
            "gpu": {"cuda_available": True},
            "models": [
                {
                    "name": f"model-{index}",
                    "expected_sha256": f"hash-{index}",
                    "actual_sha256": f"hash-{index}",
                }
                for index in range(5)
            ],
        },
    }


def test_runner_uses_minimal_mounts_and_cleans_run_staging_on_success(
    tmp_path, monkeypatch
):
    from bgpkb.ingestion.candidate_docling_reprocess import SSHDoclingRunner
    from bgpkb.ingestion.canonicalize_candidate import load_reprocess_policy
    from bgpkb.ingestion.docling_payload_worker import run_payload_worker

    inputs = _write_inputs(tmp_path, count=1)
    candidate = Path(inputs["candidate"])
    original_modes = _set_original_inputs_private(inputs)
    policy = load_reprocess_policy(Path(inputs["policy_path"]))
    plan = json.loads(Path(inputs["plan_path"]).read_text(encoding="utf-8"))
    captured = {}

    def command_runner(command, **kwargs):
        captured["command"] = command

        def argument(flag):
            return Path(command[command.index(flag) + 1])

        result = run_payload_worker(
            plan_path=argument("--plan"),
            source_manifest_path=argument("--source-manifest"),
            source_store_root=argument("--source-store"),
            output_root=argument("--output-root"),
            input_work_root=argument("--input-work-root"),
            receipt_path=argument("--receipt"),
            runtime_evidence_path=argument("--runtime-evidence"),
            release_id=command[command.index("--release-id") + 1],
            parser=lambda source: _payload(source.stem),
        )
        return subprocess.CompletedProcess(
            command, 0, json.dumps(result["summary"]), ""
        )

    runner = SSHDoclingRunner(
        command_runner=command_runner,
        local_address_resolver=lambda _host: {"10.99.8.28"},
    )
    monkeypatch.setattr(
        runner, "_preflight", lambda *, policy: _preflight_evidence()
    )
    receipt = runner(
        candidate_dir=candidate,
        plan=plan,
        plan_path=Path(inputs["plan_path"]),
        source_manifest_path=Path(inputs["source_manifest"]),
        source_store_root=Path(inputs["source_store"]),
        payload_root=candidate / "data" / "derived" / "docling_payloads",
        code_root=Path(__file__).parents[2],
        release_id=candidate.name,
        runtime_identity=_locked_runtime_identity(),
        policy=policy,
    )

    assert receipt["status"] == "complete"
    command = captured["command"]
    mounts = [command[index + 1] for index, value in enumerate(command) if value == "--mount"]
    assert all(f"src={candidate},dst={candidate}" not in mount for mount in mounts)
    assert all(str(inputs["source_store"]) not in mount for mount in mounts)
    assert all(str(inputs["source_manifest"]) not in mount for mount in mounts)
    assert all(str(inputs["plan_path"]) not in mount for mount in mounts)
    assert any(
        "/input/readonly-inputs" in mount and mount.endswith(",readonly")
        for mount in mounts
    )
    assert "--user" not in command
    assert (candidate / "data/derived/docling_payloads/docling_payload_manifest_v1.json").is_file()
    runtime_base = candidate / ".pipeline" / "tmp" / "docling"
    assert runtime_base.is_dir() and not list(runtime_base.iterdir())
    assert all(path.stat().st_mode & 0o777 == mode for path, mode in original_modes.items())


def test_runner_failure_cleans_writable_staging_and_leaves_no_formal_manifest(
    tmp_path, monkeypatch
):
    from bgpkb.ingestion.candidate_docling_reprocess import (
        CandidateDoclingReprocessError,
        SSHDoclingRunner,
    )
    from bgpkb.ingestion.canonicalize_candidate import load_reprocess_policy

    inputs = _write_inputs(tmp_path, count=1)
    candidate = Path(inputs["candidate"])
    policy = load_reprocess_policy(Path(inputs["policy_path"]))
    plan = json.loads(Path(inputs["plan_path"]).read_text(encoding="utf-8"))

    def command_runner(command, **kwargs):
        output = Path(command[command.index("--output-root") + 1])
        (output / "partial.json").write_text("partial", encoding="utf-8")
        return subprocess.CompletedProcess(command, 3, "", "worker failed")

    runner = SSHDoclingRunner(
        command_runner=command_runner,
        local_address_resolver=lambda _host: {"10.99.8.28"},
    )
    monkeypatch.setattr(
        runner, "_preflight", lambda *, policy: _preflight_evidence()
    )
    with pytest.raises(CandidateDoclingReprocessError, match="worker failed"):
        runner(
            candidate_dir=candidate,
            plan=plan,
            plan_path=Path(inputs["plan_path"]),
            source_manifest_path=Path(inputs["source_manifest"]),
            source_store_root=Path(inputs["source_store"]),
            payload_root=candidate / "data" / "derived" / "docling_payloads",
            code_root=Path(__file__).parents[2],
            release_id=candidate.name,
            runtime_identity=_locked_runtime_identity(),
            policy=policy,
        )

    runtime_base = candidate / ".pipeline" / "tmp" / "docling"
    assert runtime_base.is_dir() and not list(runtime_base.iterdir())
    assert not (
        candidate / "data/derived/docling_payloads/docling_payload_manifest_v1.json"
    ).exists()
    assert not list((candidate / "data/derived").glob(".incoming-docling-payloads-*"))


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
