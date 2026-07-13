# screen 会话契约

现阶段保留以下会话名：

- 前端：`bgpkb_frontend_wbt`，端口 `39280`。
- FastAPI：`bgpkb_fastapi_wbt`，端口 `39281`。

会话命令由部署脚本生成；本目录不保存密钥或服务器 `.env`。

`restart-services` 从部署根目录的 `current` 与 `current-artifact` 指针启动服务，保持原会话名和端口不变。FastAPI 的权威入口为 `bgpkb.api.app:app`。
