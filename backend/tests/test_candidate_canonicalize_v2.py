from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bgpkb.ingestion.canonical_contract import validate_canonical_document
from bgpkb.ingestion.canonicalize_candidate import (
    CanonicalizeCandidateError,
    load_reprocess_policy,
    main as canonicalize_main,
    run_candidate_canonicalize,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _snapshot(source_id: str, payload: bytes) -> dict:
    digest = _sha256(payload)
    return {
        "schema_version": "source_snapshot_v1",
        "source_id": source_id,
        "snapshot_id": f"snapshot_{'1' * 64}",
        "registry_version": "test-v1",
        "object_digest": f"sha256:{digest}",
        "object_path": f"objects/sha256/{digest}",
        "byte_size": len(payload),
        "mime_type": "application/pdf",
        "acquired_at": "2026-07-15T00:00:00Z",
        "acquisition_status": "imported",
        "origin_locator": "frozen://fixture.pdf",
        "license": {"status": "known", "identifier": "MIT", "notes": "fixture"},
        "http": {"status_code": None, "etag": None, "last_modified": None},
    }


def _legacy_document(source_id: str, source_payload: bytes, *, asset_payload: bytes = b"figure") -> dict:
    source_digest = _sha256(source_payload)
    asset_digest = _sha256(asset_payload)
    block_id = "block_v2_" + "2" * 64
    asset_id = "asset_v2_" + "3" * 64
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": source_id,
        "source": {
            "doc_id": source_id,
            "source_path": f"/frozen/{source_id}.pdf",
            "source_sha256": source_digest,
        },
        "runtime": {"pipeline_revision": "block_isolation_v2", "docling": "2.107.0"},
        "document_status": "parsed",
        "parser_mode": "docling",
        "blocks": [
            {
                "block_id": block_id,
                "doc_id": source_id,
                "page_id": "page-1",
                "page_number": 1,
                "parent_block_id": None,
                "block_type": "paragraph",
                "heading_level": None,
                "reading_order": 0,
                "bbox": {
                    "left": 0,
                    "top": 10,
                    "right": 20,
                    "bottom": 0,
                    "coord_origin": "bottom_left",
                },
                "raw_text": "BGP evidence",
                "cleaned_text": "BGP evidence",
                "language": "en",
                "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
                "provenance": {"source_anchor": "#/texts/0"},
                "review_status": "auto_approved",
                "generated_by": "fixture",
                "asset_refs": [asset_id],
            }
        ],
        "assets": [
            {
                "asset_id": asset_id,
                "doc_id": source_id,
                "asset_type": "picture",
                "path": "assets/figure.png",
                "sha256": asset_digest,
                "bbox": None,
                "caption": "Figure",
                "provenance": {"source_anchor": "#/pictures/0"},
            }
        ],
        "diagnostics": [],
    }


