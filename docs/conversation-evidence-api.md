# 会话、流式回答与证据接口

## 目标与兼容性

本接口为前端提供服务端会话历史、真正的流式回答、阶段耗时和消息内证据定位。原有 `POST /api/v1/rag/answer` 与 `POST /api/v1/rag/answer/stream` 保留；新前端使用会话作用域的 turn stream。

除 `/health` 和旧无状态接口外，下列会话接口都要求 `X-BGP-Client-ID`。该值是匿名命名空间标识，不是认证凭据；服务端只保存加盐哈希。客户端标识不匹配时统一返回 `404`，避免泄露其他命名空间的资源是否存在。

## HTTP 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/v1/conversations` | 新建会话 |
| `GET` | `/api/v1/conversations?limit=&cursor=` | 按更新时间倒序分页列出会话 |
| `GET` | `/api/v1/conversations/{conversation_id}` | 读取有序消息和持久化 citation 快照 |
| `DELETE` | `/api/v1/conversations/{conversation_id}` | 级联删除会话、消息、轮次与证据 |
| `POST` | `/api/v1/conversations/import` | 幂等导入旧浏览器 v2 单会话 |
| `POST` | `/api/v1/conversations/{conversation_id}/turns/stream` | 用 SSE 创建或恢复一轮问答 |
| `POST` | `/api/v1/conversations/{conversation_id}/turns/{request_id}/stop` | 停止并收敛到可恢复终态 |
| `GET` | `/api/v1/conversations/{conversation_id}/messages/{message_id}/evidence/{citation_id}` | 读取该助手消息内的 citation 详情 |

turn 请求必须带稳定 `request_id`，可选带客户端生成的用户和助手消息 ID，并通过 `resume_after_sequence` 恢复。相同会话与 `request_id` 重试不会重复插入消息。

```json
{
  "request_id": "request-20260716-000001",
  "query": "RPKI 如何帮助防止错误路由发布？",
  "limit": 8,
  "user_message_id": "message-user-000001",
  "assistant_message_id": "message-assistant-000001",
  "resume_after_sequence": 0
}
```

## SSE 事件

每帧使用 `data: <JSON>\n\n`。带 `sequence` 的事件严格递增；客户端丢弃小于等于已处理序号的重复帧。

| 事件 | 关键字段 | 含义 |
| --- | --- | --- |
| `stage` | `stage`、`status`、`duration_ms`、`elapsed_ms` | 召回、精排、上下文、等待首字、生成、持久化的开始或完成 |
| `answer_delta` | `delta` | 可立即展示的正文增量 |
| `citation_delta` | `citation_ids`、`label` | 已通过 allowlist 的结构化行内引用 |
| `heartbeat` | `elapsed_ms` | 长阶段保活，不修改正文 |
| `answer_snapshot` | `answer`、`answer_parts` | 断线恢复时校正当前正文和引用结构 |
| `done` | `payload`、`timings` | 已持久化的权威终态 |
| `error` | `status`、`partial_answer`、`timings` | 错误或停止后的可恢复状态 |

`timings` 使用服务端单调时钟，包含 `retrieval_ms`、`rerank_ms`、`context_ms`、`ttft_ms`、`generation_ms`、`persistence_ms` 和 `total_ms`。界面完成后展示召回、精排、首字、生成和总计；本地计时只用于进行中的反馈。

最终 payload 同时保留纯文本 `answer` 和结构化 `answer_parts`。引用只能来自本轮 context pack 的稳定标识，例如：

```json
[
  {"type": "text", "text": "RPKI 通过 ROA 绑定前缀与起源 AS"},
  {"type": "citation", "citation_ids": ["ev_1"], "label": "1"},
  {"type": "text", "text": "，网络可据此进行起源验证。"}
]
```

## 证据详情

证据详情默认 `scope=section`，返回完整句摘录、上下文快照和相关章节。`scope=document&cursor=<n>` 按受限 section 页读取完整文档；响应提供下一游标，前端按需加载。服务端先验证 conversation、assistant message 与 citation 的所属关系，再从当前只读 release 读取内容，不接受客户端文件路径。

历史消息始终保留回答当时的证据快照和 `release_id`。当当前知识库 release 与快照不一致时，接口继续返回当时的完整句，同时显式提示当前文档来自新 release；不得静默把新内容伪装成旧证据。

## 代理要求

SSE 路径必须直接到 FastAPI，禁用代理缓存和响应缓冲，保持 HTTP/1.1，并把读写超时设为至少 180 秒。仓库配置位于 `infra/nginx/bgpkb.conf`。静态前端自带的本地代理也必须逐行转发响应，不能先读完整答案再返回。
