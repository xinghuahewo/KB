## ADDED Requirements

### Requirement: 回答内容必须端到端增量输出
当回答模型支持流式响应时，系统 MUST 从模型接收内容增量并在最终完成事件之前向前端发送多个答案增量；仅发送阶段状态并在最后一次性发送完整答案 MUST NOT 被标记为真实流式。

#### Scenario: 模型正常流式生成
- **WHEN** 模型在生成过程中返回多个内容增量
- **THEN** 后端 SHALL 在 `done` 之前发送对应的 `answer_delta`，前端 SHALL 按到达顺序逐步追加可见答案

#### Scenario: 模型不支持流式
- **WHEN** 当前 Provider 只能返回完整答案
- **THEN** 系统 SHALL 使用最终快照兼容完成，并 MUST 以 `stream_mode=buffered` 明确标记本轮并非真实流式

### Requirement: 流式协议具有有序且可恢复的事件契约
每个流式事件 MUST 包含同一请求内单调递增的 `sequence`；协议 SHALL 区分阶段、答案增量、引用增量、心跳、最终完成和错误事件，并 SHALL 以最终完成快照作为持久化权威结果。

#### Scenario: 正常事件序列
- **WHEN** 一轮问答从接收请求运行到持久化完成
- **THEN** 事件 SHALL 按 sequence 有序到达，`done` SHALL 位于所有答案和引用增量之后并包含完整最终快照

#### Scenario: 客户端收到重复事件
- **WHEN** 断线重试或恢复导致前端再次收到已处理的 sequence
- **THEN** 前端 SHALL 忽略重复事件，并 MUST NOT 重复追加文本或 citation

#### Scenario: 长阶段尚无答案增量
- **WHEN** 检索或模型首字等待超过心跳周期
- **THEN** 服务端 SHALL 发送心跳以保持连接，且心跳 MUST NOT 改变答案正文

### Requirement: 系统记录并展示各阶段权威耗时
后端 SHALL 使用单调时钟记录候选召回、证据精排、上下文组装、答案生成、持久化和总流程耗时，并 SHALL 同时记录模型首字耗时及从请求接受到首个可见答案的耗时；完成数据 SHALL 随助手消息持久化。

#### Scenario: 阶段正常完成
- **WHEN** 候选召回、精排、上下文组装或生成阶段完成
- **THEN** 对应完成事件 SHALL 包含非负 `duration_ms` 和请求累计 `elapsed_ms`

#### Scenario: 收到第一个可见答案增量
- **WHEN** 系统首次向前端发送非空可见答案
- **THEN** 系统 SHALL 记录 `model_ttft_ms` 和 `time_to_first_answer_ms`，并保证其不大于最终总耗时

#### Scenario: 重新打开历史会话
- **WHEN** 用户查看已经完成或停止的历史回答
- **THEN** 前端 SHALL 展示该轮持久化的阶段耗时和总耗时，而不是重新估算

### Requirement: 前端分离阶段进度与答案正文
前端 MUST NOT 再用“正在检索”或省略号覆盖助手答案字段；首字前 SHALL 展示阶段时间线，首个答案增量到达后 SHALL 立即展示正文并继续保留紧凑耗时状态。

#### Scenario: 生成首字之前
- **WHEN** 问答仍处于召回、精排、上下文组装或模型首字等待
- **THEN** 消息卡片 SHALL 展示当前阶段及实时经过时间，答案正文区域 SHALL 保持独立等待状态

#### Scenario: 答案正在生成
- **WHEN** 前端收到一个或多个 `answer_delta`
- **THEN** 消息卡片 SHALL 平滑追加正文，不得等待 `done` 才一次性显示完整答案

#### Scenario: 回答完成
- **WHEN** 前端收到最终完成事件
- **THEN** 消息 SHALL 使用最终快照校正本地增量，并展示召回、精排、首字、生成和总计耗时

### Requirement: 流式引用控制标记不得泄露到正文
服务端 SHALL 在增量流中识别受控 citation 标记，普通文本 SHALL 作为答案增量发送，完整且合法的 citation SHALL 作为引用增量发送；内部控制语法 MUST NOT 显示给用户。

#### Scenario: citation 标记位于单个上游分片
- **WHEN** 模型输出完整且允许的 citation 控制标记
- **THEN** 后端 SHALL 发送对应 `citation_delta`，且前端 SHALL 在当前位置渲染可点击引用

#### Scenario: citation 标记跨多个上游分片
- **WHEN** citation 控制标记被拆分在连续模型增量中
- **THEN** 后端 SHALL 缓冲到标记闭合后再校验和发送，正文 MUST NOT 出现半个控制标记

#### Scenario: citation 标记无效或未闭合
- **WHEN** 标记不在允许列表中或流结束时仍未闭合
- **THEN** 系统 MUST NOT 将其渲染为可点击证据，并 SHALL 在最终引用状态中记录不完整或无效

### Requirement: 停止和异常保留已经生成的内容
用户停止、连接中断或上游失败时，系统 SHALL 保留已经确认的可见答案、引用和已完成阶段耗时，并 SHALL 将消息标记为准确终态；系统 MUST NOT 用通用错误文案覆盖已生成正文。

#### Scenario: 用户在生成中停止
- **WHEN** 已产生部分答案后用户点击停止
- **THEN** 前端 SHALL 保留部分答案，消息 SHALL 标记为 `stopped`，后端 SHALL 持久化部分正文和已有 timings

#### Scenario: 连接意外中断
- **WHEN** 浏览器与服务端在生成中断开
- **THEN** 前端 SHALL 标记未确认状态并允许使用相同 `request_id` 恢复，恢复后以服务端最终快照为准

#### Scenario: 首字前发生错误
- **WHEN** 上游在任何答案增量之前失败
- **THEN** 系统 SHALL 展示已完成阶段耗时和明确错误，且 MUST NOT 显示空白的已回答状态

### Requirement: 增量渲染保持阅读和辅助技术稳定
前端 SHALL 合并短时间窗内的答案增量以限制渲染频率；只有用户仍位于对话底部附近时 SHALL 自动跟随输出，且辅助技术 MUST NOT 被逐 token 播报淹没。

#### Scenario: 模型快速返回大量小增量
- **WHEN** 多个增量在一个渲染帧或短时间窗内到达
- **THEN** 前端 SHALL 批量更新正文，同时保持字符顺序和最终内容一致

#### Scenario: 用户在生成中向上阅读
- **WHEN** 用户主动滚离消息列表底部
- **THEN** 前端 MUST 停止强制自动滚动，并 SHALL 提供返回最新内容的入口

#### Scenario: 使用屏幕阅读器
- **WHEN** 答案持续生成
- **THEN** 系统 SHALL 只播报重要阶段变化和完成状态，不得逐 token 触发 `aria-live`
