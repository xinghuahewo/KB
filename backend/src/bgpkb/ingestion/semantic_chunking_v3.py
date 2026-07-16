"""从严格 Canonical Document v2 确定性派生 SemanticChunk v3。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import yaml

from bgpkb import paths
from bgpkb.ingestion.canonical_contract import require_production_canonical


DEFAULT_CONFIG_PATH = paths.CONFIG_DIR / "semantic_chunking_v3.yaml"
STRUCTURAL_BLOCK_TYPES = {"title", "heading"}
CONTENT_BLOCK_TYPES = {"paragraph", "list_item", "table", "code", "formula"}
HTML_NAVIGATION_TERMS = {
    "acknowledgements",
    "apis",
    "bgpreader",
    "components",
    "contact",
    "data encoding",
    "data providers",
    "documentation",
    "download",
    "home",
    "install",
    "news",
    "overview",
    "publications",
    "search",
    "toggle navigation",
    "tutorials",
}


@dataclass(frozen=True)
class ProfileConfig:
    profile: str
    chunker_name: str
    target_min_tokens: int
    target_max_tokens: int


@dataclass(frozen=True)
class SemanticChunkingConfig:
    config_version: str
    chunker_version: str
    config_fingerprint: str
    profiles: dict[str, ProfileConfig]
    minimum_chars: int
    short_allowlist: tuple[dict, ...]
    exact_normalization_version: str
    near_duplicate_mode: str
    max_same_source_exact_duplicate_rate: float


@dataclass(frozen=True)
class SemanticBuildResult:
    chunks: list[dict]
    excluded_blocks: list[dict]


@dataclass(frozen=True)
class SemanticDedupResult:
    chunks: list[dict]
    diagnostics: list[dict]


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value)).hexdigest()


def _normalized_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(" ".join(line.split()) for line in text.split("\n")).strip()


def _exact_normalized_text(value: object) -> str:
    return _normalized_text(value).casefold()


def load_semantic_chunking_config(path: str | Path = DEFAULT_CONFIG_PATH) -> SemanticChunkingConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != "semantic_chunking_config_v1":
        raise ValueError("Semantic chunking 配置必须使用 semantic_chunking_config_v1")
    profiles = {
        name: ProfileConfig(
            profile=name,
            chunker_name=str(payload["chunker_name"]),
            target_min_tokens=int(payload["target_min_tokens"]),
            target_max_tokens=int(payload["target_max_tokens"]),
        )
        for name, payload in raw.get("profiles", {}).items()
    }
    if not profiles:
        raise ValueError("Semantic chunking 配置至少需要一个 document_profile")
    short = raw.get("short_content", {})
    deduplication = raw.get("deduplication", {})
    quality_gates = raw.get("quality_gates", {})
    return SemanticChunkingConfig(
        config_version=str(raw["config_version"]),
        chunker_version=str(raw["chunker_version"]),
        config_fingerprint=_sha256(raw),
        profiles=profiles,
        minimum_chars=int(short.get("minimum_chars", 20)),
        short_allowlist=tuple(short.get("allowlist", [])),
        exact_normalization_version=str(
            deduplication.get("exact_normalization_version", "exact-normalization-v1")
        ),
        near_duplicate_mode=str(deduplication.get("near_duplicate_mode", "diagnostic_only")),
        max_same_source_exact_duplicate_rate=float(
            quality_gates.get("max_same_source_exact_duplicate_rate", 0.02)
        ),
    )


def resolve_profile(profile: str, config: SemanticChunkingConfig) -> ProfileConfig:
    try:
        return config.profiles[profile]
    except KeyError as exc:
        supported = ", ".join(sorted(config.profiles))
        raise ValueError(f"不支持的 document_profile：{profile}；可用值：{supported}") from exc


def build_semantic_chunk_id(
    *,
    source_snapshot_id: str,
    section_path: list[str],
    source_block_hashes: list[str],
    chunker_version: str,
    config_fingerprint: str,
    content_hash: str,
) -> str:
    identity = {
        "source_snapshot_id": source_snapshot_id,
        "section_path": [_normalized_text(item) for item in section_path],
        "source_block_hashes": list(source_block_hashes),
        "chunker_version": chunker_version,
        "config_fingerprint": config_fingerprint,
        "content_hash": content_hash,
    }
    return "semantic_chunk_v3_" + hashlib.sha256(_canonical_json(identity)).hexdigest()


def _block_hash(block: dict) -> str:
    return _sha256({
        "block_id": block.get("block_id"),
        "block_type": block.get("block_type"),
        "cleaned_text": _normalized_text(block.get("cleaned_text")),
        "table": block.get("table"),
        "page_number": block.get("page_number"),
        "source_anchor": block.get("provenance", {}).get("source_anchor"),
    })


def _document_title(document: dict) -> str:
    for block in document["blocks"]:
        if block.get("block_type") == "title" and _normalized_text(block.get("cleaned_text")):
            return _normalized_text(block["cleaned_text"])
    for block in document["blocks"]:
        if block.get("block_type") == "heading" and _normalized_text(block.get("cleaned_text")):
            return _normalized_text(block["cleaned_text"])
    return str(document["doc_id"])


def _source_ref(document: dict, block: dict) -> str:
    locator = str(document["source"]["origin_locator"])
    anchor = str(block.get("provenance", {}).get("source_anchor") or "")
    return locator + (anchor if anchor.startswith("#") else "#" + anchor)


def _estimated_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _inferred_rfc_heading_level(text: str) -> int | None:
    normalized = _normalized_text(text)
    if not normalized or len(normalized) > 160:
        return None
    numbered = re.match(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s+\S", normalized)
    if numbered:
        return len(numbered.group(1).split("."))
    appendix = re.match(r"^Appendix\s+[A-Z](?:\.\d+)*\.?\s+\S", normalized, re.IGNORECASE)
    if appendix:
        return max(1, normalized.split()[1].count(".") + 1)
    if re.match(
        r"^(Acknowledg(?:e)?ments|References|Security Considerations|IANA Considerations)$",
        normalized,
        re.IGNORECASE,
    ):
        return 1
    return None


def _make_chunk(
    document: dict,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
    section_path: list[str],
    blocks: list[dict],
    content: str,
    semantic_unit: str,
) -> dict:
    normalized_content = _normalized_text(content)
    block_hashes = [_block_hash(block) for block in blocks]
    content_hash = _sha256(normalized_content)
    source = document["source"]
    page_numbers = sorted({block["page_number"] for block in blocks if block.get("page_number")})
    source_refs = list(dict.fromkeys(_source_ref(document, block) for block in blocks))
    languages = [str(block.get("language") or "und") for block in blocks]
    language = languages[0] if len(set(languages)) == 1 else "mul"
    return {
        "schema_version": "semantic_chunk_v3",
        "chunk_id": build_semantic_chunk_id(
            source_snapshot_id=source["snapshot_id"],
            section_path=section_path,
            source_block_hashes=block_hashes,
            chunker_version=config.chunker_version,
            config_fingerprint=config.config_fingerprint,
            content_hash=content_hash,
        ),
        "doc_id": document["doc_id"],
        "source_id": source["source_id"],
        "source_snapshot_id": source["snapshot_id"],
        "source_object_digest": source["object_digest"],
        "document_profile": profile.profile,
        "chunker": {
            "name": profile.chunker_name,
            "version": config.chunker_version,
            "config_version": config.config_version,
            "config_fingerprint": config.config_fingerprint,
        },
        "title": _document_title(document),
        "section_path": list(section_path),
        "semantic_unit": semantic_unit,
        "content": normalized_content,
        "content_hash": content_hash,
        "exact_content_hash": _sha256(_exact_normalized_text(normalized_content)),
        "source_block_ids": [block["block_id"] for block in blocks],
        "source_block_hashes": block_hashes,
        "source_refs": source_refs,
        "page_numbers": page_numbers,
        "language": language,
        "estimated_tokens": _estimated_tokens(normalized_content),
        "short_content_rule_id": None,
    }


def _split_text_to_token_limit(text: str, maximum_tokens: int) -> list[str]:
    maximum_chars = maximum_tokens * 4
    if maximum_chars < 1:
        raise ValueError("target_max_tokens 必须大于零")
    words = _normalized_text(text).split()
    parts: list[str] = []
    current: list[str] = []
    current_chars = 0
    for word in words:
        if len(word) > maximum_chars:
            if current:
                parts.append(" ".join(current))
                current = []
                current_chars = 0
            parts.extend(word[index:index + maximum_chars] for index in range(0, len(word), maximum_chars))
            continue
        added_chars = len(word) + (1 if current else 0)
        if current and current_chars + added_chars > maximum_chars:
            parts.append(" ".join(current))
            current = [word]
            current_chars = len(word)
        else:
            current.append(word)
            current_chars += added_chars
    if current:
        parts.append(" ".join(current))
    return parts


def _rfc_chunks(
    document: dict,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
) -> SemanticBuildResult:
    chunks: list[dict] = []
    excluded: list[dict] = []
    section_path: list[str] = []
    section_stack: list[tuple[int, str]] = []
    pending: list[dict] = []

    def set_section(level: int, text: str) -> None:
        nonlocal section_path
        while section_stack and section_stack[-1][0] >= level:
            section_stack.pop()
        section_stack.append((level, text))
        section_path = [value for _, value in section_stack]

    def flush_pending() -> None:
        nonlocal pending
        if not pending:
            return
        content = "\n\n".join(_normalized_text(block.get("cleaned_text")) for block in pending)
        chunks.append(_make_chunk(
            document,
            profile=profile,
            config=config,
            section_path=section_path,
            blocks=pending,
            content=content,
            semantic_unit="paragraph" if all(block["block_type"] == "paragraph" for block in pending) else "list",
        ))
        pending = []

    for block in sorted(document["blocks"], key=lambda row: row["reading_order"]):
        block_type = block["block_type"]
        text = _normalized_text(block.get("cleaned_text"))
        if block_type in STRUCTURAL_BLOCK_TYPES:
            flush_pending()
            if text:
                level = int(block.get("heading_level") or 1)
                set_section(level, text)
            continue
        inferred_level = (
            _inferred_rfc_heading_level(text)
            if block_type in {"paragraph", "code"}
            else None
        )
        if inferred_level is not None:
            flush_pending()
            set_section(inferred_level, text)
            pending.append(block)
            continue
        if block_type not in CONTENT_BLOCK_TYPES or not text:
            flush_pending()
            excluded.append({
                "block_id": block["block_id"],
                "reason": "empty_content" if not text else "non_semantic_block_type",
                "document_profile": profile.profile,
                "section_path": list(section_path),
                "content": text,
            })
            continue
        if block_type not in {"paragraph", "list_item"}:
            flush_pending()
            chunks.append(_make_chunk(
                document,
                profile=profile,
                config=config,
                section_path=section_path,
                blocks=[block],
                content=text,
                semantic_unit="list" if block_type == "list_item" else block_type,
            ))
            continue
        if _estimated_tokens(text) > profile.target_max_tokens:
            flush_pending()
            for part in _split_text_to_token_limit(text, profile.target_max_tokens):
                chunks.append(_make_chunk(
                    document,
                    profile=profile,
                    config=config,
                    section_path=section_path,
                    blocks=[block],
                    content=part,
                    semantic_unit="paragraph" if block_type == "paragraph" else "list",
                ))
            continue
        combined = "\n\n".join([
            *(_normalized_text(item.get("cleaned_text")) for item in pending),
            text,
        ])
        if pending and _estimated_tokens(combined) > profile.target_max_tokens:
            flush_pending()
        pending.append(block)
    flush_pending()
    return SemanticBuildResult(chunks=chunks, excluded_blocks=excluded)


def _html_template_exclusions(document: dict) -> dict[str, str]:
    exclusions: dict[str, str] = {}
    blocks = sorted(document["blocks"], key=lambda row: row["reading_order"])
    for block in blocks:
        if block["block_type"] == "page_header":
            exclusions[block["block_id"]] = "html_template_navigation"
        elif block["block_type"] == "page_footer":
            exclusions[block["block_id"]] = "html_template_footer"

    titles = [
        block
        for block in blocks
        if block["block_type"] == "title" and _normalized_text(block.get("cleaned_text"))
    ]
    if len(titles) > 1:
        document_title = _normalized_text(titles[0]["cleaned_text"]).casefold()
        main_title = next(
            (
                block
                for block in titles[1:]
                if (
                    _normalized_text(block["cleaned_text"]).casefold() in document_title
                    or document_title in _normalized_text(block["cleaned_text"]).casefold()
                )
            ),
            None,
        )
        if main_title is not None:
            boundary = int(main_title["reading_order"])
            for block in blocks:
                if (
                    int(block["reading_order"]) < boundary
                    and block["block_type"] not in STRUCTURAL_BLOCK_TYPES
                ):
                    exclusions[block["block_id"]] = "html_template_navigation"

    def inspect_run(run: list[dict]) -> None:
        if len(run) < 4:
            return
        values = [_normalized_text(block.get("cleaned_text")).casefold() for block in run]
        navigation_hits = sum(value in HTML_NAVIGATION_TERMS for value in values)
        duplicate_count = len(values) - len(set(values))
        if navigation_hits / len(run) < 0.5 and not (
            "toggle navigation" in values and navigation_hits >= 3
        ) and duplicate_count / len(run) < 0.4:
            return
        for block in run:
            exclusions[block["block_id"]] = "html_template_navigation"

    run: list[dict] = []
    for block in blocks:
        text = _normalized_text(block.get("cleaned_text"))
        is_short_navigation_candidate = (
            block["block_type"] in {"paragraph", "list_item"}
            and 0 < len(text) <= 80
        )
        if is_short_navigation_candidate:
            run.append(block)
            continue
        inspect_run(run)
        run = []
    inspect_run(run)
    return exclusions


def _html_chunks(
    document: dict,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
) -> SemanticBuildResult:
    template_exclusions = _html_template_exclusions(document)
    filtered = dict(document)
    filtered["blocks"] = [
        block for block in document["blocks"] if block["block_id"] not in template_exclusions
    ]
    result = _rfc_chunks(filtered, profile=profile, config=config)
    excluded = list(result.excluded_blocks)
    blocks_by_id = {block["block_id"]: block for block in document["blocks"]}
    for block_id, reason in sorted(template_exclusions.items()):
        block = blocks_by_id[block_id]
        excluded.append({
            "block_id": block_id,
            "reason": reason,
            "document_profile": profile.profile,
            "section_path": [],
            "content": _normalized_text(block.get("cleaned_text")),
        })
    return SemanticBuildResult(chunks=result.chunks, excluded_blocks=excluded)


def _table_grid(table: dict) -> list[list[str]]:
    rows = int(table.get("rows", 0))
    columns = int(table.get("columns", 0))
    if rows < 1 or columns < 1:
        return []
    grid = [["" for _ in range(columns)] for _ in range(rows)]
    for cell in table.get("cells", []):
        row = int(cell.get("row", 0))
        column = int(cell.get("column", 0))
        if 0 <= row < rows and 0 <= column < columns:
            grid[row][column] = _normalized_text(cell.get("text")).replace("|", "\\|")
    return grid


def _render_table_group(caption: str, header: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]
    table_text = "\n".join(lines)
    return f"{caption}\n\n{table_text}" if caption else table_text


def _split_table_groups(table: dict, caption: str, maximum_tokens: int) -> list[str]:
    grid = _table_grid(table)
    if not grid:
        return []
    header, *data_rows = grid
    if not data_rows:
        return [_render_table_group(caption, header, [])]
    groups: list[str] = []
    current: list[list[str]] = []
    for row in data_rows:
        candidate = _render_table_group(caption, header, [*current, row])
        if current and _estimated_tokens(candidate) > maximum_tokens:
            groups.append(_render_table_group(caption, header, current))
            current = [row]
        else:
            current.append(row)
    if current:
        groups.append(_render_table_group(caption, header, current))
    return groups


def _pdf_chunks(
    document: dict,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
) -> SemanticBuildResult:
    blocks = sorted(document["blocks"], key=lambda row: row["reading_order"])
    non_table_document = dict(document)
    non_table_document["blocks"] = [block for block in blocks if block["block_type"] != "table"]
    base = _rfc_chunks(non_table_document, profile=profile, config=config)
    chunks = list(base.chunks)
    excluded = list(base.excluded_blocks)
    blocks_by_id = {block["block_id"]: block for block in blocks}
    section_path: list[str] = []
    for block in blocks:
        text = _normalized_text(block.get("cleaned_text"))
        if block["block_type"] in STRUCTURAL_BLOCK_TYPES:
            if text:
                level = int(block.get("heading_level") or 1)
                section_path = [*section_path[: level - 1], text]
            continue
        if block["block_type"] != "table":
            continue
        table = block.get("table") or {}
        caption = _normalized_text(table.get("caption"))
        caption_block = blocks_by_id.get(block.get("parent_block_id"))
        source_blocks = [block]
        if caption_block and caption_block.get("block_type") in STRUCTURAL_BLOCK_TYPES | {"caption"}:
            caption = _normalized_text(caption_block.get("cleaned_text")) or caption
            source_blocks = [caption_block, block]
        groups = _split_table_groups(table, caption, profile.target_max_tokens)
        if not groups and text:
            groups = [f"{caption}\n\n{text}" if caption else text]
        if not groups:
            excluded.append({
                "block_id": block["block_id"],
                "reason": "empty_table",
                "document_profile": profile.profile,
                "section_path": list(section_path),
                "content": "",
            })
            continue
        for content in groups:
            chunks.append(_make_chunk(
                document,
                profile=profile,
                config=config,
                section_path=section_path,
                blocks=source_blocks,
                content=content,
                semantic_unit="table",
            ))
    return SemanticBuildResult(chunks=chunks, excluded_blocks=excluded)


HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _yaml_text(value: object) -> str:
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=1_000_000).strip()


def _operation_header(method: str, path: str, operation: dict) -> str:
    lines = [f"{method.upper()} {path}"]
    operation_id = _normalized_text(operation.get("operationId"))
    if operation_id:
        lines.append(f"operationId: {operation_id}")
    return "\n".join(lines)


def _operation_content(method: str, path: str, operation: dict, payload: dict) -> str:
    header = _operation_header(method, path, operation)
    body = _yaml_text(payload)
    return f"{header}\n{body}" if body else header


def _response_family(status: object) -> str:
    value = str(status)
    return value[0] + "xx" if value and value[0] in "2345" else "default"


def _bounded_list_payloads(
    *,
    method: str,
    path: str,
    operation: dict,
    key: str,
    items: list[dict],
    maximum_tokens: int,
) -> list[dict]:
    groups: list[dict] = []
    current: list[dict] = []
    for item in items:
        candidate = {key: [*current, item]}
        if current and _estimated_tokens(_operation_content(method, path, operation, candidate)) > maximum_tokens:
            groups.append({key: current})
            current = [item]
        else:
            current.append(item)
    if current:
        groups.append({key: current})
    return groups


def _bounded_mapping_payloads(
    *,
    method: str,
    path: str,
    operation: dict,
    key: str,
    items: dict,
    maximum_tokens: int,
) -> list[dict]:
    groups: list[dict] = []
    current: dict = {}
    for name, value in items.items():
        candidate = {key: {**current, name: value}}
        if current and _estimated_tokens(_operation_content(method, path, operation, candidate)) > maximum_tokens:
            groups.append({key: current})
            current = {name: value}
        else:
            current[name] = value
    if current:
        groups.append({key: current})
    return groups


def _flatten_schema_properties(
    schema: dict,
    *,
    prefix: tuple[str, ...] = (),
) -> list[dict]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    required = {str(name) for name in schema.get("required", [])}
    entries: list[dict] = []
    for name, definition in properties.items():
        property_name = str(name)
        path = (*prefix, property_name)
        if isinstance(definition, dict) and isinstance(definition.get("properties"), dict):
            entries.extend(_flatten_schema_properties(definition, prefix=path))
            continue
        items = definition.get("items") if isinstance(definition, dict) else None
        if isinstance(items, dict) and isinstance(items.get("properties"), dict):
            entries.extend(_flatten_schema_properties(items, prefix=(*prefix, property_name + "[]")))
            continue
        entries.append({
            "property_path": ".".join(path),
            "required": property_name in required,
            "definition": definition,
        })
    return entries


def _request_body_payloads(
    method: str,
    path: str,
    operation: dict,
    request_body: dict,
    maximum_tokens: int,
) -> list[dict]:
    content = request_body.get("content") if isinstance(request_body, dict) else None
    if not isinstance(content, dict):
        payload = {"requestBody": request_body}
        if _estimated_tokens(_operation_content(method, path, operation, payload)) > maximum_tokens:
            raise ValueError(f"{method.upper()} {path} requestBody 无可分区 properties 且超过 token 上限")
        return [payload]
    payloads: list[dict] = []
    for media_type, media in content.items():
        schema = media.get("schema") if isinstance(media, dict) else None
        entries = _flatten_schema_properties(schema) if isinstance(schema, dict) else []
        if not entries:
            payload = {
                "requestBody": {
                    "required": bool(request_body.get("required", False)),
                    "content_type": str(media_type),
                    "schema": schema,
                }
            }
            if _estimated_tokens(_operation_content(method, path, operation, payload)) > maximum_tokens:
                raise ValueError(f"{method.upper()} {path} requestBody schema 无可分区 properties 且超过 token 上限")
            payloads.append(payload)
            continue
        current: list[dict] = []
        for entry in entries:
            candidate = {
                "requestBody": {
                    "required": bool(request_body.get("required", False)),
                    "content_type": str(media_type),
                    "schema_type": schema.get("type"),
                    "property_definitions": [*current, entry],
                }
            }
            if current and _estimated_tokens(_operation_content(method, path, operation, candidate)) > maximum_tokens:
                payloads.append({
                    "requestBody": {
                        "required": bool(request_body.get("required", False)),
                        "content_type": str(media_type),
                        "schema_type": schema.get("type"),
                        "property_definitions": current,
                    }
                })
                current = [entry]
            else:
                current.append(entry)
        if current:
            payloads.append({
                "requestBody": {
                    "required": bool(request_body.get("required", False)),
                    "content_type": str(media_type),
                    "schema_type": schema.get("type"),
                    "property_definitions": current,
                }
            })
    for payload in payloads:
        if _estimated_tokens(_operation_content(method, path, operation, payload)) > maximum_tokens:
            property_path = payload["requestBody"].get("property_definitions", [{}])[0].get("property_path")
            raise ValueError(
                f"{method.upper()} {path} requestBody property {property_path} 超过 token 上限"
            )
    return payloads


def _overview_payloads(
    method: str,
    path: str,
    operation: dict,
    maximum_tokens: int,
) -> list[dict]:
    fixed_keys = ("summary", "security", "deprecated", "tags")
    fixed = {key: operation[key] for key in fixed_keys if key in operation}
    description = str(operation.get("description") or "").replace("\r\n", "\n").replace("\r", "\n")
    if not description.strip():
        return [fixed] if fixed else []
    segments = [segment.strip() for segment in re.split(r"\n\s*\n", description) if segment.strip()]
    overhead = _estimated_tokens(_operation_content(method, path, operation, fixed)) + 12
    available_tokens = max(1, maximum_tokens - overhead)
    bounded_segments: list[str] = []
    for segment in segments:
        if _estimated_tokens(segment) <= available_tokens:
            bounded_segments.append(segment)
        else:
            bounded_segments.extend(_split_text_to_token_limit(segment, available_tokens))

    payloads: list[dict] = []
    current: list[str] = []
    for segment in bounded_segments:
        candidate = {**fixed, "description_segments": [*current, segment]}
        if current and _estimated_tokens(_operation_content(method, path, operation, candidate)) > maximum_tokens:
            payloads.append({**fixed, "description_segments": current})
            current = [segment]
        else:
            current.append(segment)
    if current:
        payloads.append({**fixed, "description_segments": current})
    if any(
        _estimated_tokens(_operation_content(method, path, operation, payload)) > maximum_tokens
        for payload in payloads
    ):
        raise ValueError(f"{method.upper()} {path} overview 单一描述片段超过 token 上限")
    return payloads


def _operation_partitions(method: str, path: str, operation: dict, maximum_tokens: int) -> list[tuple[str, str]]:
    full_content = _operation_content(method, path, operation, operation)
    if _estimated_tokens(full_content) <= maximum_tokens:
        return [("operation", full_content)]

    partitions: list[tuple[str, str]] = []
    partitions.extend(
        ("overview", _operation_content(method, path, operation, overview))
        for overview in _overview_payloads(method, path, operation, maximum_tokens)
    )

    parameters = operation.get("parameters") or []
    by_location: dict[str, list[dict]] = {}
    for parameter in parameters:
        if isinstance(parameter, dict):
            by_location.setdefault(str(parameter.get("in") or "unknown"), []).append(parameter)
    for location, items in by_location.items():
        payloads = _bounded_list_payloads(
            method=method,
            path=path,
            operation=operation,
            key="parameters",
            items=items,
            maximum_tokens=maximum_tokens,
        )
        partitions.extend(
            (f"parameters:{location}", _operation_content(method, path, operation, payload))
            for payload in payloads
        )
    if "requestBody" in operation:
        partitions.extend(
            ("parameters:body", _operation_content(method, path, operation, payload))
            for payload in _request_body_payloads(
                method,
                path,
                operation,
                operation["requestBody"],
                maximum_tokens,
            )
        )

    responses = operation.get("responses") or {}
    by_family: dict[str, dict] = {}
    if isinstance(responses, dict):
        for status, response in responses.items():
            by_family.setdefault(_response_family(status), {})[status] = response
    for family, items in by_family.items():
        payloads = _bounded_mapping_payloads(
            method=method,
            path=path,
            operation=operation,
            key="responses",
            items=items,
            maximum_tokens=maximum_tokens,
        )
        partitions.extend(
            (f"responses:{family}", _operation_content(method, path, operation, payload))
            for payload in payloads
        )
    result = partitions or [("operation", full_content)]
    oversized = [partition for partition, content in result if _estimated_tokens(content) > maximum_tokens]
    if oversized:
        raise ValueError(
            f"{method.upper()} {path} OpenAPI 分区仍超过 token 上限：{', '.join(oversized)}"
        )
    return result


def _schema_contents(name: str, schema: dict, maximum_tokens: int) -> list[str]:
    prefix = f"Schema {name}"
    full = f"{prefix}\n{_yaml_text(schema)}"
    if _estimated_tokens(full) <= maximum_tokens or not isinstance(schema.get("properties"), dict):
        return [full]
    common = {key: value for key, value in schema.items() if key not in {"properties", "required"}}
    entries = _flatten_schema_properties(schema)
    groups: list[str] = []
    current: list[dict] = []
    for entry in entries:
        candidate = {**common, "property_definitions": [*current, entry]}
        content = f"{prefix}\n{_yaml_text(candidate)}"
        if current and _estimated_tokens(content) > maximum_tokens:
            groups.append(f"{prefix}\n{_yaml_text({**common, 'property_definitions': current})}")
            current = [entry]
        else:
            current.append(entry)
    if current:
        groups.append(f"{prefix}\n{_yaml_text({**common, 'property_definitions': current})}")
    if any(_estimated_tokens(content) > maximum_tokens for content in groups):
        raise ValueError(f"OpenAPI schema {name} 的单一 property 超过 token 上限")
    return groups


def _openapi_chunks(
    document: dict,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
) -> SemanticBuildResult:
    source_blocks = [
        block
        for block in sorted(document["blocks"], key=lambda row: row["reading_order"])
        if block["block_type"] in CONTENT_BLOCK_TYPES and _normalized_text(block.get("cleaned_text"))
    ]
    raw = "\n".join(
        str(block.get("cleaned_text") or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        for block in source_blocks
    )
    try:
        payload = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"OpenAPI/YAML 解析失败：{exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("paths"), dict):
        raise ValueError("OpenAPI/YAML 文档缺少 paths 对象")

    chunks: list[dict] = []
    for path, path_item in payload["paths"].items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_name = f"{method.upper()} {path}"
            for partition, content in _operation_partitions(
                method, str(path), operation, profile.target_max_tokens
            ):
                section_path = [operation_name] if partition == "operation" else [operation_name, partition]
                chunks.append(_make_chunk(
                    document,
                    profile=profile,
                    config=config,
                    section_path=section_path,
                    blocks=source_blocks,
                    content=content,
                    semantic_unit="operation",
                ))

    components = payload.get("components") or {}
    schemas = components.get("schemas") or {}
    if isinstance(schemas, dict):
        for name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            for content in _schema_contents(str(name), schema, profile.target_max_tokens):
                chunks.append(_make_chunk(
                    document,
                    profile=profile,
                    config=config,
                    section_path=["components", "schemas", str(name)],
                    blocks=source_blocks,
                    content=content,
                    semantic_unit="schema",
                ))
    security_schemes = components.get("securitySchemes") or {}
    if isinstance(security_schemes, dict):
        for name, definition in security_schemes.items():
            chunks.append(_make_chunk(
                document,
                profile=profile,
                config=config,
                section_path=["components", "securitySchemes", str(name)],
                blocks=source_blocks,
                content=f"Security scheme {name}\n{_yaml_text(definition)}",
                semantic_unit="security",
            ))
    error_responses = components.get("responses") or {}
    if isinstance(error_responses, dict):
        for name, definition in error_responses.items():
            chunks.append(_make_chunk(
                document,
                profile=profile,
                config=config,
                section_path=["components", "responses", str(name)],
                blocks=source_blocks,
                content=f"Response object {name}\n{_yaml_text(definition)}",
                semantic_unit="error",
            ))
    return SemanticBuildResult(chunks=chunks, excluded_blocks=[])


def _short_allowlist_rule(content: str, profile: str, config: SemanticChunkingConfig) -> str | None:
    normalized = _normalized_text(content)
    for rule in config.short_allowlist:
        if not isinstance(rule, dict):
            continue
        profiles = rule.get("profiles")
        if profiles and profile not in profiles:
            continue
        if _normalized_text(rule.get("exact")) == normalized and rule.get("rule_id"):
            return str(rule["rule_id"])
    return None


def _apply_short_content_policy(
    result: SemanticBuildResult,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
) -> SemanticBuildResult:
    chunks: list[dict] = []
    excluded = list(result.excluded_blocks)
    for chunk in result.chunks:
        content = _normalized_text(chunk["content"])
        if len(content) >= config.minimum_chars:
            chunks.append(chunk)
            continue
        rule_id = _short_allowlist_rule(content, profile.profile, config)
        if rule_id:
            allowed = dict(chunk)
            allowed["semantic_unit"] = "term"
            allowed["short_content_rule_id"] = rule_id
            chunks.append(allowed)
            continue
        excluded.extend({
            "block_id": block_id,
            "reason": "short_unmeaningful_content",
            "document_profile": profile.profile,
            "section_path": list(chunk["section_path"]),
            "content": content,
        } for block_id in chunk["source_block_ids"])
    return SemanticBuildResult(chunks=chunks, excluded_blocks=excluded)


def _dedup_key(chunk: dict) -> tuple:
    return (
        chunk["source_id"],
        chunk["source_snapshot_id"],
        tuple(_normalized_text(item) for item in chunk["section_path"]),
        chunk["document_profile"],
        chunk["semantic_unit"],
        chunk["exact_content_hash"],
    )


def _unique(values: list) -> list:
    return list(dict.fromkeys(values))


def _merge_exact_group(group: list[dict]) -> dict:
    canonical = dict(group[0])
    canonical["source_block_ids"] = _unique([
        block_id for chunk in group for block_id in chunk["source_block_ids"]
    ])
    canonical["source_block_hashes"] = _unique([
        block_hash for chunk in group for block_hash in chunk["source_block_hashes"]
    ])
    canonical["source_refs"] = _unique([
        source_ref for chunk in group for source_ref in chunk["source_refs"]
    ])
    canonical["page_numbers"] = sorted({
        page_number for chunk in group for page_number in chunk["page_numbers"]
    })
    canonical["chunk_id"] = build_semantic_chunk_id(
        source_snapshot_id=canonical["source_snapshot_id"],
        section_path=canonical["section_path"],
        source_block_hashes=canonical["source_block_hashes"],
        chunker_version=canonical["chunker"]["version"],
        config_fingerprint=canonical["chunker"]["config_fingerprint"],
        content_hash=canonical["content_hash"],
    )
    return canonical


def _near_shingles(text: str, size: int = 3) -> set[str]:
    tokens = re.findall(r"[\w]+", _exact_normalized_text(text), flags=re.UNICODE)
    tokens = ["<number>" if token.isdigit() else token for token in tokens]
    if len(tokens) < size:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def _near_similarity(left: str, right: str) -> float:
    left_shingles = _near_shingles(left)
    right_shingles = _near_shingles(right)
    union = left_shingles | right_shingles
    return len(left_shingles & right_shingles) / len(union) if union else 1.0


def deduplicate_semantic_chunks(
    chunks: list[dict],
    *,
    config: SemanticChunkingConfig | None = None,
) -> SemanticDedupResult:
    """折叠同来源同语义上下文 exact 重复；近重复只记录诊断。"""

    active_config = config or load_semantic_chunking_config()
    if active_config.near_duplicate_mode != "diagnostic_only":
        raise ValueError("近重复自动折叠尚未获得 ADR 批准；只允许 diagnostic_only")
    grouped: dict[tuple, list[dict]] = {}
    for chunk in chunks:
        grouped.setdefault(_dedup_key(chunk), []).append(chunk)

    deduplicated: list[dict] = []
    diagnostics: list[dict] = []
    for group in grouped.values():
        canonical = _merge_exact_group(group) if len(group) > 1 else dict(group[0])
        deduplicated.append(canonical)
        if len(group) > 1:
            diagnostics.append({
                "code": "same_source_exact_deduplicated",
                "canonical_chunk_id": canonical["chunk_id"],
                "input_chunk_ids": [chunk["chunk_id"] for chunk in group],
                "source_id": canonical["source_id"],
                "source_snapshot_id": canonical["source_snapshot_id"],
                "merged_source_block_ids": list(canonical["source_block_ids"]),
            })

    chunks_by_source: dict[tuple[str, str], list[dict]] = {}
    for chunk in deduplicated:
        chunks_by_source.setdefault(
            (chunk["source_id"], chunk["source_snapshot_id"]), []
        ).append(chunk)
    shingles = {chunk["chunk_id"]: _near_shingles(chunk["content"]) for chunk in deduplicated}
    for source_chunks in chunks_by_source.values():
        for left_index, left in enumerate(source_chunks):
            for right in source_chunks[left_index + 1:]:
                if left["exact_content_hash"] == right["exact_content_hash"]:
                    continue
                left_shingles = shingles[left["chunk_id"]]
                right_shingles = shingles[right["chunk_id"]]
                union = left_shingles | right_shingles
                score = len(left_shingles & right_shingles) / len(union) if union else 1.0
                if score < 0.8:
                    continue
                diagnostics.append({
                    "code": "near_duplicate_diagnostic",
                    "left_chunk_id": left["chunk_id"],
                    "right_chunk_id": right["chunk_id"],
                    "left_source_id": left["source_id"],
                    "right_source_id": right["source_id"],
                    "same_source": True,
                    "algorithm": "token_3_shingles_mask_numbers_v1",
                    "score": round(score, 6),
                    "auto_collapsed": False,
                })
    return SemanticDedupResult(chunks=deduplicated, diagnostics=diagnostics)


def _migration_blocks(chunk: dict) -> set[str]:
    return {str(block_id) for block_id in chunk.get("source_block_ids", []) if block_id}


def _migration_text(chunk: dict) -> str:
    return " ".join(_normalized_text(chunk.get("content")).casefold().split())


def _migration_record(relation: str, old_group: list[dict], new_group: list[dict]) -> dict:
    source_blocks = sorted({
        block_id
        for chunk in [*old_group, *new_group]
        for block_id in _migration_blocks(chunk)
    })
    return {
        "schema_version": "chunk_id_migration_v1",
        "relation": relation,
        "old_chunk_ids": [str(chunk["chunk_id"]) for chunk in old_group],
        "new_chunk_ids": [str(chunk["chunk_id"]) for chunk in new_group],
        "proof": {
            "method": (
                "source_block_and_normalized_content_v1"
                if relation in {"equivalent", "merged", "split"}
                else "source_block_overlap_v1" if relation == "replaced" else "no_source_block_overlap_v1"
            ),
            "source_block_ids": source_blocks,
        },
    }


def _migration_relation(old_group: list[dict], new_group: list[dict]) -> str:
    if len(old_group) == 1 and len(new_group) == 1:
        old, new = old_group[0], new_group[0]
        if _migration_blocks(old) == _migration_blocks(new) and _migration_text(old) == _migration_text(new):
            return "equivalent"
        return "replaced"
    if len(old_group) > 1 and len(new_group) == 1:
        merged_blocks = set().union(*(_migration_blocks(chunk) for chunk in old_group))
        merged_text = _migration_text(new_group[0])
        if merged_blocks == _migration_blocks(new_group[0]) and all(
            _migration_text(chunk) in merged_text for chunk in old_group
        ):
            return "merged"
        return "replaced"
    if len(old_group) == 1 and len(new_group) > 1:
        split_blocks = set().union(*(_migration_blocks(chunk) for chunk in new_group))
        split_text = " ".join(_migration_text(chunk) for chunk in new_group)
        if split_blocks == _migration_blocks(old_group[0]) and split_text == _migration_text(old_group[0]):
            return "split"
        return "replaced"
    return "replaced"


def build_chunk_id_migration(old_chunks: list[dict], new_chunks: list[dict]) -> list[dict]:
    """按 source block 闭包构建可审计旧新 chunk 关系。"""

    old_ids = [str(chunk.get("chunk_id") or "") for chunk in old_chunks]
    new_ids = [str(chunk.get("chunk_id") or "") for chunk in new_chunks]
    if not all(old_ids) or len(old_ids) != len(set(old_ids)):
        raise ValueError("旧 chunk_id 必须非空且唯一")
    if not all(new_ids) or len(new_ids) != len(set(new_ids)):
        raise ValueError("新 chunk_id 必须非空且唯一")

    old_to_new: dict[int, set[int]] = {index: set() for index in range(len(old_chunks))}
    new_to_old: dict[int, set[int]] = {index: set() for index in range(len(new_chunks))}
    new_by_source_block: dict[tuple[str, str, str], set[int]] = {}
    for new_index, new in enumerate(new_chunks):
        source_id = str(new.get("source_id", new.get("doc_id")) or "")
        doc_id = str(new.get("doc_id") or "")
        for block_id in _migration_blocks(new):
            new_by_source_block.setdefault((source_id, doc_id, block_id), set()).add(new_index)
    for old_index, old in enumerate(old_chunks):
        source_id = str(old.get("source_id", old.get("doc_id")) or "")
        doc_id = str(old.get("doc_id") or "")
        candidates: set[int] = set()
        for block_id in _migration_blocks(old):
            candidates.update(new_by_source_block.get((source_id, doc_id, block_id), set()))
        old_to_new[old_index].update(candidates)
        for new_index in candidates:
            new_to_old[new_index].add(old_index)

    records: list[dict] = []
    visited_old: set[int] = set()
    for start in range(len(old_chunks)):
        if start in visited_old:
            continue
        if not old_to_new[start]:
            visited_old.add(start)
            records.append(_migration_record("retired", [old_chunks[start]], []))
            continue
        component_old: set[int] = set()
        component_new: set[int] = set()
        old_queue = [start]
        while old_queue:
            old_index = old_queue.pop()
            if old_index in component_old:
                continue
            component_old.add(old_index)
            for new_index in old_to_new[old_index]:
                if new_index not in component_new:
                    component_new.add(new_index)
                    old_queue.extend(new_to_old[new_index] - component_old)
        visited_old.update(component_old)
        old_group = [old_chunks[index] for index in sorted(component_old)]
        new_group = [new_chunks[index] for index in sorted(component_new)]
        records.append(_migration_record(_migration_relation(old_group, new_group), old_group, new_group))
    return records


def write_chunk_id_migration(path: str | Path, records: list[dict]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    temporary.replace(output)


def _generic_chunks(
    document: dict,
    *,
    profile: ProfileConfig,
    config: SemanticChunkingConfig,
) -> SemanticBuildResult:
    """建立可由专用策略逐步替换的最小、确定性 profile 路由骨架。"""

    chunks: list[dict] = []
    excluded: list[dict] = []
    section_path: list[str] = []
    for block in sorted(document["blocks"], key=lambda row: row["reading_order"]):
        block_type = block["block_type"]
        text = _normalized_text(block.get("cleaned_text"))
        if block_type in STRUCTURAL_BLOCK_TYPES:
            if text:
                level = int(block.get("heading_level") or 1)
                section_path = [*section_path[: level - 1], text]
            continue
        if block_type not in CONTENT_BLOCK_TYPES or not text:
            excluded.append({
                "block_id": block["block_id"],
                "reason": "empty_content" if not text else "non_semantic_block_type",
                "document_profile": profile.profile,
                "section_path": list(section_path),
                "content": text,
            })
            continue
        semantic_unit = "list" if block_type == "list_item" else block_type
        chunks.append(_make_chunk(
            document,
            profile=profile,
            config=config,
            section_path=section_path,
            blocks=[block],
            content=text,
            semantic_unit=semantic_unit,
        ))
    return SemanticBuildResult(chunks=chunks, excluded_blocks=excluded)


def build_semantic_chunks(
    document: dict,
    *,
    document_profile: str,
    config: SemanticChunkingConfig | None = None,
) -> SemanticBuildResult:
    require_production_canonical(document)
    active_config = config or load_semantic_chunking_config()
    profile = resolve_profile(document_profile, active_config)
    if profile.chunker_name == "rfc_semantic":
        result = _rfc_chunks(document, profile=profile, config=active_config)
    elif profile.chunker_name == "html_semantic":
        result = _html_chunks(document, profile=profile, config=active_config)
    elif profile.chunker_name == "pdf_semantic":
        result = _pdf_chunks(document, profile=profile, config=active_config)
    elif profile.chunker_name == "openapi_semantic":
        result = _openapi_chunks(document, profile=profile, config=active_config)
    else:
        result = _generic_chunks(document, profile=profile, config=active_config)
    return _apply_short_content_policy(result, profile=profile, config=active_config)
