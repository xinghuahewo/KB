# 对话前端实施计划

> **给自动化执行者：** 逐项执行本计划时，优先使用 `superpowers:subagent-driven-development`，也可使用 `superpowers:executing-plans`。步骤使用 checkbox（`- [ ]`）语法跟踪。

**目标：** 新增 `chat_frontend/`，把现有 BGP RAG FastAPI 服务包装成可本地运行的 ChatGPT 类型对话工作台。

**架构：** Next.js App Router 提供页面和 `/api/chat` 服务端代理。浏览器只和 Next.js 交互，Next.js 服务端调用现有 FastAPI RAG API，并把 `answer_status`、引用和检索状态转换为前端消息格式。

**技术栈：** Next.js、React、TypeScript、Tailwind CSS、Vitest、localStorage、现有 FastAPI RAG 服务。

---

### Task 1: 项目骨架和环境边界

**文件：**
- 新建：`chat_frontend/package.json`
- 新建：`chat_frontend/next.config.mjs`
- 新建：`chat_frontend/tsconfig.json`
- 新建：`chat_frontend/vitest.config.ts`
- 新建：`chat_frontend/postcss.config.js`
- 新建：`chat_frontend/tailwind.config.ts`
- 新建：`chat_frontend/app/layout.tsx`
- 新建：`chat_frontend/app/globals.css`
- 新建：`chat_frontend/.env.example`

- [ ] **Step 1: 创建最小 Next.js 配置和依赖**

使用 Next.js App Router、TypeScript、Tailwind 和 Vitest。`.env.example` 只包含 `BGP_RAG_BASE_URL`、`CHAT_PROVIDER`，不添加任何模型 API key 或 `NEXT_PUBLIC_*_API_KEY`。

- [ ] **Step 2: 运行依赖安装**

运行：`cd chat_frontend && corepack yarn install`

- [ ] **Step 3: 验证空项目构建基础**

运行：`cd chat_frontend && corepack yarn lint`

预期：lint 命令可执行，若页面尚未完成只允许出现明确的缺失文件错误。

### Task 2: BGP RAG client 的测试优先实现

**文件：**
- 新建：`chat_frontend/lib/env.ts`
- 新建：`chat_frontend/lib/chat-types.ts`
- 新建：`chat_frontend/lib/bgp-rag-client.ts`
- 新建：`chat_frontend/tests/bgp-rag-client.test.ts`

- [ ] **Step 1: 写成功返回的失败测试**

测试 `answerQuestion("route leak", 3)` 会向 `/api/v1/rag/answer` POST，保留 `answer_status=answered`、`citations` 和 `context_pack`。

- [ ] **Step 2: 运行测试确认失败**

运行：`cd chat_frontend && corepack yarn test bgp-rag-client.test.ts`

预期：FAIL，因为 `bgp-rag-client.ts` 尚不存在或函数未实现。

- [ ] **Step 3: 实现最小 client**

实现 `health()`、`answerQuestion()`、`getContextPack()`、`hybridSearch()`，统一使用 `fetch`、`AbortController` 和服务端 `BGP_RAG_BASE_URL`。

- [ ] **Step 4: 补充无证据和服务不可用测试**

覆盖 `answer_status=no_evidence` 原样返回，以及网络错误转换为明确异常。

- [ ] **Step 5: 运行测试确认通过**

运行：`cd chat_frontend && corepack yarn test bgp-rag-client.test.ts`

预期：PASS。

### Task 3: `/api/chat` 契约

**文件：**
- 新建：`chat_frontend/app/api/chat/route.ts`
- 新建：`chat_frontend/app/api/chat/stream/route.ts`
- 新建：`chat_frontend/tests/chat-api-route.test.ts`
- 新建：`chat_frontend/tests/chat-stream-route.test.ts`

- [ ] **Step 1: 写消息提取和成功转换的失败测试**

测试 route 从最后一条 `role=user` 的消息中提取问题，调用 RAG client，并返回 `{ message, answerStatus, citations, retrieval }`。

- [ ] **Step 2: 运行测试确认失败**

运行：`cd chat_frontend && corepack yarn test chat-api-route.test.ts`

预期：FAIL，因为 API route 尚未实现。

- [ ] **Step 3: 实现最小 route**

支持 `POST`，校验请求体，limit 默认 8，错误返回 HTTP 400 或 502。

- [ ] **Step 4: 补充拒答和后端不可用测试**

覆盖 `no_evidence` 返回拒答正文，后端异常返回 `answerStatus=error`。

- [ ] **Step 5: 运行测试确认通过**

运行：`cd chat_frontend && corepack yarn test chat-api-route.test.ts`

预期：PASS。

### Task 4: 对话工作台 UI

**文件：**
- 新建：`chat_frontend/app/page.tsx`
- 新建：`chat_frontend/components/chat/chat-shell.tsx`
- 新建：`chat_frontend/components/chat/message-list.tsx`
- 新建：`chat_frontend/components/chat/message-composer.tsx`
- 新建：`chat_frontend/components/chat/citation-panel.tsx`
- 新建：`chat_frontend/components/chat/retrieval-status.tsx`
- 新建：`chat_frontend/components/chat/example-prompts.tsx`
- 新建：`chat_frontend/components/layout/app-sidebar.tsx`
- 新建：`chat_frontend/components/layout/top-status-bar.tsx`

- [ ] **Step 1: 创建工作台页面**

首屏为三栏工作台，不做营销页。布局在移动端变成单栏，引用面板下移。

- [ ] **Step 2: 实现消息提交**

输入中文或英文问题后调用 `/api/chat`，把用户消息、助手消息、引用和检索状态写入 React state。

- [ ] **Step 3: 实现状态展示**

展示 `answered`、`no_evidence`、`llm_unavailable` 和 `error` 标签，引用数量、检索结果数和 source 信息。

- [ ] **Step 4: 实现基础交互**

支持复制消息、清空会话、示例问题填入输入框、发送时禁用按钮。

### Task 5: localStorage 会话历史

**文件：**
- 新建：`chat_frontend/lib/storage.ts`
- 修改：`chat_frontend/components/chat/chat-shell.tsx`

- [ ] **Step 1: 写 storage 单元测试**

覆盖保存、读取、清空，以及损坏 JSON 时返回空会话。

- [ ] **Step 2: 实现 storage helper**

只保存会话 id、messages、citations、retrieval，不保存 API key。

- [ ] **Step 3: 接入 UI**

页面加载时恢复最近会话，消息变化时保存，清空时删除。

### Task 6: 验收与安全扫描

**文件：**
- 按需修改：`chat_frontend/*`

- [ ] **Step 1: 运行前端测试**

运行：`cd chat_frontend && corepack yarn test`

预期：PASS。

- [ ] **Step 2: 运行 lint 和 build**

运行：`cd chat_frontend && corepack yarn lint && corepack yarn build`

预期：PASS。

- [ ] **Step 3: 运行安全扫描**

运行：`rg "sk-[A-Za-z0-9_-]{20,}" .`

预期：无匹配。

运行：`rg "NEXT_PUBLIC_.*API_KEY" chat_frontend`

预期：无匹配。

- [ ] **Step 4: 确认阶段目录未新增对话前端文档**

运行：`git diff --name-only -- bgp_knowledge_base/docs/stages`

预期：无输出。

- [ ] **Step 5: 启动本地开发服务**

运行：`cd chat_frontend && corepack yarn dev`

预期：Next.js dev server 启动并打印 localhost URL。
