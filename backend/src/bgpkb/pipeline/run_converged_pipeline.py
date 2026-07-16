"""兼容 `python -m bgpkb.pipeline.run_converged_pipeline` 的五阶段入口。"""

from bgpkb.workflows.converged_pipeline import main


if __name__ == "__main__":
    raise SystemExit(main())
