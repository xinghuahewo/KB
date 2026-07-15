## ADDED Requirements

### Requirement: 系统使用版本化来源注册表
系统 SHALL 使用版本化、Schema 校验的来源注册表声明每个逻辑来源；记录 MUST 包含稳定 source_id、获取方式、来源类型、权威组织、语言、许可证状态和预期内容类型，来源采集器 MUST NOT 再以代码内硬编码列表作为权威输入。

#### Scenario: 操作者登记新的远端来源
- **WHEN** 操作者向来源注册表加入满足 Schema 的新来源
- **THEN** 下一次来源采集 SHALL 从注册表发现该来源并在运行 manifest 中记录所用注册表版本

#### Scenario: 来源缺少许可证状态
- **WHEN** 来源记录未声明许可证或明确的 unknown 状态
- **THEN** 注册表校验 MUST 失败且不得开始该来源的生产采集

### Requirement: 原始内容采用不可变内容寻址快照
系统 MUST 按响应或本地文件内容的 SHA-256 保存 raw object，并生成引用该对象的 source snapshot；相同 digest MUST 复用既有对象，不同 digest MUST 生成新 snapshot，系统 MUST NOT 原地覆盖已经被 release 引用的 raw object。

#### Scenario: 同一 URL 返回新内容
- **WHEN** 已登记 URL 的新抓取内容 SHA-256 与当前 snapshot 不同
- **THEN** 系统 SHALL 保存新对象和新 snapshot，并保留旧 snapshot 可供历史 release 回溯

#### Scenario: 重复导入相同内容
- **WHEN** 本地导入或远端抓取的内容 SHA-256 已存在
- **THEN** 系统 SHALL 复用对象并生成确定性的 snapshot 引用，不得复制对象本体

### Requirement: 快照记录完整获取与来源元数据
每个 source snapshot MUST 记录 source_id、snapshot_id、内容 SHA-256、字节数、MIME、获取时间、获取状态、原始 URL 或受控本地标识；远端 HTTP 来源还 SHALL 记录可用的 ETag、Last-Modified 和 HTTP 状态，且不得记录密钥、cookie 或授权头。

#### Scenario: 服务器未返回条件请求元数据
- **WHEN** HTTP 响应没有 ETag 或 Last-Modified
- **THEN** 系统 SHALL 以显式 null/unknown 记录缺失值并仍以内容 SHA-256 判定版本

### Requirement: 来源采集可审计且失败隔离
来源采集 SHALL 为每个来源产生终态和错误诊断，单个来源失败 MUST NOT 覆盖其既有成功 snapshot；生产阶段只有满足注册表、快照和许可证策略的来源集合才能进入 canonicalize。

#### Scenario: 某个远端来源暂时不可用
- **WHEN** 抓取发生超时或 HTTP 失败
- **THEN** 该来源 SHALL 标记为失败并保留既有 snapshot，其他来源 SHALL 继续处理，候选 release 是否可继续由版本化缺失策略决定

#### Scenario: 从现有 raw 目录首次迁移
- **WHEN** 操作者执行 legacy raw import
- **THEN** 系统 SHALL 在不重新下载和不修改原文件的前提下计算 hash、建立对象与 snapshot，并输出逐来源迁移清单
