# 对话前端项目分支设计

## 目标

在独立分支 `codex/project-chat-frontend` 中新增 `chat_frontend/` 前端应用，把现有 BGP RAG FastAPI 服务包装成 ChatGPT 类型的对话工作台。第一版只消费现有只读 API，不改变知识库构建、检索排序、评测集或阶段验收配置。

## 范围

纳入第一版的功能包括：Next.js App Router 前端、服务端 `/api/chat` 代理、BGP RAG 客户端、普通 JSON 回答、引用面板、检索状态、本地会话历史和基础测试。流式输出、账号系统、文件上传、多租户、真实 provider 切换和数据库持久化不进入第一版。

## 架构

浏览器只访问 `chat_frontend` 的 Next.js 页面和 `/api/chat`。Next.js 服务端读取 `BGP_RAG_BASE_URL`，调用现有 FastAPI 的 `POST /api/v1/rag/answer`、`GET /api/v1/retrieval/context-pack`、`GET /api/v1/retrieval/search` 和 `GET /health`。浏览器端不读取模型 API key，也不直接请求 DeepSeek、SiliconFlow 或 OpenAI。

## 组件边界

- `lib/env.ts`：读取和校验服务端环境变量，禁止前端 API key 约定。
- `lib/chat-types.ts`：定义消息、引用、检索状态、RAG 响应和 API 响应类型。
- `lib/bgp-rag-client.ts`：封装 FastAPI 请求、超时、错误转换和状态保留。
- `app/api/chat/route.ts`：接收前端消息，提取最后一条用户问题，调用 RAG client 并转换成前端消息格式。
- `components/chat/*`：只负责工作台 UI、消息流、输入框、引用和状态展示。
- `components/layout/*`：负责侧边栏和顶部服务状态。

## 数据流

用户提交问题后，前端把 `messages` 和 `options.limit` 发到 `/api/chat`。API route 取最后一条 user 消息，调用 `answerQuestion(query, limit)`。后端返回 `answer_status`、`answer`、`citations` 和 `context_pack` 后，Next.js 统一转换为 `message`、`answerStatus`、`citations`、`retrieval` 和 `error`。无证据时返回拒答消息；LLM 不可用时展示模型不可用但保留证据；FastAPI 不可用时返回可理解错误。

## UI 设计

首屏就是对话工作台。左侧展示会话、示例问题和服务状态；中间是消息流和固定底部输入区；右侧是引用与证据面板，窄屏时折叠到消息流下方。视觉方向采用“网络运维控制台”：高密度、克制、可扫描，使用清晰边框、状态色和等宽证据片段，避免营销页和模板品牌残留。

## 本地历史

第一版使用 `localStorage` 保存会话 id、消息、引用和最近一次检索摘要。清空会话会删除本地记录。历史记录不保存任何 API key、后端地址中的凭据或模型 provider 密钥。

## 错误处理

RAG client 为所有后端调用设置超时。网络错误、非 2xx 响应和响应格式异常都会转换为 `error` 状态，不伪装成成功答案。`answer_status` 原样保留给 UI，UI 根据 `answered`、`no_evidence`、`llm_unavailable` 和 `error` 展示不同状态。

## 测试与验收

使用 Vitest 覆盖 RAG client 的成功、无证据和服务不可用结果，覆盖 `/api/chat` 的消息提取、拒答和错误转换。使用 Next.js build 验证生产构建，使用 lint 和安全扫描确认没有 `NEXT_PUBLIC_*_API_KEY` 或疑似 key。后端阶段目录不新增对话前端文档。
