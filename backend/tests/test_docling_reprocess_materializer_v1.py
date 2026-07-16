from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bgpkb.ingestion.canonical_contract import validate_canonical_document


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _inputs(tmp_path: Path) -> dict[str, Path | dict]:
    source_id = "html-source"
    raw = b"<html><article><h1>ASPA</h1><p>Providers authorize customer relationships.</p></article></html>"
    digest = _sha256(raw)
    snapshot = {
        "schema_version": "source_snapshot_v1",
        "source_id": source_id,
        "snapshot_id": "snapshot_" + "1" * 64,
        "registry_version": "test-v1",
        "object_digest": "sha256:" + digest,
        "object_path": f"objects/sha256/{digest}",
        "byte_size": len(raw),
        "mime_type": "text/html",
        "acquired_at": "2026-07-15T00:00:00Z",
        "acquisition_status": "imported",
        "origin_locator": "https://example.test/aspa",
        "license": {"status": "known", "identifier": "MIT", "notes": "fixture"},
        "http": {"status_code": None, "etag": None, "last_modified": None},
    }
    source_store = tmp_path / "source-store"
    object_path = source_store / snapshot["object_path"]
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(raw)
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
            }
        ),
        encoding="utf-8",
    )
    payload_root = tmp_path / "payloads"
    payload_root.mkdir()
    payload = {
        "body": {
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/texts/1"},
            ]
        },
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "title",
                "text": "ASPA",
                "orig": "ASPA",
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
    (payload_root / f"{source_id}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return {
        "source_id": source_id,
        "snapshot": snapshot,
        "source_store": source_store,
        "source_manifest": source_manifest,
        "payload_root": payload_root,
    }


def test_materializer_creates_strict_snapshot_bound_canonical_and_manifest(tmp_path):
    from bgpkb.ingestion.docling_reprocess_materializer import (
        materialize_docling_reprocess,
    )

    inputs = _inputs(tmp_path)
    output_root = tmp_path / "canonical-overlay"
    manifest_path = output_root / "docling_reprocess_manifest_v1.json"

    result = materialize_docling_reprocess(
        source_manifest_path=inputs["source_manifest"],
        source_store_root=inputs["source_store"],
        payload_root=inputs["payload_root"],
        output_root=output_root,
        manifest_path=manifest_path,
        source_ids=[inputs["source_id"]],
        release_id="candidate-v2",
        runtime_identity={
            "pipeline_revision": "docling-html-reprocess-v1",
            "parser_version": "2.107.0",
            "image": "bgpkb-docling-v2:2.107.0-cu128",
            "image_digest": "sha256:" + "a" * 64,
            "gpu_index": 1,
            "device": "nvidia.com/gpu=1",
            "network": "none",
        },
    )

    document = json.loads(
        (output_root / "html-source.json").read_text(encoding="utf-8")
    )
    assert validate_canonical_document(
        document, known_snapshot_ids={inputs["snapshot"]["snapshot_id"]}
    ) == []
    assert document["source"] == inputs["snapshot"]
    assert document["runtime"]["pipeline_revision"] == "docling-html-reprocess-v1"
    assert document["runtime"]["parser"] == {"name": "docling", "version": "2.107.0"}
    assert [block["cleaned_text"] for block in document["blocks"]] == [
        "ASPA",
        "Providers authorize customer relationships.",
    ]
    assert result["status"] == "complete"
    assert result["summary"] == {"requested": 1, "materialized": 1, "failed": 0}
    assert result["runtime"]["gpu_index"] == 1
    assert result["runtime"]["network"] == "none"
    assert result["documents"][0]["canonical_sha256"].startswith("sha256:")
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == result


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("gpu_index", 0, "GPU 1"),
        ("network", "bridge", "network=none"),
        ("image_digest", "latest", "image digest"),
    ],
)
def test_materializer_rejects_unlocked_docling_runtime(
    tmp_path, field, value, message
):
    from bgpkb.ingestion.docling_reprocess_materializer import (
        DoclingReprocessError,
        materialize_docling_reprocess,
    )

    inputs = _inputs(tmp_path)
    runtime = {
        "pipeline_revision": "docling-html-reprocess-v1",
        "parser_version": "2.107.0",
        "image": "bgpkb-docling-v2:2.107.0-cu128",
        "image_digest": "sha256:" + "a" * 64,
        "gpu_index": 1,
        "device": "nvidia.com/gpu=1",
        "network": "none",
    }
    runtime[field] = value

    with pytest.raises(DoclingReprocessError, match=message):
        materialize_docling_reprocess(
            source_manifest_path=inputs["source_manifest"],
            source_store_root=inputs["source_store"],
            payload_root=inputs["payload_root"],
            output_root=tmp_path / "output",
            manifest_path=tmp_path / "output" / "manifest.json",
            source_ids=[inputs["source_id"]],
            release_id="candidate-v2",
            runtime_identity=runtime,
        )
