## Context

当前 `frontend/components/chat/chat-shell.tsx` 只把一个 `StoredConversation` 写入 `localStorage`，侧栏仅显示当前消息数和清空入口，无法列出或切换历史会话。消息复制直接调用可选的 `navigator.clipboard.writeText`，没有非安全上下文回退、异常捕获或可见反馈。回答使用轻量 Markdown 渲染，正文中没有可解析的证据标记；`CitationPanel` 只能展示 citation 预览或跳转到新页面，无法从回答中的具体论述定位到同轮证据。

当前 `/api/v1/rag/answer/stream` 虽返回 `text/event-stream`，但只发送检索、精排和生成阶段事件。`DeepSeekClient.generate_answer` 仍等待上游一次性 JSON 响应，前端 `rag-stream.ts` 也只识别 `stage`、`done` 和 `error`。因此界面会连续显示“正在检索……正在生成……”，随后突然出现完整答案；现有部分事件虽携带个别 latency 字段，但没有统一的阶段起止、首字时间和总耗时展示。

FastAPI 当前只提供无状态的 RAG 回答接口，发布知识库 SQLite 以 `mode=ro&immutable=1` 打开。这一只读边界必须保留，因此会话历史不能写入发布制品。现有 `ChunkStore` 已能按发布目录安全读取完整 chunk 和 section，可作为证据详情接口的基础。

本变更由前端体验驱动，但需要后端提供最小支撑：独立的运行时会话库、带会话的流式问答接口、结构化行内引用和受控的文档内容读取接口。首版面向当前私有部署，不引入账户系统。

## Goals / Non-Goals

**Goals:**

- 提供可创建、恢复、切换和删除的多会话历史，并持久保存每一轮的回答状态与证据快照。
- 修复复制按钮，使其在主 Clipboard API 不可用时仍有兼容路径，并明确反馈结果。
- 让回答正文中的引用标记与本轮 citation 一一映射，点击后在当前页面的“本轮证据”中定位、展开并高亮文档内容。
- 保证上一轮引用只打开上一轮证据，避免当前选中轮次与最新回答相互串扰。
- 让支持流式的回答模型真实地产生答案增量，并在前端平滑追加，而不是只流式展示状态。
- 为检索、精排、上下文、首字、生成、持久化和总流程提供可比较、可持久化的耗时数据。
- 保留现有无状态 RAG 接口和发布知识库只读边界，支持渐进部署与回滚。
- 为桌面端、移动端和键盘操作提供一致的核心能力。

**Non-Goals:**

- 不在本变更中引入登录、组织、角色权限或跨设备身份认证。
- 不实现多人共享会话、公开分享链接、会话导出或全文编辑。
- 不修改检索算法、跨语言召回策略或对事实支持度进行新的语义判定。
- 不要求查询类型分类、全局上下文摘要和其他后台模型调用都向用户逐 token 展示。
- 不把完整文档复制进每次问答响应，也不开放任意服务器文件读取。
- 不改变现有 screen 常驻方式、端口、nginx 入口或发布知识库格式。

## Decisions

### 1. 采用“前端主导、后端持久化”的分层方案

前端继续负责乐观渲染、活动会话和证据面板状态；后端成为历史对话的权威数据源。浏览器本地只保存匿名客户端标识、当前会话标识和未同步恢复缓存。

选择该方案是因为只使用 `localStorage` 无法可靠保存多个会话，也无法在浏览器数据被清理后恢复。备选方案是扩展本地存储为多会话，但仍不能满足前后端记录历史的目标。

### 2. 会话数据写入独立运行时 SQLite

新增由 `BGP_CHAT_DB_PATH` 指定的可写 SQLite，建议默认位于部署持久化目录的 `runtime/chat/chat_history.sqlite3`。它与只读的 `bgp_knowledge_base.sqlite` 分离，至少包含：

- `conversations`：`conversation_id`、`client_key_hash`、标题、创建/更新时间；
- `messages`：`message_id`、`conversation_id`、顺序、角色、正文、回答状态、阶段耗时 JSON、流式模式、时间；
- `message_evidence`：`citation_id`、助手消息、`chunk_id`、`source_id`、章节、可见摘录、引用快照和知识库发布标识；
- `turn_requests`：请求幂等键、处理状态及关联的用户/助手消息。

