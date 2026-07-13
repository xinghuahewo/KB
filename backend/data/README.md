# 运行数据制品

此目录用于本地开发和运行时展开知识库制品，不纳入普通 Git 历史。

当前已验证制品版本：`2026-07-10-93a4c97`。

- 服务器路径：`/srv/bgpkb/artifacts/releases/2026-07-10-93a4c97/data/`
- 完整性清单：`/srv/bgpkb/artifacts/releases/2026-07-10-93a4c97/SHA256SUMS`
- 清单 SHA-256：`97400ef06e8ef20c3d363918b79d2540d4e513e6fe5be4ea9e84e9c870f9a04b`
- 文件数：`1293`

部署前必须先校验制品清单，再将 `data/` 内容同步到目标运行目录。不得将语料、向量索引、SQLite 数据库、派生数据或生成报告重新提交到 Git。
