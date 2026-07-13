#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "llm_candidate_enrichment.yaml"
CHUNKS = paths.PUBLISHED_DIR / "chunk_catalog.jsonl"
ENTITIES = paths.PUBLISHED_DIR / "entity_catalog.jsonl"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def require_provider_ready(config, provider):
    if provider == "mock":
        return
    provider_config = config["providers"].get(provider)
    if provider_config is None:
        raise SystemExit(f"Unknown provider: {provider}")
    api_key_env = provider_config.get("api_key_env", "")
    if api_key_env and not os.environ.get(api_key_env):
        print(f"{provider} provider requires environment variable {api_key_env}", file=sys.stderr)
        raise SystemExit(2)


def interesting_chunks(chunks):
    needles = ["route leak", "prefix hijack", "rpki", "as_path", "moas"]
    selected = []
    for chunk in chunks:
        text = " ".join([
            chunk.get("title", ""),
            chunk.get("content_preview", ""),
            " ".join(chunk.get("topics", [])),
        ]).lower()
        if any(needle in text for needle in needles):
            selected.append(chunk)
        if len(selected) >= 25:
            break
    return selected


def build_candidates(provider):
    chunks = interesting_chunks(load_jsonl(CHUNKS))
    entity_ids = {entity.get("entity_id", "") for entity in load_jsonl(ENTITIES)}
    chunk_candidates = []
    link_candidates = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id", "")
        preview = chunk.get("content_preview", "")
        keywords = sorted(set(part.strip(".,;:()").lower() for part in preview.split() if len(part) > 4))[:8]
        if "route" not in keywords:
            keywords.insert(0, "route")
        chunk_candidates.append({
            "candidate_id": f"chunk_enrichment_{chunk_id}",
            "chunk_id": chunk_id,
            "semantic_title": chunk.get("title", "") or chunk_id,
            "summary": " ".join(preview.split())[:280],
            "keywords": keywords,
            "evidence_type": chunk.get("chunk_type", "chunk"),
            "source_ref": chunk.get("source_ref", ""),
            "review_status": "pending_review",
            "provider": provider,
            "generated_by": "src/bgpkb/pipeline/build_llm_candidate_enrichment.py",
        })
        entity_id = "anomaly_route_leak" if "anomaly_route_leak" in entity_ids else ""
        if entity_id:
            link_candidates.append({
                "candidate_id": f"entity_link_{chunk_id}_{entity_id}",
                "chunk_id": chunk_id,
                "entity_id": entity_id,
                "confidence": 0.55 + min(index, 10) / 100,
                "source_ref": chunk.get("source_ref", ""),
                "review_status": "pending_review",
                "provider": provider,
                "generated_by": "src/bgpkb/pipeline/build_llm_candidate_enrichment.py",
            })
    return chunk_candidates, link_candidates


def main():
    parser = argparse.ArgumentParser(description="Build offline LLM candidate enrichment framework outputs.")
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()
    cfg = load_config()
    provider = args.provider or cfg.get("default_provider", "mock")
    require_provider_ready(cfg, provider)

    chunk_candidates, link_candidates = build_candidates(provider)
    chunk_path = ROOT / cfg["generated_policy"]["chunk_candidates_path"]
    link_path = ROOT / cfg["generated_policy"]["entity_link_candidates_path"]
    write_jsonl(chunk_path, chunk_candidates)
    write_jsonl(link_path, link_candidates)
    print(f"Wrote {chunk_path.relative_to(ROOT)}")
    print(f"Wrote {link_path.relative_to(ROOT)}")
    print(f"Provider: {provider}; candidates require human review; primary entities unchanged")


if __name__ == "__main__":
    main()
