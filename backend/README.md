# BGP 知识库后端

本目录是 Python 后端包，包含领域配置、离线流水线、检索服务和测试。项目级说明以仓库根 [README](../README.md) 和 [架构文档](../docs/architecture.md) 为准。

## 本地开发

```bash
uv sync --frozen --all-groups
uv run pytest -q -m 'not artifact and not legacy_documentation'
uv run uvicorn bgpkb.api.app:app --host 127.0.0.1 --port 39281
```

旧 `bgpkb.service.*` 与 `bgpkb.pipeline.*` 在迁移期保留兼容入口；新代码应使用 `domain`、`infrastructure`、`ingestion`、`indexing`、`publishing`、`retrieval`、`api` 和 `workflows`。

在线服务必须设置 `BGPKB_DATA_DIR`。真实制品校验与测试从仓库根 Makefile 运行，禁止把 `data/` 中的运行产物提交到 Git。