def _write_inputs(tmp_path: Path, *, document: dict | None = None) -> dict[str, Path | dict]:
    source_id = "paper"
    source_payload = b"immutable pdf bytes"
    asset_payload = b"figure"
    snapshot = _snapshot(source_id, source_payload)
    source_store = tmp_path / "source-store"
    object_path = source_store / snapshot["object_path"]
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(source_payload)
    source_manifest = tmp_path / "source_ingest.json"
    source_manifest.write_text(
        json.dumps(
            {
                "schema_version": "source_ingest_manifest_v1",
                "status": "complete",
                "registry_version": "test-v1",
                "sources": [
                    {
                        "source_id": source_id,
                        "required": True,
                        "status": "imported",
                        "snapshot": snapshot,
                    }
                ],
                "summary": {"imported": 1, "missing": 0, "failed": 0},
            }
        ),
        encoding="utf-8",
    )
    frozen_canonical = tmp_path / "frozen-canonical"
    frozen_canonical.mkdir()
    if document is None:
        document = _legacy_document(source_id, source_payload, asset_payload=asset_payload)
    (frozen_canonical / f"{source_id}.json").write_text(
        json.dumps(document), encoding="utf-8"
    )
    frozen_assets = tmp_path / "frozen-assets"
    asset_path = frozen_assets / source_id / "assets" / "figure.png"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(asset_payload)
    policy = tmp_path / "canonical_reprocess_policy.yaml"
    policy.write_text(
        "\n".join(
            [
                "schema_version: canonical_reprocess_policy_v1",
                "policy_version: test-v1",
                "affected_source_ids: []",
                "docling:",
                "  ssh_target: root@10.99.8.28",
                "  gpu_index: 1",
                "  device: nvidia.com/gpu=1",
                "  network: none",
                "  image: bgpkb-docling-v2:2.107.0-cu128",
                "  image_digest: sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "source_id": source_id,
        "snapshot": snapshot,
        "source_manifest": source_manifest,
        "source_store": source_store,
        "frozen_canonical": frozen_canonical,
        "frozen_assets": frozen_assets,
        "policy": policy,
    }


def test_candidate_canonicalize_upgrades_only_metadata_and_closes_assets(tmp_path):
    inputs = _write_inputs(tmp_path)
    output_root = tmp_path / "candidate" / "data" / "corpus" / "canonical"
    output_assets = tmp_path / "candidate" / "data" / "corpus" / "assets_v2"
    manifest_path = tmp_path / "candidate" / "data" / "manifests" / "canonical_documents_v2.json"

    result = run_candidate_canonicalize(
        source_manifest_path=inputs["source_manifest"],
        source_store_root=inputs["source_store"],
        frozen_canonical_root=inputs["frozen_canonical"],
        frozen_assets_root=inputs["frozen_assets"],
        output_root=output_root,
        output_assets_root=output_assets,
        manifest_path=manifest_path,
        reprocess_policy_path=inputs["policy"],
        release_id="candidate-11-2",
    )

    assert result["status"] == "complete"
    assert result["summary"] == {
        "sources": 1,
        "valid_reused": 0,
        "metadata_upgraded": 1,
        "docling_reprocess": 0,
        "documents_written": 1,
        "assets_copied": 1,
    }
    assert result["docling"]["execution_count"] == 0
    assert result["docling"]["route"]["gpu_index"] == 1
    assert result["docling"]["route"]["device"] == "nvidia.com/gpu=1"
    assert result["docling_reprocess_queue"] == []

    upgraded = json.loads((output_root / "paper.json").read_text(encoding="utf-8"))
    assert upgraded["blocks"][0]["block_id"] == "block_v2_" + "2" * 64
    assert upgraded["blocks"][0]["content_quality_status"] == "approved"
    assert upgraded["source"] == inputs["snapshot"]
    assert validate_canonical_document(
        upgraded, known_snapshot_ids={inputs["snapshot"]["snapshot_id"]}
    ) == []
    assert (output_assets / "paper" / "assets" / "figure.png").read_bytes() == b"figure"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == result


def test_candidate_canonicalize_fails_closed_and_records_docling_queue(tmp_path):
    inputs = _write_inputs(tmp_path, document={"schema_version": "broken"})
    candidate = tmp_path / "candidate"
    manifest_path = candidate / "data" / "manifests" / "canonical_documents_v2.json"

    exit_code = canonicalize_main(
        [
            "--source-manifest",
            str(inputs["source_manifest"]),
            "--source-store",
            str(inputs["source_store"]),
            "--frozen-canonical-root",
            str(inputs["frozen_canonical"]),
            "--frozen-assets-root",
            str(inputs["frozen_assets"]),
            "--output-root",
            str(candidate / "data" / "corpus" / "canonical"),
            "--output-assets-root",
            str(candidate / "data" / "corpus" / "assets_v2"),
            "--manifest",
            str(manifest_path),
            "--reprocess-policy",
            str(inputs["policy"]),
            "--release-id",
            "candidate-11-2",
        ]
    )

    assert exit_code != 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "blocked_reprocess_required"
    assert manifest["summary"]["docling_reprocess"] == 1
    assert manifest["summary"]["documents_written"] == 0
    assert manifest["docling"]["execution_count"] == 0
    assert manifest["docling_reprocess_queue"][0]["source_id"] == "paper"
    assert manifest["docling_reprocess_queue"][0]["reason"] == "legacy_schema_version"


def test_candidate_canonicalize_rejects_asset_hash_mismatch(tmp_path):
    inputs = _write_inputs(tmp_path)
    (inputs["frozen_assets"] / "paper" / "assets" / "figure.png").write_bytes(b"tampered")

    with pytest.raises(CanonicalizeCandidateError, match="asset hash"):
        run_candidate_canonicalize(
            source_manifest_path=inputs["source_manifest"],
            source_store_root=inputs["source_store"],
            frozen_canonical_root=inputs["frozen_canonical"],
            frozen_assets_root=inputs["frozen_assets"],
            output_root=tmp_path / "candidate" / "canonical",
            output_assets_root=tmp_path / "candidate" / "assets",
            manifest_path=tmp_path / "candidate" / "manifest.json",
            reprocess_policy_path=inputs["policy"],
            release_id="candidate-11-2",
        )


def test_docling_reprocess_policy_fails_closed_for_any_route_other_than_gpu_1(tmp_path):
    policy = tmp_path / "bad.yaml"
    policy.write_text(
        "\n".join(
            [
                "schema_version: canonical_reprocess_policy_v1",
                "policy_version: test-v1",
                "affected_source_ids: []",
                "docling:",
                "  ssh_target: root@10.99.8.28",
                "  gpu_index: 0",
                "  device: nvidia.com/gpu=0",
                "  network: none",
                "  image: bgpkb-docling-v2:2.107.0-cu128",
                "  image_digest: sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(CanonicalizeCandidateError, match="GPU 1"):
        load_reprocess_policy(policy)
