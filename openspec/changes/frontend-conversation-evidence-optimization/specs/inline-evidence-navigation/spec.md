## ADDED Requirements

### Requirement: 回答中的行内引用具有稳定且受验证的证据映射
已回答消息 SHALL 返回结构化回答片段和本轮 citation 映射；每个可点击引用 MUST 映射到同一助手消息的一个或多个允许 citation，且 citation SHALL 包含稳定标识、`chunk_id`、来源标识、章节信息和完整句边界内的可见摘录。

#### Scenario: 模型返回合法引用
- **WHEN** 回答使用本轮允许列表中的 citation 标识
- **THEN** 后端 SHALL 将其转换为结构化引用片段，前端 SHALL 显示可点击编号

#### Scenario: 模型返回未知引用
- **WHEN** 回答包含不属于本轮允许列表的引用标识
- **THEN** 系统 MUST NOT 把该标识渲染为可点击证据，并 SHALL 在响应元数据中记录引用不完整状态

### Requirement: 点击行内引用只打开所属轮次的本轮证据
前端 SHALL 将引用所属的助手消息设为当前证据轮次，打开“本轮证据”区域，展开对应文档并定位、突出目标 citation；该操作 MUST NOT 使用最新轮次的证据替代引用所属轮次。

#### Scenario: 点击当前轮次引用
- **WHEN** 用户点击当前助手回答中的引用编号
- **THEN** 证据面板 SHALL 展示当前轮证据并把目标 citation 滚动到可见区域

#### Scenario: 点击历史轮次引用
- **WHEN** 用户点击较早助手回答中的引用编号
- **THEN** 证据面板 SHALL 切换到该历史轮次并定位其 citation，且不得显示较新回答的 citation

#### Scenario: 移动端点击引用
- **WHEN** 用户在窄屏设备点击引用编号
- **THEN** 系统 SHALL 打开“本轮证据”抽屉并定位相同 citation

### Requirement: 证据面板按需展示文档内容和相关上下文
系统 SHALL 在用户打开或定位 citation 时按需读取其相关章节，展示未被任意字符数截断的完整句子，并突出目标 chunk；用户 SHALL 能继续加载该来源的分页或分章节完整文档内容。

#### Scenario: 首次打开引用
- **WHEN** 目标 citation 的文档正文尚未加载
- **THEN** 前端 SHALL 请求该消息作用域内的证据详情，显示加载状态，并在成功后展开相关章节和高亮目标 chunk

#### Scenario: 查看完整文档
- **WHEN** 用户在证据卡片中选择查看完整文档
- **THEN** 系统 SHALL 按页或 section 加载受控文档内容，而不是把整篇文档预装进初始问答响应

#### Scenario: 摘录跨越预览边界
- **WHEN** 支持答案的术语位于旧预览截断位置之后
- **THEN** 面板 SHALL 显示包含该术语的完整句子，不得在句中以固定字符数硬截断

### Requirement: 证据内容读取受消息作用域和发布目录约束
证据详情接口 MUST 仅接受已属于目标助手消息的 citation 标识，并 MUST 通过已发布的来源、章节和 chunk 标识读取内容；接口 MUST NOT 接受任意文件路径或返回本机路径。

#### Scenario: 请求属于该消息的 citation
- **WHEN** 客户端请求的 citation 已持久化在目标助手消息下
- **THEN** 系统 SHALL 返回其证据快照和允许读取的相关文档内容

#### Scenario: citation 属于其他轮次
- **WHEN** 客户端把另一条消息的 citation 标识用于当前消息证据接口
- **THEN** 系统 SHALL 返回未找到且 MUST NOT 返回其他轮次内容

#### Scenario: 请求尝试路径越界
- **WHEN** 请求参数包含文件路径或不能解析为已发布标识
- **THEN** 系统 SHALL 拒绝请求且 MUST NOT 读取发布根目录之外的文件

### Requirement: 历史证据保留生成时快照和发布版本
系统 SHALL 随助手消息保存 citation 摘录、上下文快照和知识库发布标识；当当前发布与生成时版本不一致时，面板 SHALL 优先保留快照并明确提示版本差异。

#### Scenario: 历史会话使用相同发布版本
- **WHEN** 用户打开历史引用且原发布仍为当前发布
- **THEN** 系统 SHALL 展示持久化快照并允许加载匹配的文档内容

#### Scenario: 知识库已经更新
- **WHEN** 历史引用的发布标识与当前知识库不同
- **THEN** 系统 SHALL 标明版本差异，继续展示原 citation 快照，且 MUST NOT 静默用新内容替换原证据

### Requirement: 引用导航具备降级和可访问行为
引用组件 SHALL 支持键盘激活、可见焦点和描述性辅助文本；详情加载失败时 SHALL 保留已保存摘录、显示错误和重试入口，而不是清空整轮证据。

#### Scenario: 键盘打开引用
- **WHEN** 键盘用户聚焦引用编号并激活它
- **THEN** 系统 SHALL 打开对应证据、移动到合理焦点位置并保留可返回回答的操作路径

#### Scenario: 文档详情加载失败
- **WHEN** 证据详情接口超时或返回错误
- **THEN** 面板 SHALL 继续显示 citation 快照、明确失败原因并允许重试
