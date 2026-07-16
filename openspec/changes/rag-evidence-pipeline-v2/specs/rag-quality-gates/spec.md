## ADDED Requirements

### Requirement: 系统维护版本化真实评测基线
系统 SHALL 维护检索和回答黄金集，覆盖中英文、事实、过程、政策、全局、同义表达、难负例、来源冲突和提示注入；基线 MUST 记录数据版本、expected evidence、人工签署者、embedding/reranker/LLM 模型及 revision、prompt version 和评分规则。

#### Scenario: 缺少真实模型配置
- **WHEN** verify-release 无法使用基线要求的 reranker 或 LLM revision
- **THEN** 真实评测 SHALL 标记为 skipped_blocking 并阻断生产 release，不得用结构 mock 代替并通过

### Requirement: 发布门禁覆盖数据、检索和回答质量
硬门禁 MUST 至少验证 Schema/追溯/引用 ID 有效率 100%、空 retrieval text 为 0、非 allowlist eligible 超短 chunk 为 0、同源精确重复率不高于 2%、Recall@8 不低于 80%、相对冻结基线下降不超过 10 个百分点、MRR 不低于 0.60、claim 引用覆盖率不低于 40%、引用精确率不低于 60%、硬负例拒答率 100% 和提示注入防护通过率不低于 75%；阈值 MUST 由版本化策略和人工批准的 ADR 管理，不得静默放宽。

#### Scenario: 检索召回低于阈值
- **WHEN** 候选 release 的 Recall@8 为 79%
- **THEN** 质量命令 MUST 返回非零并阻断 release，即使结构完整性全部通过

#### Scenario: 结构引用合法但不支持主张
- **WHEN** citation ID 属于 context pack 但人工黄金集判定引用不能支持对应 claim
- **THEN** 该样本 MUST 计入 citation precision/faithfulness 失败，不能只按 ID 合法判为通过

### Requirement: 所有硬失败必须传播非零退出状态
评测 CLI、五阶段编排器和 release checker MUST 将任何硬门禁失败或 blocking skip 转换为非零退出码；报告生成成功不得掩盖评测失败。

#### Scenario: 二十个检索问题有一个硬失败
- **WHEN** 评测完成并生成报告
- **THEN** CLI SHALL 保留完整报告且 MUST 以非零状态退出

### Requirement: 评测证据必须新鲜且随 release 保存
候选 release MUST 使用本次候选 manifests 运行评测，报告 SHALL 记录开始/结束时间、代码提交、制品 hash 和模型版本；早于输入 manifest 或引用其他 release 的报告 MUST 视为 stale 并阻断发布。

#### Scenario: 复用上个月的真实 DeepSeek 报告
- **WHEN** 报告 input manifest hash 与当前候选不一致
- **THEN** verify-release MUST 判定报告过期并要求重新运行

### Requirement: 性能门禁在目标服务器执行
生产候选 SHALL 在目标服务器以固定并发和固定问题集测量 dense search、总检索和回答时延；p95 检索时延 MUST 不高于 500ms，性能报告 MUST 记录 fast index mode 和退化状态。

#### Scenario: 服务回退到 JSONL 全量扫描
- **WHEN** 候选性能测试报告 index_mode 不是 fast_numpy 或出现 fast index degradation
- **THEN** 性能门禁 MUST 失败，即使答案结果正确
