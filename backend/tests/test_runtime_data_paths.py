from pathlib import Path
import importlib
import tomllib

import pytest

from bgpkb import paths
from bgpkb.infrastructure import database
from bgpkb.infrastructure import serving_bundle
from bgpkb.retrieval import retrieval_framework
from bgpkb.retrieval import hybrid_retrieval
from bgpkb.retrieval.retrieval_data import PublishedArtifactRetrievalData
from bgpkb.retrieval.retrievers import Bm25Retriever, DenseRetriever, RetrievalChannelResult


def _serving_document():
    text = "RFC 4271 Border Gateway Protocol complete retrieval text"
    chunk_id = "semantic_chunk_v3_" + "1" * 64
    return {
        "retrieval_doc_id": "retrieval_doc_v1_" + "2" * 64,
        "chunk_id": chunk_id,
        "doc_id": "rfc4271",
        "source_id": "rfc4271",
        "title": "RFC 4271",
        "document_profile": "rfc",
        "section_path": ["BGP"],
        "semantic_unit": "paragraph",
        "source_ref": "raw/rfc4271.txt#bgp",
        "retrieval_text": text,
        "retrieval_text_hash": "sha256:" + "3" * 64,
        "retrieval_text_version": "retrieval_text_v1",
        "content_preview": text,
        "governance": {
            "parse_status": "parsed",
            "content_quality_status": "approved",
            "source_trust_status": "trusted",
            "semantic_review_status": "approved",
        },
        "eligibility": {
            "status": "eligible",
            "policy_version": "retrieval_eligibility_v1",
            "rule_id": "retrieval.eligible_reviewed_source",
            "reason": "eligible",
            "audit": {},
        },
    }


def _write_serving_database(published_dir, *, entities=()):
    published_dir.mkdir(parents=True, exist_ok=True)
    path = published_dir / "serving.sqlite"
    serving_bundle.build_serving_database(
        path,
        release_id="release-test",
        retrieval_documents=[_serving_document()],
        entities=list(entities),
    )
    return path


def test_runtime_data_dir_is_unavailable_without_explicit_configuration(monkeypatch):
    monkeypatch.delenv("BGPKB_DATA_DIR", raising=False)

    assert paths.runtime_data_dir() is None
    with pytest.raises(paths.RuntimeDataUnavailable, match="BGPKB_DATA_DIR"):
        paths.require_runtime_data_dir()


def test_runtime_data_dir_uses_configured_directory(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))

    assert paths.runtime_data_dir() == data_dir.resolve()
    assert paths.require_runtime_data_dir() == data_dir.resolve()


def test_legacy_pipeline_path_constants_follow_configured_data_root(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)

    with monkeypatch.context() as patch:
        patch.setenv("BGPKB_DATA_DIR", str(data_dir))
        reloaded = importlib.reload(paths)
        assert reloaded.DATA_DIR == data_dir.resolve()
        assert reloaded.RAW_DIR == data_dir.resolve() / "sources" / "raw"

    importlib.reload(paths)


def test_logical_relative_path_preserves_data_prefix_for_external_artifacts(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    source = data_dir / "sources" / "raw" / "rfc4271.txt"
    source.parent.mkdir(parents=True)
    source.write_text("BGP", encoding="utf-8")

    with monkeypatch.context() as patch:
        patch.setenv("BGPKB_DATA_DIR", str(data_dir))
        reloaded = importlib.reload(paths)
        assert reloaded.rel(source) == "data/sources/raw/rfc4271.txt"
        assert reloaded.rel(reloaded.CONFIG_DIR / "rag_retrieval.yaml") == "metadata/config/rag_retrieval.yaml"

    importlib.reload(paths)


def test_repository_docs_path_and_relative_label_follow_moved_root_docs():
    assert paths.DOCS_DIR == paths.REPOSITORY_ROOT / "docs"
    assert paths.rel(paths.DOCS_DIR / "architecture.md") == "docs/architecture.md"


def test_logical_data_path_resolves_under_external_artifact(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)

    with monkeypatch.context() as patch:
        patch.setenv("BGPKB_DATA_DIR", str(data_dir))
        reloaded = importlib.reload(paths)
        assert reloaded.resolve_logical_path("data/published/manifest.json") == (
            data_dir / "published" / "manifest.json"
        ).resolve()
        assert reloaded.resolve_logical_path("metadata/config/rag_retrieval.yaml") == (
            reloaded.PROJECT_ROOT / "metadata/config/rag_retrieval.yaml"
        )
        assert reloaded.resolve_logical_path("docs/architecture.md") == (
            reloaded.PROJECT_ROOT.parent / "docs/architecture.md"
        )

    importlib.reload(paths)


@pytest.mark.parametrize("unsafe", ["../outside", "/tmp/outside", "data/../../outside"])
def test_logical_path_rejects_escape(monkeypatch, tmp_path, unsafe):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)

    with monkeypatch.context() as patch:
        patch.setenv("BGPKB_DATA_DIR", str(data_dir))
        reloaded = importlib.reload(paths)
        with pytest.raises(ValueError, match="逻辑路径"):
            reloaded.resolve_logical_path(unsafe)

    importlib.reload(paths)


