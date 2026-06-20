# 阶段 4.5 BGE-M3 混合检索实施计划

> **给后续执行代理：** 建议使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 按任务执行。步骤使用复选框语法，便于逐项跟踪。

**目标：** 接入 BGE-M3 远程 embedding，并实现 BM25/关键词、向量、元数据过滤和 RRF 融合的混合检索较优解 v1。

**架构：** 保留现有只读 FastAPI 和 RAG Answer API。新增远程 embedding provider、文件化向量索引、混合检索模块和检索评测脚本；DeepSeek 仍只负责基于 context pack 生成答案。

**技术栈：** Python 3、标准库 `urllib.request`、FastAPI、pytest、JSONL、SiliconFlow `BAAI/bge-m3`、阿里云 PAI/EAS BGE-M3、DeepSeek API。

---

### 任务 1：合并阶段 4.4 并创建阶段 4.5 分支

**文件：**
- 修改：仅 Git 分支

- [ ] 确认 `codex/phase-4-4-deepseek-eval-analysis` 工作区干净。
- [ ] 切到 `main` 并快进合并阶段 4.4。
- [ ] 推送 `main`。
- [ ] 新建 `codex/phase-4-5-bge-m3-hybrid`。
- [ ] 运行 `python3 -m pytest -v` 确认基线未破坏。

### 任务 2：配置 BGE-M3 远程 provider 边界

**文件：**
- 修改：`config/rag_retrieval.yaml`
- 测试：`tests/test_embedding_provider.py`

- [ ] 写失败测试：默认不运行本地模型，`siliconflow_bge_m3` 和 `aliyun_eas_bge_m3` 只读取环境变量。
- [ ] 写失败测试：无 `SILICONFLOW_API_KEY`、`ALIYUN_BGE_M3_ENDPOINT` 或 `ALIYUN_BGE_M3_API_KEY` 时真实 provider 标记为 unavailable。
- [ ] 实现配置字段：provider、model_name、base_url_env、endpoint_env、api_key_env、timeout_seconds、batch_size、enabled。
- [ ] 默认 provider 设为 `siliconflow_bge_m3`，模型为 `BAAI/bge-m3`。
- [ ] 运行 `python3 -m pytest tests/test_embedding_provider.py -v`。

### 任务 3：实现 BGE-M3 远程客户端

**文件：**
- 新建：`service/bge_m3_remote_client.py`
- 测试：`tests/test_bge_m3_remote_client.py`

- [ ] 写失败测试：SiliconFlow payload 使用 `model=BAAI/bge-m3` 和 `input`。
- [ ] 写失败测试：阿里云 PAI/EAS payload 可通过配置适配。
- [ ] 写失败测试：真实 key 不会出现在异常、报告或 repr 中。
- [ ] 写失败测试：fake response 能解析为 `list[float]`。
- [ ] 实现 `BgeM3RemoteClient.embed_texts(texts: list[str])`。
- [ ] 运行 `python3 -m pytest tests/test_bge_m3_remote_client.py -v`。

### 任务 4：构建文件化 embedding index

**文件：**
- 新建：`scripts/build_bge_m3_index.py`
- 新建：`published/bge_m3_vector_index.jsonl`
- 新建：`published/bge_m3_embedding_manifest.json`
- 新建：`reports/bge_m3_embedding_report.md`
- 测试：`tests/test_build_bge_m3_index.py`

- [ ] 写失败测试：fake client 能生成 index、manifest 和中文报告。
- [ ] 写失败测试：无 key 时脚本跳过真实调用但返回结构化状态。
- [ ] 写失败测试：manifest 包含模型名、维度、输入数量、输入 hash 和生成时间。
- [ ] 实现分批 embedding、余弦归一化、JSONL 输出和报告。
- [ ] 运行 `python3 -m pytest tests/test_build_bge_m3_index.py -v`。

### 任务 5：实现混合检索排序

**文件：**
- 新建：`service/hybrid_retrieval.py`
- 修改：`service/retrieval_framework.py`
- 测试：`tests/test_hybrid_retrieval.py`

- [ ] 写失败测试：lexical 和 vector 结果通过 RRF 合并。
- [ ] 写失败测试：同一 `chunk_id` 去重并保留最高解释。
- [ ] 写失败测试：standards 查询加权 standards，事件查询加权 cases，方法查询加权 papers。
- [ ] 写失败测试：中文“路由泄露”扩展到 `route leak`。
- [ ] 实现 lexical score、vector score、metadata boost、fusion score 和 reason 输出。
- [ ] 运行 `python3 -m pytest tests/test_hybrid_retrieval.py -v`。

### 任务 6：接入查询脚本和 API

**文件：**
- 新建：`scripts/query_hybrid_rag.py`
- 修改：`service/app.py`
- 修改：`service/repository.py`
- 测试：`tests/test_service_api.py`

- [ ] 写失败测试：`GET /api/v1/hybrid/search` 返回融合排序结果。
- [ ] 写失败测试：`GET /api/v1/hybrid/context-pack` 返回可给 RAG Answer 使用的 context pack。
- [ ] 实现只读 API endpoint。
- [ ] 实现命令行查询脚本，支持 `--query`、`--top-k`、`--json`。
- [ ] 运行 `python3 -m pytest tests/test_service_api.py -v`。

### 任务 7：建立混合检索评测

**文件：**
- 新建：`datasets/hybrid_retrieval_eval_questions.jsonl`
- 新建：`scripts/run_hybrid_retrieval_eval.py`
- 新建：`datasets/hybrid_retrieval_eval_results.jsonl`
- 新建：`reports/hybrid_retrieval_eval_report.md`
- 测试：`tests/test_hybrid_retrieval_eval.py`

- [ ] 写失败测试：评测集字段完整、`question_id` 唯一。
- [ ] 写失败测试：recall@5、recall@8、MRR 和 source coverage 可计算。
- [ ] 写失败测试：无证据问题不应强行返回高置信 context。
- [ ] 实现中文评测报告，列出通过、失败和需人工复核问题。
- [ ] 运行 `python3 -m pytest tests/test_hybrid_retrieval_eval.py -v`。

### 任务 8：阶段验收与文档更新

**文件：**
- 修改：`config/stage_acceptance.yaml`
- 修改：`README.md`
- 修改：`docs/stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md`

- [ ] 新增 `phase_4_5_bge_m3_hybrid_retrieval_v1` 阶段验收项。
- [ ] README 增加 SiliconFlow BGE-M3 与阿里云 PAI/EAS BGE-M3 环境变量和运行命令。
- [ ] 阶段文档更新真实验收结果。
- [ ] 运行 `python3 scripts/run_stage_acceptance.py --stage phase_4_5_bge_m3_hybrid_retrieval_v1`。

### 任务 9：完整验证与提交

**文件：**
- 修改：仅在现有脚本生成报告时更新验证输出

- [ ] 运行 `python3 -m pytest -v`。
- [ ] 运行 `python3 scripts/run_pipeline.py`。
- [ ] 运行 `python3 scripts/build_artifact_manifest.py && python3 scripts/quality_check.py`。
- [ ] 运行 `git diff --check`。
- [ ] 运行密钥扫描，确认 DeepSeek、SiliconFlow 和阿里云真实 key 未落盘。
- [ ] 提交并推送阶段 4.5 分支。
