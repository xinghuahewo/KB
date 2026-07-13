# Resumable Cleaning Batches 规格

## Purpose

本规格定义文档级清洗批处理的可靠执行机制，通过显式状态机、处理指纹和断点续跑保证幂等恢复，通过失败隔离与有限重试保障批次推进，并保留审计和容量分析所需的运行指标。

## Requirements

### Requirement: 系统维护文档级批处理状态机
每篇文档 SHALL 按 discovered、preflighted、parsed、normalized、validated、approved 或 quarantined 状态推进，状态变化 MUST 记录 run_id、时间和原因。

#### Scenario: 单篇文档成功完成
- **WHEN** 文档通过全部解析、清洗和验证步骤
- **THEN** 状态 SHALL 按顺序推进到 approved，并登记全部输出摘要

### Requirement: 批处理必须幂等且可断点续跑
系统 SHALL 使用输入、镜像、模型和配置生成处理指纹；相同指纹的成功步骤 SHALL 被复用，操作者 SHALL 能从指定阶段恢复。

#### Scenario: 批次在中途重启
- **WHEN** 已有部分文档完成且处理指纹未变化
- **THEN** 系统 SHALL 跳过已成功步骤并继续未完成文档

#### Scenario: 清洗配置发生变化
- **WHEN** 配置版本改变导致处理指纹变化
- **THEN** 系统 SHALL 重新执行受影响阶段和下游阶段

### Requirement: 系统隔离失败并实施有限重试
单篇失败 MUST NOT 中止全批次；OOM、超时和暂态模型错误 SHALL 按配置有限重试，内容、Schema 和治理错误 SHALL 直接隔离。

#### Scenario: 单篇 PDF 损坏
- **WHEN** Docling 判定文档内容不可解析
- **THEN** 文档 SHALL 进入 quarantined，其他文档 SHALL 继续处理，错误与中间证据 SHALL 被保存

#### Scenario: GPU 暂态 OOM
- **WHEN** 文档触发可重试 OOM
- **THEN** 系统 SHALL 按资源降级策略有限重试，达到上限后隔离文档

### Requirement: 运行记录支持审计和容量分析
系统 SHALL 记录每篇文档耗时、页数、OCR 页数、GPU 峰值显存、重试、fallback 和输出计数，并汇总吞吐、p50/p95 时延和失败率。

#### Scenario: 批次完成
- **WHEN** 所有文档达到终态
- **THEN** 系统 SHALL 生成中文运行报告和机器可读 run/document status 数据集
