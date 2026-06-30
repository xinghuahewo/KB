---
title: "BGP 对话前端项目说明"
document_type: "项目说明"
purpose: "记录已交付对话前端的定位、目录、接口、运行方式和维护边界。"
scope: "独立 Next.js 对话前端与 BGP KB FastAPI 服务的集成"
status: "已交付"
last_reviewed: "2026-06-29"
---
# BGP 对话前端项目说明

## 项目定位

对话前端是 BGP 知识库之外的独立产品界面，位于知识库同级目录 `../../../chat_frontend/`。它消费知识库的只读 RAG 接口，不参与知识库流水线，也不修改实体、关系、chunk 或发布数据。

## 已交付能力

- Next.js 对话界面和本地会话历史。
- 普通回答与流式回答代理接口。
- 引用、来源证据和检索状态展示。
- 后端不可用、证据不足和模型不可用状态处理。
- API 客户端、路由和本地存储测试。

## 系统边界

```text
浏览器
  -> chat_frontend 的 /api/chat 或 /api/chat/stream
  -> BGP KB FastAPI 的 /api/v1/rag/answer
  -> 检索、context pack、答案和引用
```

浏览器不直接读取模型密钥，也不直接调用 DeepSeek、SiliconFlow 或其他模型服务。服务端代理负责读取环境变量并调用 BGP KB 后端。

## 主要目录

| 路径 | 作用 |
| --- | --- |
| `../../../chat_frontend/app/` | 页面、布局和服务端 API 路由。 |
| `../../../chat_frontend/components/` | 对话、引用、状态和布局组件。 |
| `../../../chat_frontend/lib/` | BGP RAG 客户端、类型、环境变量和本地存储。 |
| `../../../chat_frontend/tests/` | API 客户端、路由、流式响应和存储测试。 |

## 依赖接口

前端主要依赖知识库服务的 `POST /api/v1/rag/answer`。知识库服务还提供健康检查、混合检索和 context pack 接口，具体契约以 FastAPI OpenAPI 输出和服务测试为准。

## 本地运行

先在 `bgp_knowledge_base/` 启动后端：

```bash
PYTHONPATH=src uvicorn bgpkb.service.app:app --reload --host 127.0.0.1 --port 8000
```

再在 `../../../chat_frontend/` 启动前端：

```bash
yarn install
yarn dev
```

环境变量以 `../../../chat_frontend/.env.example` 为准。模型密钥只允许配置在服务端环境中，不得提交到仓库或暴露给浏览器。

## 维护规则

- 后端接口变化时，同步更新 `lib/bgp-rag-client.ts` 和相关测试。
- 新增前端能力不得绕过知识库的可信集合、引用和拒答边界。
- 前端项目不进入知识库阶段验收链；知识库流水线也不负责构建前端。
- 运行事实以代码和测试为准，本文件只保留稳定边界，不再记录一次性开发任务清单。
