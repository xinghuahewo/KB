#!/usr/bin/env python3
"""兼容入口：转发到显式启用的证据绑定知识候选抽取器。"""

from bgpkb.workflows.extract_knowledge_candidates import main


if __name__ == "__main__":
    raise SystemExit(main())
