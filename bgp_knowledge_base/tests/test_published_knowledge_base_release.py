import json

from bgpkb.pipeline import build_published_knowledge_base as published
from bgpkb.pipeline import build_sqlite_knowledge_base as sqlite_builder


def test_published_chunk_catalog_resolves_active_release(tmp_path):
    chunks = tmp_path / "data/corpus/chunks_v2"
    chunks.mkdir(parents=True)
    (chunks / "doc-a.jsonl").write_text(
        json.dumps(
            {
                "chunk_id": "chunk-v2-a",
                "doc_id": "doc-a",
                "content": "approved v2 content",
                "review_status": "approved",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    pointer = tmp_path / "metadata/config/corpus_release_pointer.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(
        json.dumps(
            {
                "active": {
                    "version": "v2",
                    "authority": "data/corpus/cleaned_blocks_v2",
                    "markdown": "data/corpus/markdown_v2",
                    "chunks": "data/corpus/chunks_v2",
                    "input_snapshot": "sha256:v2-snapshot",
                }
            }
        ),
        encoding="utf-8",
    )

    active = published.resolve_active_release(pointer, project_root=tmp_path)
    catalog = published.build_chunk_catalog(
        active["chunks_path"],
        project_root=tmp_path,
        sources_by_doc={
            "doc-a": {
                "source_type": "standard",
                "title": "RFC fixture",
                "language": "en",
            }
        },
    )

    assert active["manifest"]["version"] == "v2"
    assert active["manifest"]["input_snapshot"] == "sha256:v2-snapshot"
    assert [row["chunk_id"] for row in catalog] == ["chunk-v2-a"]
    assert catalog[0]["chunk_file"] == "data/corpus/chunks_v2/doc-a.jsonl"
    assert catalog[0]["source_type"] == "standard"
    assert catalog[0]["title"] == "RFC fixture"


def test_historical_review_evidence_is_segregated_from_active_chunks():
    rows = sqlite_builder.build_historical_evidence_chunks(
        [
            {
                "chunk_id": "legacy-chunk-a",
                "chunk_file": "data/corpus/chunks/paper_chunks.jsonl",
                "doc_id": "doc-a",
                "source_ref": "data/sources/raw/doc-a.pdf#page-1",
                "chunk_type": "paper_method_source",
            },
            {
                "chunk_id": "legacy-chunk-a",
                "chunk_file": "data/corpus/chunks/paper_chunks.jsonl",
                "doc_id": "doc-a",
                "source_ref": "data/sources/raw/doc-a.pdf#page-1",
                "chunk_type": "paper_method_source",
            },
        ],
        corpus_version="v1",
    )

    assert rows == [
        {
            "chunk_id": "legacy-chunk-a",
            "chunk_file": "data/corpus/chunks/paper_chunks.jsonl",
            "doc_id": "doc-a",
            "source_ref": "data/sources/raw/doc-a.pdf#page-1",
            "chunk_type": "paper_method_source",
            "corpus_version": "v1",
        }
    ]
