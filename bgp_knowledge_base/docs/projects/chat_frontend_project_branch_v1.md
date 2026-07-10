---
title: "BGP 对话前端项目说明"
document_type: "项目说明"
purpose: "记录已交付对话前端的定位、目录、接口、静态部署方式和维护边界。"
scope: "独立 Next.js 静态对话前端与 BGP KB FastAPI 服务的集成"
status: "已交付"
last_reviewed: "2026-07-09"
---
# BGP 对话前端项目说明

## 项目定位

对话前端是 BGP 知识库之外的独立产品界面，位于知识库同级目录 `../../../chat_frontend/`。它消费知识库的只读 RAG 接口，不参与知识库流水线，也不修改实体、关系、chunk 或发布数据。

## 已交付能力

- Next.js 静态导出对话界面和本地会话历史。
- 直接面向用户的证据问答、相关章节、引用和知识库状态展示。
- 静态文件服务中的同源代理，转发 `/api/`、`/health`、`/sources/`、`/entities/` 和 `/search` 到 BGP KB FastAPI。
- 后端不可用、证据不足和模型不可用状态处理。
- API 客户端、路由和本地存储测试。

## 系统边界

```text
浏览器
  -> chat_frontend 静态服务 10.99.8.28:39280
  -> 同源代理 /api/v1/rag/answer
  -> BGP KB FastAPI 127.0.0.1:39281
  -> 检索、context pack、答案和引用
```

浏览器不直接读取模型密钥，也不直接调用 DeepSeek、SiliconFlow、BGE-M3 或 reranker 服务。静态服务中的 Python 同源代理只转发知识库 HTTP 请求；模型密钥仍只允许配置在 BGP KB 后端环境中。

## 主要目录

| 路径 | 作用 |
| --- | --- |
| `../../../chat_frontend/app/` | 页面、布局和服务端 API 路由。 |
| `../../../chat_frontend/components/` | 对话、引用、状态和布局组件。 |
| `../../../chat_frontend/lib/` | BGP RAG 客户端、类型、环境变量和本地存储。 |
| `../../../chat_frontend/scripts/` | 静态文件服务和同源代理脚本。 |
| `../../../chat_frontend/tests/` | API 客户端、路由、流式响应和存储测试。 |

## 依赖接口

前端主要依赖知识库服务的 `POST /api/v1/rag/answer`。知识库服务还提供健康检查、混合检索和 context pack 接口，具体契约以 FastAPI OpenAPI 输出和服务测试为准。

## 本地运行

先在 `bgp_knowledge_base/` 启动后端：

```bash
uv sync
uv run uvicorn bgpkb.service.app:app --reload --host 127.0.0.1 --port 8000
```

再在 `../../../chat_frontend/` 启动前端开发服务：

```bash
corepack yarn install
corepack yarn dev
```

环境变量以 `../../../chat_frontend/.env.example` 为准。模型密钥只允许配置在服务端环境中，不得提交到仓库或暴露给浏览器。

## 静态部署

生产部署采用 Next.js static export，而不是在服务器上运行 Next.js Node 进程。

当前远端使用 `screen` 常驻运行静态文件服务和同源代理；不迁移到 systemd。

本地构建：

```bash
cd ../../../chat_frontend
corepack yarn build
```

远端当前部署目录和后台会话：

```text
/home/wbt/DB/chat_frontend
screen: bgpkb_frontend_wbt
listen: 0.0.0.0:39280
backend proxy: http://127.0.0.1:39281
```

完整上传、重启、巡检命令见 [远端服务器与前端部署操作手册 v1](../operations/remote_server_operations_v1.md)。

访问入口：

```text
http://10.99.8.28/
http://10.99.8.28:39280/
```

当前若页面可打开但问答失败，优先检查 BGP KB FastAPI 的 `39281` 端口是否运行。

## 维护规则

- 后端接口变化时，同步更新 `lib/bgp-rag-client.ts` 和相关测试。
- 新增前端能力不得绕过知识库的可信集合、引用和拒答边界。
- 前端项目不进入知识库阶段验收链；知识库流水线也不负责构建前端。
- 生产前端保持轻量：用户只需要看到“证据问答、相关章节、引用和状态”，不暴露 `top_n`、`query_type`、reranker、token budget 等后端实现细节。
- 运行事实以代码和测试为准，本文件只保留稳定边界，不再记录一次性开发任务清单。
