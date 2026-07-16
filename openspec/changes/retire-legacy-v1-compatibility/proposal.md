## Why

`rag-evidence-pipeline-v2` 已完成统一门禁、隔离 canary、成对回滚演练和生产切换；当前生产只读 `serving.sqlite`，没有活动 v1 文件句柄或阻断级 v1 依赖。继续保留默认运行面的 legacy reader 开关和过时平行脚本会增加误启用、跨 release 混读与维护分叉风险，因此应在独立、可回滚的变更中正式退役。

## What Changes

- **BREAKING**：移除在线 reader 的 `BGPKB_ALLOW_LEGACY_READER` 开关、legacy SQLite 自动/显式回退和对应 degraded 分支；在线服务只接受经验证的 `serving_sqlite_v1` 及后续兼容版本。
- **BREAKING**：移除已被五阶段流水线取代的 v1 parsed/cleaned/chunks 平行生产 CLI 和作业入口，不再把它们作为可运行产品表面。
- 将仍有追溯价值的 v1 数据、人工决策、迁移报告与历史 release 收敛为仓库外不可变审计面，仅允许独立离线导出/查阅工具读取，禁止进入 serving、embedding、真实评测和新治理决策。
- 把零活动 v1 引用扫描、历史制品保留、新 reader 失败关闭和成对回滚验证纳入退役门禁；任一证据缺失时不得删除兼容面。
- 删除过时文档和配置登记，保留 ADR、迁移映射、生产验收、回滚演练和历史 release 说明，不改写历史事实。

## Capabilities

### New Capabilities

- `legacy-v1-retirement`：定义 v1 活动引用归零证明、在线兼容面移除、离线审计保留、失败关闭与不重建历史 release 的验收要求。

### Modified Capabilities


## Impact

- 影响 `backend/src/bgpkb/infrastructure/serving_bundle.py`、在线 database/retrieval adapters、`backend/src/bgpkb/ingestion` 和 `publishing` 中登记的 legacy 工具、相关测试、运维文档与 v1 依赖策略。
- 不改变 FastAPI 路由、SSE 和前端响应契约，不引入账号/云同步，不更换 screen 部署。
- 不删除或改写 `/srv/bgpkb/artifacts/releases` 中的历史 release、source snapshots、旧治理证据和迁移映射；不把大型数据放入 Git。
- 前置证据为生产验收报告 `production-acceptance.json` SHA-256 `3192ea533f2ecb464b1bfd40d4881ac3e9e7aabb6256e86b1f98fb9eacf5309b`：新 serving bundle、公网 SSE、V4 Pro 绑定、热态检索、零 blocking v1 依赖和零活动 legacy 文件句柄均通过。