数据库启用外键、WAL、短事务和 schema version。会话库故障不得影响原有无状态 RAG 接口。备选方案是把表加入发布知识库，但会破坏不可变发布制品和只读运行契约，因此不采用。

### 3. 以匿名客户端标识做命名空间，不把它描述为认证

浏览器首次访问时生成高熵 `client_id`，请求通过 `X-BGP-Client-ID` 传递；后端只保存其带服务端盐的摘要，并校验长度与格式。所有会话读取和删除必须同时匹配 `conversation_id` 与客户端摘要，找不到统一返回 404，避免泄露存在性。

该标识用于私有部署中的会话隔离，不构成强认证。真正的跨设备同步和权限控制留给未来登录体系。

### 4. 新增带会话的幂等流式问答接口，保留原接口

新增接口契约：

- `POST /api/v1/conversations`：创建会话；
- `GET /api/v1/conversations?cursor=&limit=`：按更新时间倒序列出当前客户端会话；
- `GET /api/v1/conversations/{conversation_id}`：读取消息、回答状态和证据摘要；
- `DELETE /api/v1/conversations/{conversation_id}`：删除会话及其消息、证据；
- `POST /api/v1/conversations/{conversation_id}/turns/stream`：提交 `request_id`、问题和 limit，流式返回阶段事件与已持久化结果；
- `GET /api/v1/conversations/{conversation_id}/messages/{message_id}/evidence/{citation_id}`：读取该轮引用对应的章节或分页文档内容。

`request_id` 设置唯一约束。相同客户端、会话和 request 重试时返回既有结果或继续报告状态，不重复插入消息。最终 `done` 事件只在助手消息、阶段耗时和证据事务提交后发送；中止或失败也保存可辨识状态。现有 `/api/v1/rag/answer` 和 `/api/v1/rag/answer/stream` 保持兼容。

### 5. 上游模型流、服务端事件流和前端渲染流采用统一协议

回答路径为 DeepSeek 请求设置 `stream: true`，逐帧解析上游 SSE 的 `choices[].delta.content`、结束原因和 usage。服务端不等待完整回答才返回，而是把安全的文本增量继续推送给浏览器。查询分类、上下文摘要等内部调用保持现状。

对外 SSE 使用单调递增 `sequence`，事件类型至少包括：

```json
{"type":"stage","sequence":1,"stage":"retrieval","status":"started","elapsed_ms":0}
{"type":"stage","sequence":2,"stage":"retrieval","status":"complete","duration_ms":820,"elapsed_ms":820}
{"type":"answer_delta","sequence":8,"delta":"路由泄露通常"}
{"type":"citation_delta","sequence":9,"citation_ids":["ev_1"],"label":"1"}
{"type":"heartbeat","sequence":10,"elapsed_ms":15000}
{"type":"done","sequence":42,"payload":{},"timings":{}}
```

服务端使用 `time.perf_counter_ns()` 或等效单调时钟记录权威耗时：`retrieval_ms`、`rerank_ms`、`context_pack_ms`、`generation_ms`、`persistence_ms`、`model_ttft_ms`、从请求接受到首个可见答案的 `time_to_first_answer_ms` 以及 `total_ms`。每个阶段发出 started 和 complete；前端在阶段进行中用本地单调时钟刷新经过时间，完成后以服务端 duration 为准。最终 timings 随消息持久化，历史会话可再次查看。

上游不支持流式时允许退化为一次 `answer_snapshot`，但响应和界面 MUST 标记 `stream_mode=buffered`，不能把它显示成真实流式。心跳用于防止代理在长检索或首字等待期间判定连接空闲。

选择端到端增量协议，而不是在前端对完整答案模拟打字，因为模拟不能缩短首字等待，也会掩盖后端真实时延。

### 6. 后端返回结构化回答片段，不让前端猜测引用

生成阶段为模型提供本轮允许使用的 citation 标识，例如 `ev_1`、`ev_2`，并要求在答案中输出受控标记。后端只接受 allowlist 中的标识，解析后返回：

