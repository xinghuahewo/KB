# 服务数据包规格

## Purpose

定义在线 serving 数据与治理数据分离、数据库原子构建、跨制品一致性和 reader 版本控制。

## Requirements

### Requirement: 在线 serving 数据与治理审计数据分离
系统 SHALL 生成最小 `serving.sqlite`，只包含在线检索、证据组装和必要知识查询所需的数据；人工复核工作簿、决策审计、历史 v1 evidence 和离线报告索引 MUST 位于独立 governance 制品，在线进程 MUST NOT 打开治理数据库。

#### Scenario: FastAPI 启动
- **WHEN** 服务加载已验证 release
- **THEN** 它 SHALL 只打开 serving bundle 和检索索引，并能够在 governance 制品不存在时提供完整在线问答

### Requirement: 数据库采用候选构建和原子替换
数据库构建器 MUST 写入同文件系统临时路径，完成 Schema version、foreign key check、integrity check、记录数和跨制品 ID 闭包校验后才能原子 rename；失败 MUST 保留上一完整数据库且不得暴露半写文件。

#### Scenario: 插入过程中发生异常
- **WHEN** serving 数据库尚未通过全部校验
- **THEN** 构建器 MUST 删除或隔离临时文件并保持既有候选输出不变

### Requirement: 同一 serving bundle 内的制品必须一致
release manifest MUST 绑定 source snapshot、Canonical manifest、chunk manifest、retrieval document manifest、SQLite、vector JSONL、fast matrix/metadata 和评测证据的 hash；运行适配器 MUST 拒绝跨 release 或 hash 不匹配的组合。

#### Scenario: SQLite 来自新 release 而快索引来自旧 release
- **WHEN** artifact verification 发现 manifest 或 chunk ID 集合不一致
- **THEN** release MUST 验证失败，FastAPI MUST NOT 以该组合启动

### Requirement: serving schema 显式版本化且兼容读取受控
serving bundle SHALL 声明 schema_version 和 minimum_reader_version；新 reader MAY 在显式 legacy 开关下读取受支持的旧 release，但 MUST 报告 legacy/degraded 状态，旧 reader MUST NOT 静默读取不兼容新 schema。

#### Scenario: reader 版本低于 release 要求
- **WHEN** minimum_reader_version 高于当前代码支持版本
- **THEN** 启动 MUST 失败并给出代码/制品版本不兼容诊断
