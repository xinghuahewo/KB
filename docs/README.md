# 项目文档

本目录只保留长期有效、能够支持开发、部署、回滚和审计的文档。

1. [架构](architecture.md)：系统边界、模块方向和数据流。
2. [RAG 五阶段流水线](pipeline.md)：候选构建、checkpoint、制品闭包、验证、迁移与成对回滚。
3. [数据与制品](data-artifacts.md)：数据根目录、release、校验与回滚约束。
4. [会话、流式回答与证据接口](conversation-evidence-api.md)：会话 API、SSE 事件、耗时和消息内证据读取契约。
5. [运维与部署](operations.md)：服务器、端口、screen、巡检、会话备份和故障处理。
6. [工程治理](governance.md)：分支、PR、CI、Git 与文档规则。
7. [里程碑](milestones.md)：已完成能力与当前重构状态。
8. [架构决策](adr/README.md)：关键取舍及其后果。
9. [RAG 证据流水线 v2 迁移基线](baselines/rag-evidence-pipeline-v2.md)：代码、制品、语料和评测的冻结比较点。

历史阶段计划不再作为活文档维护。其归宿记录在[历史文档映射](archive-map.md)，具体内容可由 Git 历史和归档 OpenSpec change 追溯。