```json
{
  "answer": "兼容旧客户端的纯文本答案",
  "answer_parts": [
    {"type": "text", "text": "RPKI 可验证路由起源"},
    {"type": "citation", "citation_ids": ["ev_1"], "label": "1"}
  ],
  "citations": [
    {
      "citation_id": "ev_1",
      "chunk_id": "...",
      "source_id": "...",
      "section_id": "...",
      "content_preview": "完整句边界内的摘录"
    }
  ]
}
```

流式期间，服务端使用增量控制标记解析器缓冲可能不完整的 citation 标记：普通文本作为 `answer_delta` 发出，只有完整且通过 allowlist 的标记才转为 `citation_delta`，控制语法本身不会显示给用户。该解析器必须正确处理引用标记被拆到多个上游 chunk 的情况。最终 `done` 仍返回完整 `answer_parts` 作为权威快照，用于持久化、刷新恢复和校正增量结果。

前端只渲染经过验证的引用组件，避免使用字符偏移或解析任意 URL。无效标识不会变成链接，并在响应元数据中记录 `inline_citation_status`；普通 citations 列表继续可用。备选方案是在前端通过关键词把答案与证据自动关联，但容易产生错误归因，因此不采用。

### 7. 引用点击采用“选择轮次—打开面板—定位引用—按需加载”的状态机

前端活动状态包含 `activeConversationId`、`selectedAssistantMessageId`、`activeCitationId` 和已加载的证据详情缓存。用户点击引用后依次：

1. 将引用所属的助手消息设为当前证据轮次；
2. 桌面端显示右侧“本轮证据”，移动端打开证据抽屉；
3. 展开包含 `activeCitationId` 的文档卡片并滚动到引用；
4. 若正文尚未加载，调用该消息作用域内的证据详情接口；
5. 显示相关章节，突出对应 chunk；用户可继续加载分页的完整文档。

每个引用组件使用 `button` 语义、可见焦点和包含文档标题的 `aria-label`。面板加载失败时保留已持久化的摘录，不跳转到错误轮次。外部来源链接可以保留为次级入口，但不再承担主要核验流程。

### 8. 文档内容采用受控标识和懒加载

证据详情接口只接受已属于该助手消息的 `citation_id`，再由服务端解析其已验证的 `chunk_id`、`section_id` 和 `source_id`。默认返回相关章节和高亮锚点；完整文档按 section 或游标分页读取，并设置响应大小上限。接口不得接受文件路径，也不得直接回传本机路径。

回答完成时持久保存引用摘录、上下文快照和 `release_id`。历史会话使用旧发布证据时，面板先展示快照；若当前发布与原发布不一致，明确标记版本差异，不用当前正文悄悄替换历史证据。

### 9. 复制使用双路径实现和可访问反馈

复制内容从消息的可读模型生成：正文保持段落和列表，行内引用转为 `[1]` 等文本标记，不复制内部 `citation_id`、内部接口 URL或隐藏上下文。实现先尝试 `navigator.clipboard.writeText`，失败或不可用时使用临时 `textarea` 和受控的 `document.execCommand("copy")` 回退，并在 `finally` 清理节点和选区。

结果通过按钮状态、短时提示和 `aria-live` 区域反馈“已复制”或“复制失败”，异常不得成为未处理的 Promise。复制不触发会话写入或重新检索。

### 10. 历史侧栏和本地数据采用渐进迁移

侧栏改为会话列表，展示标题、最后更新时间和状态；“新会话”只创建并切换空会话，不删除旧会话，“删除”需明确确认。标题首版由第一条用户问题确定性截断生成，不额外调用模型。

检测到现有 `bgp-chat-conversation` v2 数据时，前端通过一次性幂等导入将其保存为历史会话。只有服务端确认成功后才移除旧负载；失败时继续保留并提示“尚未同步”。

### 11. 流式界面同时优化即时反馈和阅读稳定性