def test_report_policy_data_path_resolves_under_external_artifact(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)

    with monkeypatch.context() as patch:
        patch.setenv("BGPKB_DATA_DIR", str(data_dir))
        reloaded = importlib.reload(paths)
        assert reloaded.report_path("query_examples_report") == (
            data_dir / "reports/reference/query_examples_report.md"
        ).resolve()

    importlib.reload(paths)


def test_runtime_data_dir_rejects_missing_configured_directory(monkeypatch, tmp_path):
    missing_dir = tmp_path / "missing-release" / "data"
    monkeypatch.setenv("BGPKB_DATA_DIR", str(missing_dir))

    with pytest.raises(paths.RuntimeDataUnavailable, match=str(missing_dir)):
        paths.require_runtime_data_dir()


def test_database_path_uses_configured_runtime_data_directory(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    _write_serving_database(data_dir / "published")
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))

    assert database.runtime_database_path() == data_dir / "published" / "serving.sqlite"


def test_retrievers_use_configured_runtime_data_directory_by_default(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    published_dir = data_dir / "published"
    published_dir.mkdir(parents=True)
    _write_serving_database(published_dir)
    (published_dir / "bge_m3_vector_index.jsonl").touch()
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))

    assert Bm25Retriever().db_path == data_dir / "published" / "serving.sqlite"
    assert DenseRetriever(provider=object()).index_path == data_dir / "published" / "bge_m3_vector_index.jsonl"


def test_retrieval_framework_reads_published_data_from_runtime_directory(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    published_dir = data_dir / "published"
    published_dir.mkdir(parents=True)
    (published_dir / "semantic_id_map.jsonl").write_text(
        '{"resource_type":"chunk","local_id":"chunk-1","uri":"urn:bgpkb:chunk-1"}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))

    assert retrieval_framework.semantic_uri_map("chunk") == {"chunk-1": "urn:bgpkb:chunk-1"}


def test_hybrid_retrieval_reads_trust_metadata_from_runtime_directory(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    datasets_dir = data_dir / "derived" / "datasets"
    datasets_dir.mkdir(parents=True)
    (datasets_dir / "entity_source_evidence.jsonl").write_text(
        '{"entity_review_status":"approved","chunk_sample_ids":["chunk-1"]}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))

    assert hybrid_retrieval._trusted_chunk_ids() == {"chunk-1"}


def test_published_artifact_retrieval_data_loads_runtime_metadata(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    published_dir = data_dir / "published"
    datasets_dir = data_dir / "derived" / "datasets"
    published_dir.mkdir(parents=True)
    datasets_dir.mkdir(parents=True)
    _write_serving_database(
        published_dir,
        entities=[
            {"entity_id": "approved", "review_status": "approved"},
            {"entity_id": "pending", "review_status": "pending"},
        ],
    )
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))

    retrieval_data = PublishedArtifactRetrievalData.from_environment()

    assert retrieval_data.trusted_chunk_ids() == {_serving_document()["chunk_id"]}
    assert retrieval_data.eligible_doc_ids() == {"rfc4271"}
    assert retrieval_data.excluded_by_policy() == [
        {"entity_id": "pending", "reason": "not_approved", "review_status": "pending"}
    ]


def test_retrieval_data_owns_all_runtime_catalog_and_index_paths(tmp_path):
    data_dir = tmp_path / "release" / "data"
    published_dir = data_dir / "published"
    datasets_dir = data_dir / "derived" / "datasets"
    published_dir.mkdir(parents=True)
    datasets_dir.mkdir(parents=True)
    for path in (
        published_dir / "bge_m3_vector_index.jsonl",
        published_dir / "chunk_catalog.jsonl",
        datasets_dir / "section_catalog.jsonl",
    ):
        path.touch()
    _write_serving_database(published_dir)
    retrieval_data = PublishedArtifactRetrievalData(data_dir)

    assert retrieval_data.database_path() == published_dir / "serving.sqlite"
    assert retrieval_data.vector_index_path() == published_dir / "bge_m3_vector_index.jsonl"
    assert retrieval_data.chunk_catalog_path() == published_dir / "chunk_catalog.jsonl"
    assert retrieval_data.section_catalog_path() == datasets_dir / "section_catalog.jsonl"
    assert Bm25Retriever(retrieval_data=retrieval_data).db_path == retrieval_data.database_path()
    assert DenseRetriever(retrieval_data=retrieval_data, provider=object()).index_path == (
        retrieval_data.vector_index_path()
    )


def test_retrieval_data_fails_closed_when_serving_database_is_missing(tmp_path):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)
    retrieval_data = PublishedArtifactRetrievalData(data_dir)

    with pytest.raises(FileNotFoundError, match="serving.sqlite"):
        retrieval_data.trusted_chunk_ids()


def test_hybrid_search_with_injected_retrievers_does_not_require_runtime_artifact(monkeypatch):
    monkeypatch.delenv("BGPKB_DATA_DIR", raising=False)

    class FakeRetriever:
        def search(self, query, top_k):
            return RetrievalChannelResult("lexical", items=[])

    payload = hybrid_retrieval.search(
        "route leak",
        lexical_retriever=FakeRetriever(),
        dense_retriever=FakeRetriever(),
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
    )

    assert payload["results"] == []


def test_pytest_declares_artifact_marker():
    pyproject = tomllib.loads((paths.PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]

    assert any(marker.startswith("artifact:") for marker in markers)
