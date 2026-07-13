# 基础设施资产

本目录保存可审查的部署配置模板，不包含凭据和服务器运行数据。

- `nginx/bgpkb.conf`：裸 IP 前端入口与 API 代理模板。
- `screen/README.md`：当前 screen 会话契约。

正式部署和回滚统一从根 `scripts/` 入口执行。
