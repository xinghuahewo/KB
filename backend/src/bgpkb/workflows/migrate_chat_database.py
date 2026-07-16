"""初始化或升级独立会话数据库。"""

from __future__ import annotations

import argparse
from pathlib import Path

from bgpkb.infrastructure.chat_store import ChatRepository, runtime_chat_database_path


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 BGP 问答会话 SQLite")
    parser.add_argument("--database", type=Path, default=runtime_chat_database_path())
    args = parser.parse_args()
    repository = ChatRepository(args.database)
    repository.initialize()
    health = repository.health()
    if health.get("integrity_check") != "ok":
        raise SystemExit(f"会话数据库初始化失败：{health}")
    print(f"会话数据库已就绪：{health['database_path']}（schema v{health['schema_version']}）")


if __name__ == "__main__":
    main()