前端不再用阶段文字覆盖助手正文。消息卡片把“阶段进度”和“答案内容”分离：生成首字前显示阶段时间线；收到首个 `answer_delta` 后立即展示正文，并在正文上方或下方继续显示紧凑的耗时状态。完成后保留可展开的阶段用时，例如“召回 0.8 秒 · 精排 1.4 秒 · 首字 3.2 秒 · 生成 5.6 秒 · 总计 8.1 秒”。

答案增量先进入内存缓冲，再按 animation frame 或约 30–50ms 批量提交 React 状态，减少每 token 重渲染。仅当用户位于消息列表底部附近时自动跟随输出；用户向上滚动后停止抢夺滚动位置，并提供“回到最新”入口。`aria-live` 只播报阶段切换和完成，不逐 token 朗读。

停止或连接异常时保留已经显示的正文，将消息标记为 `stopped` 或 `interrupted`，并保留已经完成的阶段耗时。重试相同 `request_id` 时根据 `sequence` 忽略重复事件，以最终持久化快照校正本地内容。

## Risks / Trade-offs

- [匿名客户端标识被复制后可访问同一命名空间] → 明确其不是认证；使用高熵标识、服务端摘要、私有网络边界，并为未来账户迁移保留 owner 字段。
- [流式请求中断导致半轮消息] → 先记录幂等请求和 pending 消息，终态事务更新；启动时可把超时 pending 标记为 interrupted。
- [代理缓冲或空闲超时使增量不能及时到达] → nginx 关闭该路由响应缓冲，SSE 设置 no-cache/no-transform，并定期发送心跳；部署验收测量首个增量到达时间。
- [每 token 更新 React 导致卡顿] → 在前端合并短时间窗内的增量，以 animation frame 批量渲染，并限制历史消息同时活跃的流数量。
- [citation 控制标记跨上游分片或流中断] → 服务端维护有限状态缓冲，只有闭合且合法的标记才发 citation 事件；未闭合内容在终态按安全文本或无效引用规则处理。
- [客户端断线后事件重复或顺序错乱] → 每个事件带递增 sequence，客户端去重并以最终持久化快照为准。
- [会话库写入增加服务复杂度] → 与发布库物理分离，设置迁移版本、WAL、备份和健康检查；故障时保留无状态 RAG 可用性。
- [模型遗漏或误用行内引用标记] → 只渲染 allowlist 引用，记录完整性状态；不通过前端猜测补链，普通证据列表作为降级入口。
- [完整文档过大造成面板卡顿] → 默认返回相关章节，完整文档分页或分 section 懒加载，前端缓存并限制 DOM 规模。
- [历史证据与新知识库发布不一致] → 保存证据快照和 release 标识；检测不一致时展示版本提示，优先保留历史可追溯内容。
- [Clipboard 回退依赖已弃用浏览器能力] → 仅作为兼容路径并完整捕获失败；现代安全上下文仍使用标准 Clipboard API。

## Migration Plan

1. 增加会话库 schema、repository 和健康检查，部署时创建持久化目录并验证 FastAPI 进程可写。
2. 为 DeepSeek 回答增加上游流式适配器、统一阶段计时和扩展 SSE 事件；先用旧前端验证旧 `stage` 与 `done` 仍兼容。
3. 增加会话 CRUD、幂等流式 turn 和证据详情接口，同时保持现有 RAG 接口不变。
4. 扩展 RAG 返回 DTO，返回答案增量、`answer_parts`、增强 citations 和 timings；旧前端继续读取最终 `answer`。
5. 上线前端渐进答案、阶段耗时、历史侧栏、同步状态、复制回退和引用导航；首次加载执行旧本地会话的一次性导入。
6. 调整 nginx SSE 路由的缓冲与超时设置，运行 API、前端单元、集成、移动端和端到端测试，再在远端启用会话持久化。
7. 若需回滚，先回滚前端到只消费最终 `done` 的旧版，再停用新会话接口；独立会话 SQLite 保留且不影响发布知识库和旧 RAG 接口。

## Open Questions

- 首版默认不设置自动过期，仅支持用户主动删除；上线前由运维确认备份周期和磁盘保留上限。
- 跨设备同步、账户归属和会话导出不阻断本次实现，待引入身份体系时另立变更。
