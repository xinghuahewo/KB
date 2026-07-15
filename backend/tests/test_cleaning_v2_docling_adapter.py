import importlib
import importlib.util
import json
from pathlib import Path


MODULE = "bgpkb.cleaning_v2.docling_adapter"
FIXTURES = Path(__file__).parent / "fixtures" / "docling"
SOURCE_META = {
    "doc_id": "fixture-doc",
    "source_path": "data/sources/raw/fixture.pdf",
    "source_sha256": "a" * 64,
}
RUNTIME_META = {
    "parser": "docling",
    "docling_version": "2.107.0",
    "image_digest": "sha256:" + "b" * 64,
    "model_manifest_sha256": "c" * 64,
}


def load_adapter():
    assert importlib.util.find_spec(MODULE) is not None, "Docling 适配器尚未实现"
    return importlib.import_module(MODULE)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_adapter_preserves_reading_order_hierarchy_bbox_and_special_blocks():
    adapter = load_adapter()

    document = adapter.adapt_docling_document(
        fixture("representative_document.json"), SOURCE_META, RUNTIME_META, {}
    )
    blocks = document["blocks"]

    assert document["schema_version"] == "canonical_document_v2"
    assert document["doc_id"] == "fixture-doc"
    assert [block["reading_order"] for block in blocks] == list(range(len(blocks)))
    assert [block["block_type"] for block in blocks[:6]] == [
        "title",
        "heading",
        "paragraph",
        "code",
        "formula",
        "picture",
    ]
    assert blocks[1]["heading_level"] == 2
    assert blocks[2]["parent_block_id"] == blocks[1]["block_id"]
    assert blocks[3]["raw_text"].startswith("router bgp")
    assert blocks[4]["raw_text"] == "P(invalid)=n_invalid/n_total"
    assert blocks[2]["bbox"] == {
        "left": 10.0,
        "top": 680.0,
        "right": 500.0,
        "bottom": 650.0,
        "coord_origin": "bottom_left",
    }
    assert blocks[5]["asset_refs"] == [document["assets"][0]["asset_id"]]
    assert document["assets"][0]["caption"] == "Figure 1: RPKI workflow"
    assert blocks[-1]["block_type"] == "unsupported"
    assert blocks[-1]["review_status"] == "quarantined"
    assert document["diagnostics"][0]["code"] == "unsupported_block_type"


def test_adapter_preserves_table_headers_spans_caption_and_source_page():
    adapter = load_adapter()

    document = adapter.adapt_docling_document(
        fixture("table_document.json"), SOURCE_META, RUNTIME_META, {}
    )
    table_block = document["blocks"][1]
    table = table_block["table"]

    assert table["rows"] == 3
    assert table["columns"] == 2
    assert table["source_pages"] == [2]
    assert table["caption"] == "Table 1: Route states"
    assert table["cells"][0]["column_header"] is True
    assert table["cells"][2]["row_span"] == 2
    assert table["cells"][2]["row_header"] is True


def test_adapter_is_stable_for_identical_inputs():
    adapter = load_adapter()
    payload = fixture("representative_document.json")

    first = adapter.adapt_docling_document(payload, SOURCE_META, RUNTIME_META, {})
    second = adapter.adapt_docling_document(payload, SOURCE_META, RUNTIME_META, {})

    assert first == second
    assert len({block["block_id"] for block in first["blocks"]}) == len(first["blocks"])


def test_adapter_recovers_unmounted_body_items_without_importing_furniture():
    adapter = load_adapter()
    payload = {
        "body": {
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/texts/2"},
            ]
        },
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "title",
                "content_layer": "body",
                "orig": "ASPA Overview",
                "text": "ASPA Overview",
            },
            {
                "self_ref": "#/texts/1",
                "label": "text",
                "content_layer": "body",
                "orig": "An ASPA authorizes provider ASNs.",
                "text": "An ASPA authorizes provider ASNs.",
            },
            {
                "self_ref": "#/texts/2",
                "label": "text",
                "content_layer": "furniture",
                "orig": "Skip to main content",
                "text": "Skip to main content",
            },
        ],
    }

    document = adapter.adapt_docling_document(
        payload, SOURCE_META, RUNTIME_META, {}
    )

    assert [block["cleaned_text"] for block in document["blocks"]] == [
        "ASPA Overview",
        "An ASPA authorizes provider ASNs.",
    ]
    assert document["diagnostics"] == [
        {
            "code": "unmounted_body_items_recovered",
            "count": 1,
            "source_anchors": ["#/texts/1"],
        }
    ]


def test_docling_success_never_calls_fallback():
    adapter = load_adapter()
    calls = {"docling": 0, "fallback": 0}

    def docling_parser(_source):
        calls["docling"] += 1
        return fixture("representative_document.json")

    def fallback_parser(_source, _doc_id):
        calls["fallback"] += 1
        raise AssertionError("Docling 成功时不得调用 fallback")

    result = adapter.parse_with_explicit_fallback(
        "fixture.pdf",
        SOURCE_META,
        RUNTIME_META,
        {"fallback": {"enabled": True, "requires_review": True}},
        docling_parser,
        fallback_parser,
        allow_fallback=True,
    )

    assert calls == {"docling": 1, "fallback": 0}
    assert result["parser_mode"] == "docling"
    assert result["fallback_reason"] is None


def test_docling_failure_requires_explicit_fallback_and_quarantines_otherwise():
    adapter = load_adapter()
    calls = {"fallback": 0}

    def fail_docling(_source):
        raise adapter.DoclingParseError("layout model failed")

    def fallback_parser(_source, _doc_id):
        calls["fallback"] += 1
        return {
            "doc_id": "fixture-doc",
            "title": "Fallback title",
            "sections": [{"section_id": "full", "heading": "Full", "content": "Fallback body"}],
        }, "Fallback body"

    blocked = adapter.parse_with_explicit_fallback(
        "fixture.pdf",
        SOURCE_META,
        RUNTIME_META,
        {"fallback": {"enabled": True, "requires_review": True}},
        fail_docling,
        fallback_parser,
        allow_fallback=False,
    )

    assert calls["fallback"] == 0
    assert blocked["parser_mode"] == "docling_failed"
    assert blocked["document_status"] == "quarantined"


def test_explicit_fallback_is_pending_and_excluded_from_publishable_blocks():
    adapter = load_adapter()

    def fail_docling(_source):
        raise adapter.DoclingParseError("layout model failed")

    def fallback_parser(_source, _doc_id):
        return {
            "doc_id": "fixture-doc",
            "title": "Fallback title",
            "sections": [{"section_id": "full", "heading": "Full", "content": "Fallback body"}],
        }, "Fallback body"

    result = adapter.parse_with_explicit_fallback(
        "fixture.pdf",
        SOURCE_META,
        RUNTIME_META,
        {"fallback": {"enabled": True, "requires_review": True}},
        fail_docling,
        fallback_parser,
        allow_fallback=True,
    )

    assert result["parser_mode"] == "fallback"
    assert result["fallback_reason"] == "layout model failed"
    assert result["fallback_review_status"] == "pending_review"
    assert all(block["review_status"] == "pending_review" for block in result["blocks"])
    assert adapter.publishable_blocks(result) == []
