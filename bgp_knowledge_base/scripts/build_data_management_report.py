#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import glob

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "data_management_capabilities.yaml"


SECTION_BY_CAPABILITY = {
    "data_asset_inventory": "数据资产清单",
    "data_model_standards": "数据模型标准覆盖",
    "metadata_lineage": "元数据与溯源覆盖",
    "quality_governance": "质量治理能力",
    "lifecycle": "生命周期现状",
    "semantic_quality_governance": "语义质量治理能力",
    "service_access": "服务化访问现状",
    "standard_exports": "标准化出口现状",
}


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def path_exists(pattern):
    target = ROOT / pattern
    if any(char in pattern for char in "*?[]"):
        return bool(glob.glob(str(target)))
    return target.exists()


def evidence_status(evidence):
    checked = []
    missing = []
    for item in evidence:
        exists = path_exists(item)
        checked.append((item, exists))
        if not exists:
            missing.append(item)
    return checked, missing


def status_label(status):
    return {
        "achieved": "已完成",
        "partial": "部分完成",
        "planned": "已规划",
        "not_started": "未开始",
        "deferred": "暂缓",
    }.get(status, status)


def render_asset_table(asset_groups):
    lines = [
        "| 资产组 | 状态 | 说明 | 主要路径 | 证据缺失数 |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for group in asset_groups:
        _, missing = evidence_status(group.get("evidence", []))
        paths = "<br>".join(f"`{path}`" for path in group.get("paths", []))
        lines.append(
            f"| {group['name']} (`{group['id']}`) | {status_label(group['status'])} | "
            f"{group['description']} | {paths} | {len(missing)} |"
        )
    return lines


def render_capability_sections(capability_groups):
    lines = []
    for group in capability_groups:
        heading = SECTION_BY_CAPABILITY.get(group["id"], group["name"])
        checked, missing = evidence_status(group.get("evidence", []))
        lines.extend([
            f"## {heading}",
            "",
            f"- 状态：{status_label(group['status'])}",
            f"- 能力 ID：`{group['id']}`",
            f"- 说明：{group['description']}",
            "",
            "| 证据 | 状态 |",
            "| --- | --- |",
        ])
        for item, exists in checked:
            lines.append(f"| `{item}` | {'存在' if exists else '缺失'} |")
        if group.get("next_steps"):
            lines.extend(["", "后续动作："])
            for step in group["next_steps"]:
                lines.append(f"- {step}")
        if missing:
            lines.extend(["", "缺失证据："])
            for item in missing:
                lines.append(f"- `{item}`")
        lines.append("")
    return lines


def render_gap_summary(asset_groups, capability_groups):
    lines = ["## 缺口与下一步建议", ""]
    gaps = [
        group
        for group in [*asset_groups, *capability_groups]
        if group.get("status") != "achieved"
    ]
    if not gaps:
        lines.append("- 当前配置中的资产和能力均标记为已完成。")
        return lines

    for group in gaps:
        lines.append(f"- {group['name']}：{status_label(group['status'])}。{group['description']}")
        for step in group.get("next_steps", []):
            lines.append(f"  - 下一步：{step}")
    return lines


def build_report(config):
    asset_groups = config["asset_groups"]
    capability_groups = config["capability_groups"]
    all_groups = [*asset_groups, *capability_groups]
    status_counts = Counter(group["status"] for group in all_groups)
    missing_evidence = []
    for group in all_groups:
        _, missing = evidence_status(group.get("evidence", []))
        missing_evidence.extend((group["id"], item) for item in missing)

    lines = [
        "# 数据管理能力报告",
        "",
        "## 范围",
        "",
        "本报告基于 `config/data_management_capabilities.yaml` 生成，用于盘点 BGP KB 数据资产、治理能力、证据覆盖和下一步缺口。",
        "",
        "该步骤不联网、不下载、不调用 LLM，不修改实体、关系、chunk 或发布包。",
        "",
        "## 摘要",
        "",
        f"- 配置版本：`{config['version']}`",
        f"- 数据资产组数：{len(asset_groups)}",
        f"- 能力模块数：{len(capability_groups)}",
        f"- 证据缺失数：{len(missing_evidence)}",
        "",
        "## 状态统计",
        "",
        "| 状态 | 数量 |",
        "| --- | ---: |",
    ]
    for status in config["allowed_statuses"]:
        lines.append(f"| {status_label(status)} (`{status}`) | {status_counts.get(status, 0)} |")

    lines.extend(["", "## 数据资产清单", ""])
    lines.extend(render_asset_table(asset_groups))
    lines.append("")
    lines.extend(render_capability_sections(capability_groups))

    lines.extend(render_gap_summary(asset_groups, capability_groups))

    if missing_evidence:
        lines.extend(["", "## 证据缺失清单", "", "| 分组 | 缺失证据 |", "| --- | --- |"])
        for group_id, item in missing_evidence:
            lines.append(f"| `{group_id}` | `{item}` |")

    return "\n".join(lines) + "\n"


def main():
    config = load_config()
    report_path = ROOT / config["generated_policy"]["report_path"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(config), encoding="utf-8")
    print(f"Wrote {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
