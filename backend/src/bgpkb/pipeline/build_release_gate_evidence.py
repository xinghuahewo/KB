"""候选 release 统一真实评测 evidence CLI 兼容入口。"""

from bgpkb.workflows.release_gate_evidence import main


if __name__ == "__main__":
    raise SystemExit(main())
