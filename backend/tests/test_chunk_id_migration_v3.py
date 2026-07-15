import json


def _chunk(chunk_id: str, content: str, block_ids: list[str]) -> dict:
    return {
        "chunk_id": chunk_id,
        "doc_id": "fixture-migration",
        "source_id": "fixture-migration",
        "content": content,
        "source_block_ids": block_ids,
    }


def test_chunk_id_migration_classifies_proven_equivalent_merged_split_replaced_and_retired(tmp_path):
    from bgpkb.ingestion.semantic_chunking_v3 import (
        build_chunk_id_migration,
        write_chunk_id_migration,
    )

    old = [
        _chunk("old-equivalent", "same content", ["block-equivalent"]),
        _chunk("old-merge-a", "first merged paragraph", ["block-merge-a"]),
        _chunk("old-merge-b", "second merged paragraph", ["block-merge-b"]),
        _chunk("old-split", "one old chunk becomes two bounded parts", ["block-split"]),
        _chunk("old-replaced", "obsolete rendering", ["block-replaced"]),
        _chunk("old-retired", "removed navigation", ["block-retired"]),
        _chunk("old-unproven", "same words are not enough", ["block-old-only"]),
    ]
    new = [
        _chunk("new-equivalent", "same content", ["block-equivalent"]),
        _chunk(
            "new-merged",
            "first merged paragraph\n\nsecond merged paragraph",
            ["block-merge-a", "block-merge-b"],
        ),
        _chunk("new-split-a", "one old chunk becomes", ["block-split"]),
        _chunk("new-split-b", "two bounded parts", ["block-split"]),
        _chunk("new-replaced", "new structured rendering", ["block-replaced"]),
        _chunk("new-unproven", "same words are not enough", ["block-new-only"]),
    ]

    records = build_chunk_id_migration(old, new)
    output = tmp_path / "chunk_id_migration.jsonl"
    write_chunk_id_migration(output, records)
    persisted = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert persisted == records
    by_relation = {relation: [row for row in records if row["relation"] == relation] for relation in {
        "equivalent", "merged", "split", "replaced", "retired"
    }}
    assert by_relation["equivalent"][0]["old_chunk_ids"] == ["old-equivalent"]
    assert by_relation["equivalent"][0]["new_chunk_ids"] == ["new-equivalent"]
    assert by_relation["merged"][0]["old_chunk_ids"] == ["old-merge-a", "old-merge-b"]
    assert by_relation["merged"][0]["new_chunk_ids"] == ["new-merged"]
    assert by_relation["split"][0]["old_chunk_ids"] == ["old-split"]
    assert by_relation["split"][0]["new_chunk_ids"] == ["new-split-a", "new-split-b"]
    assert by_relation["replaced"][0]["old_chunk_ids"] == ["old-replaced"]
    retired_ids = {row["old_chunk_ids"][0] for row in by_relation["retired"]}
    assert retired_ids == {"old-retired", "old-unproven"}
    assert not any(
        row["relation"] == "equivalent" and row["old_chunk_ids"] == ["old-unproven"]
        for row in records
    )
    assert not list(output.parent.glob("*.tmp"))
