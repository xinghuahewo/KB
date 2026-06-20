# 阶段 4.2 DeepSeek 冒烟测试报告

## 摘要

- 生成时间：2026-06-20T11:38:24
- DeepSeek API key 配置：是
- 密钥记录：未写入报告、数据集或仓库。
- 查询数：3
- 状态分布：{"answered": 2, "no_evidence": 1}

## 约束确认

- 当前设备不运行本地模型。
- 只读调用已发布知识库与 RAG Answer 编排。
- 无引用证据时拒绝生成答案。
- LLM 不可用时保留检索证据，不编造答案。
- `DEEPSEEK_API_KEY` 只从环境变量读取。

## 查询结果

| 查询 | 状态 | generated | 引用数 | 命中数 | 错误码 |
| --- | --- | --- | ---: | ---: | --- |
| route leak | answered | 是 | 3 | 3 |  |
| 路由泄露 | answered | 是 | 3 | 3 |  |
| zzzzqqqxxxx | no_evidence | 否 | 0 | 0 |  |

## 答案预览

### route leak

- 状态：answered
- 模型：deepseek / deepseek-chat
- 引用数：3

根据现有证据，**BGP route leak（路由泄露）** 是一种BGP异常，指某个行为不当的自治系统（AS）违反预期策略，将BGP通告传播给另一个AS，导致流量通过非预期链路转发。该定义基于Gao-Rexford模型描述的互联网商业关系（如客户-提供商、对等关系）[chunk_id: beam_2024_s004_page_4_002]。

此外，证据中通过示意图对比了BGP路由泄露与BGP劫持的区别：路由泄露中，泄露者（leaker）将本应仅向特定邻居通告的路由错误地

### 路由泄露

- 状态：answered
- 模型：deepseek / deepseek-chat
- 引用数：3

根据现有证据，**路由泄露（BGP route leak）** 是一种BGP路由异常事件，其定义和分类可参考RFC 7908（由K. Sriram等人于2016年发布）[chunk_id: beam_2024_s017_page_17_003]。在研究中，路由泄露常与BGP劫持（BGP hijack）并列作为典型的BGP安全事件类型，例如在合成数据集中，17个BGP劫持事件和17个BGP路由泄露事件被用于评估异常检测方法[chunk_id: bear_2025_s006_pa

### zzzzqqqxxxx

- 状态：no_evidence
- 模型：none / 
- 引用数：0

无生成答案。
