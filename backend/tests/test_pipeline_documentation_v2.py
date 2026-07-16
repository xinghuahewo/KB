from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_long_lived_pipeline_document_is_the_single_five_stage_entrypoint():
    pipeline_doc = REPOSITORY_ROOT / "docs" / "pipeline.md"
    assert pipeline_doc.is_file()
    content = pipeline_doc.read_text(encoding="utf-8")

    for heading in (
        "## 五阶段入口",
        "## 候选目录边界",
        "## Checkpoint 与恢复",
        "## publish-index 制品闭包",
        "## 迁移与完整重建",
        "## verify-release 统一门禁",
        "## 成对发布与回滚",
        "## 故障诊断",
    ):
        assert heading in content
    for stage in (
        "source-ingest",
        "canonicalize",
        "semantic-build",
        "publish-index",
        "verify-release",
    ):
        assert f"make {stage}" in content
    for artifact in (
        "source_catalog.jsonl",
        "chunk_catalog.jsonl",
        "retrieval_documents_v1.jsonl",
        "serving.sqlite",
        "governance.sqlite",
        "bge_m3_vector_index.jsonl",
        "bge_m3_vector_matrix.npy",
        "bge_m3_vector_metadata.jsonl",
        "bge_m3_vector_fast_manifest.json",
        "artifact_manifest.jsonl",
        "publish_index_manifest_v1.json",
    ):
        assert artifact in content
    assert "不得自动切换" in content
    assert "代码 generation" in content
    assert "previous" in content


def test_document_indexes_link_to_pipeline_without_discarding_traceability():
    root_readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    docs_readme = (REPOSITORY_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    for content in (root_readme, docs_readme):
        assert "docs/pipeline.md" in content or "pipeline.md" in content

    for retained in (
        "docs/adr/0001-modular-monolith.md",
        "docs/adr/0002-server-artifact-store.md",
        "docs/adr/0003-retain-screen.md",
        "docs/adr/0004-exact-dedup-first.md",
        "docs/adr/0005-openapi-operation-partition.md",
        "docs/baselines/rag-evidence-pipeline-v2.md",
        "docs/archive-map.md",
        "docs/quality/rag-answer-gold-scoring-v1.md",
    ):
        assert (REPOSITORY_ROOT / retained).is_file()
