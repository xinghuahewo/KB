## ADDED Requirements

### Requirement: 用户可以复制任一消息的可读内容
前端 SHALL 为用户消息和助手消息提供复制操作，并 SHALL 将渲染后的正文转换为保持段落、列表和可读引用编号的纯文本；复制内容 MUST NOT 包含内部 citation 标识、内部接口 URL 或隐藏证据上下文。

#### Scenario: 复制普通用户消息
- **WHEN** 用户点击某条用户消息的复制按钮
- **THEN** 剪贴板 SHALL 包含该条消息正文且不包含其他轮次内容

#### Scenario: 复制带行内引用的助手回答
- **WHEN** 用户复制包含可点击引用的助手回答
- **THEN** 剪贴板 SHALL 保留正文和 `[1]` 等可读引用编号，但 MUST NOT 包含内部 `citation_id`

### Requirement: 复制操作提供标准路径和兼容回退
前端 SHALL 优先使用标准 Clipboard API；当该 API 不存在、被拒绝或抛出异常时，系统 SHALL 尝试受控的文本选择回退，并 SHALL 捕获所有失败。

#### Scenario: Clipboard API 成功
- **WHEN** 浏览器允许 `navigator.clipboard.writeText`
- **THEN** 系统 SHALL 复制目标文本且不得执行回退路径

#### Scenario: Clipboard API 不可用
- **WHEN** 页面处于不支持 Clipboard API 的环境或权限被拒绝
- **THEN** 系统 SHALL 尝试兼容回退、清理临时 DOM 和选区，并返回明确结果

#### Scenario: 所有复制路径失败
- **WHEN** 标准路径和兼容回退均失败
- **THEN** 系统 SHALL 显示复制失败且 MUST NOT 产生未处理异常

### Requirement: 复制结果具有可见和可访问反馈
复制按钮 SHALL 在操作后展示短时成功或失败状态，并 SHALL 通过 `aria-live` 或等效机制向辅助技术播报结果；按钮在键盘操作时 SHALL 具有可见焦点。

#### Scenario: 复制成功反馈
- **WHEN** 任一复制路径成功
- **THEN** 当前消息 SHALL 显示“已复制”反馈并在合理时间后恢复默认状态

#### Scenario: 键盘触发复制
- **WHEN** 键盘用户聚焦复制按钮并激活它
- **THEN** 系统 SHALL 执行与指针点击相同的复制和反馈流程

### Requirement: 复制不得改变会话状态
复制操作 MUST NOT 创建消息、触发检索、修改证据选择或写入新的会话轮次。

#### Scenario: 复制历史回答
- **WHEN** 用户复制非当前轮次的历史回答
- **THEN** 会话消息、当前证据轮次和后端历史 SHALL 保持不变
