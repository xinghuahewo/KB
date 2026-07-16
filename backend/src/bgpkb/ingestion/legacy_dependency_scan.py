"""扫描仍直接读取 parsed/cleaned/chunks v1 的生产代码引用。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import yaml

from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json


_SYMBOLS = ("PARSED_DIR", "CLEANED_DIR", "CHUNKS_DIR")
_ATTRIBUTE_PATTERN = re.compile(r"\b(?:paths\.)?(PARSED_DIR|CLEANED_DIR|CHUNKS_DIR)\b")
_ADAPTER_PATTERN = re.compile(r"\bread_legacy_read_only\s*\(")
_SKIP_PARTS = {".git", ".venv", "__pycache__", "node_modules", "tests", "generated"}


def _scan_roots(root: Path) -> list[Path]:
    candidates = [
        root / "backend" / "src",
        root / "src",
    ]
    return [path for path in candidates if path.is_dir()]


def _load_policy(root: Path, policy_path: Path | None) -> dict[str, dict]:
    if policy_path is None:
        candidates = [
            root / "backend" / "metadata" / "config" / "legacy_v1_dependencies.yaml",
            root / "metadata" / "config" / "legacy_v1_dependencies.yaml",
        ]
        policy_path = next((path for path in candidates if path.is_file()), None)
    if policy_path is None:
        return {}
    payload = yaml.safe_load(Path(policy_path).read_text(encoding="utf-8")) or {}
    return {
        row["path"]: row
        for row in payload.get("deprecated_paths", [])
    }


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_v1_dependencies(root: Path, *, policy_path: Path | None = None) -> dict:
    """返回 blocking 与限期 deprecated 引用；忽略测试和生成报告。"""

    root = Path(root).resolve()
    policy = _load_policy(root, policy_path)
    references = []
    for scan_root in _scan_roots(root):
        for path in sorted(scan_root.rglob("*.py")):
            if path.is_symlink():
                continue
            if any(part in _SKIP_PARTS for part in path.parts):
                continue
            if path.name in {"paths.py", "legacy_dependency_scan.py"}:
                continue
            relative = _relative(path, root)
            lines = path.read_text(encoding="utf-8").splitlines()
            adapter_lines = {
                number for number, line in enumerate(lines, start=1) if _ADAPTER_PATTERN.search(line)
            }
            has_explicit_adapter = bool(adapter_lines)
            for number, line in enumerate(lines, start=1):
                for symbol in sorted(set(_ATTRIBUTE_PATTERN.findall(line))):
                    policy_row = policy.get(relative)
                    status = "deprecated" if has_explicit_adapter or policy_row else "blocking"
                    references.append({
                        "path": relative,
                        "line": number,
                        "symbol": symbol,
                        "status": status,
                        "reason": (
                            (policy_row or {}).get("reason")
                            or "文件通过显式 legacy 只读适配器访问历史数据"
                            if status == "deprecated"
                            else "新生产代码直接引用 v1 数据目录"
                        ),
                        "retire_by": (policy_row or {}).get("retire_by"),
                    })
            for number in sorted(adapter_lines):
                if not any(row["path"] == relative for row in references):
                    references.append({
                        "path": relative,
                        "line": number,
                        "symbol": "read_legacy_read_only",
                        "status": "deprecated",
                        "reason": "文件通过显式 legacy 只读适配器访问历史数据",
                        "retire_by": (policy.get(relative) or {}).get("retire_by"),
                    })
    references.sort(key=lambda row: (row["path"], row["line"], row["symbol"]))
    blocking = [row for row in references if row["status"] == "blocking"]
    deprecated = [row for row in references if row["status"] == "deprecated"]
    return {
        "schema_version": "legacy_v1_dependency_scan_v1",
        "summary": {
            "references": len(references),
            "blocking": len(blocking),
            "deprecated": len(deprecated),
        },
        "blocking_references": blocking,
        "deprecated_references": deprecated,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="扫描旧 parsed/cleaned/chunks v1 生产依赖")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-blocking", action="store_true")
    args = parser.parse_args(argv)
    report = scan_v1_dependencies(args.root, policy_path=args.policy)
    if args.output:
        atomic_write_json(args.output, report, indent=2)
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 1 if args.fail_on_blocking and report["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
