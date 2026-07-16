## 1. 退役基线与证明契约

- [ ] 1.1 固化当前生产代码/制品对、deployment state、服务健康、运行环境非密钥字段和历史 release/snapshot/审计证据数量与 hash
- [ ] 1.2 先为生产 blocking 依赖、legacy 环境开关、旧 DB 文件句柄、current manifest v1 输入和历史证据误分类编写失败测试
- [ ] 1.3 实现机器可读退役证明器，输出 active/preserved 分类、路径、release id、hash、检查时间与非零失败状态
- [ ] 1.4 在未删除兼容面前运行退役证明 dry-run，确认生产活动 v1 引用为 0，静态 deprecated 引用全部有 owner 和处置决定

## 2. 在线 reader 失败关闭

- [ ] 2.1 先为 `BGPKB_ALLOW_LEGACY_READER=1`、只有 `bgp_knowledge_base.sqlite`、不兼容 minimum reader 和跨 release 混用编写启动失败测试
- [ ] 2.2 移除 `serving_bundle` 的 legacy 检测/开关/降级分支，让 database、retrieval adapter 和 FastAPI 只接受当前 serving schema
- [ ] 2.3 删除在线响应中仅为 legacy reader 存在的 degraded 诊断，保持现有 API/SSE/前端字段契约不变
- [ ] 2.4 增加新 serving bundle 正常启动、governance 制品缺失仍可在线服务、旧 DB 必须拒绝的完整 contract 回归

## 3. v1 平行入口收敛

- [ ] 3.1 根据 `legacy_v1_dependencies.yaml` 对每个已登记路径确认删除、隔离审计或保留历史 release 的唯一处置，拒绝无处置记录
- [ ] 3.2 先为 Make/CLI/CI/部署脚本重新调用 parsed/cleaned/chunks v1 构建器编写失败扫描测试
- [ ] 3.3 删除被五阶段完全取代的 v1 构建、画像、报告和 manifest 生产入口，保持五阶段子任务诊断能力
- [ ] 3.4 将确有追溯价值的旧决策查阅收敛为不安装到服务运行包的离线审计入口，禁止其输出进入 publish-index
- [ ] 3.5 更新依赖扫描策略，删除已退役 deprecated 例外，并证明新增例外不能通过 CI

## 4. 历史证据保留与迁移核对

- [ ] 4.1 对比退役前后历史 release、source snapshots、v1 人工决策、chunk migration、评测和回滚证据的数量与 hash，任一删除/改写必须阻断
- [ ] 4.2 验证隔离审计只读导出不修改治理状态、不生成 retrieval documents、不进入 embedding 或真实评测
- [ ] 4.3 更新中文运维/流水线文档，仅保留新五阶段入口、历史查阅、成对回滚和故障诊断，不改写 ADR 与历史事实

## 5. 发布验收与成对回滚

- [ ] 5.1 运行后端完整测试、静态检查、compileall、`uv build`、前端 contract 测试/构建、OpenSpec strict validation、退役证明和 `git diff --check`
- [ ] 5.2 从干净提交构建新代码 release，重新验证它与当前不可变 serving 制品的 schema、hash、API 与模型配置兼容性
- [ ] 5.3 在生产服务器 `/tmp` 启动隔离 canary，证明旧 DB 组合失败关闭、新 serving 组合的健康/SSE/典型/拒答/长回答/多引用/时延通过
- [ ] 5.4 在隔离部署根重演候选代码/当前制品成对切换和 previous 成对回滚，证明旧 release 无需重建可恢复
- [ ] 5.5 获得人工明确批准后才执行生产成对切换，验证原 screen、公网入口、V4 Pro revision、无降级和热态检索门禁
- [ ] 5.6 生成最终退役/保留/发布/回滚证据报告，完成需求追踪、OpenSpec 同步和归档决策
