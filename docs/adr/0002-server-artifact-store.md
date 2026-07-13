# ADR-0002：采用服务器不可变制品库

- 状态：已接受
- 日期：2026-07-13

## 背景

语料、SQLite、向量索引和报告约 2 GB，曾混入普通 Git 工作流，导致无共同祖先、推送困难和历史膨胀。

## 决策

运行数据迁移到 `/srv/bgpkb/artifacts/releases/<release-id>`。每个 release 不可变，包含 `SHA256SUMS`；Git 只保存 `artifacts/releases.yaml`。代码通过 `BGPKB_DATA_DIR` 选择制品。

## 后果

源码仓库保持轻量，代码与数据可独立回滚；部署前必须额外完成制品分发、注册和校验。开发者需要最小 fixture 或显式 artifact gate。

## 未采用方案

- 普通 Git：不适合大型生成二进制和高频制品。
- 全量 Git LFS：仍把运行发布与源码协作耦合，当前服务器制品库更直接。
- 仅对象存储：当前私有服务器已有持久磁盘，暂不增加外部依赖。
