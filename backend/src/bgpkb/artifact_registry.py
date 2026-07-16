"""Validate the repository's lightweight registry of external artifact releases."""

from __future__ import annotations

from pathlib import Path
import re

import yaml


class ArtifactRegistryError(ValueError):
    pass


RELEASE_ID_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")


def validate_release_registry(payload: dict) -> dict:
    if payload.get("schema_version") != 1:
        raise ArtifactRegistryError("不支持的制品注册表 schema_version")
    releases = payload.get("releases")
    if not isinstance(releases, list) or not releases:
        raise ArtifactRegistryError("制品注册表 releases 必须为非空数组")

    required = {
        "release_id",
        "source_commit",
        "file_count",
        "sha256sums_sha256",
        "data_path",
        "status",
    }
    release_ids = []
    for release in releases:
        if not isinstance(release, dict) or set(release) != required:
            raise ArtifactRegistryError("每个 release 必须且只能包含规定字段")
        release_id = release["release_id"]
        release_ids.append(release_id)
        if not isinstance(release_id, str) or RELEASE_ID_PATTERN.fullmatch(release_id) is None:
            raise ArtifactRegistryError(f"release_id 非法：{release_id}")
        if not re.fullmatch(r"[0-9a-f]{7,40}", str(release["source_commit"])):
            raise ArtifactRegistryError(f"source_commit 非法：{release['source_commit']}")
        if not isinstance(release["file_count"], int) or release["file_count"] <= 0:
            raise ArtifactRegistryError("file_count 必须为正整数")
        if not re.fullmatch(r"[0-9a-f]{64}", str(release["sha256sums_sha256"])):
            raise ArtifactRegistryError("sha256sums_sha256 必须为 64 位小写十六进制")
        expected_suffix = f"/releases/{release_id}/data"
        if not str(release["data_path"]).startswith("/") or not str(release["data_path"]).endswith(expected_suffix):
            raise ArtifactRegistryError(f"data_path 必须指向对应不可变 release：{release['data_path']}")
        if release["status"] not in {"current", "previous", "available"}:
            raise ArtifactRegistryError(f"未知 release status：{release['status']}")

    if len(release_ids) != len(set(release_ids)):
        raise ArtifactRegistryError("release_id 重复")
    current_release_id = payload.get("current_release_id")
    if current_release_id not in release_ids:
        raise ArtifactRegistryError("current_release_id 未登记")
    if sum(release["status"] == "current" for release in releases) != 1:
        raise ArtifactRegistryError("必须且只能有一个 current release")
    if next(release["release_id"] for release in releases if release["status"] == "current") != current_release_id:
        raise ArtifactRegistryError("current_release_id 与 current 状态不一致")
    return payload


def load_release_registry(path: Path) -> dict:
    if not path.is_file():
        raise ArtifactRegistryError(f"制品注册表不存在：{path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ArtifactRegistryError("制品注册表根节点必须为对象")
    return validate_release_registry(payload)
