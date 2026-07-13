## ADDED Requirements

### Requirement: 系统使用锁定的私有 Docling 运行环境
系统 SHALL 在 Linux GPU 容器中运行 Docling，镜像、Python 依赖、Docling、CUDA 和模型文件 MUST 使用可验证版本或摘要锁定。

#### Scenario: 构建私有运行镜像
- **WHEN** 运维构建 Docling 清洗镜像
- **THEN** 系统 SHALL 生成镜像 digest、依赖锁、模型 manifest、模型 SHA-256 和许可证清单

### Requirement: 生产运行禁止联网下载
生产运行 MUST NOT 访问外网或自动下载依赖、模型和配置；缺少锁定资产时 MUST 失败关闭。

#### Scenario: 模型文件缺失
- **WHEN** 生产批处理启动时锁定模型不存在或 hash 不匹配
- **THEN** 系统 SHALL 在读取语料前失败并报告缺失资产，且 MUST NOT 尝试联网下载

### Requirement: 系统记录运行环境证据
每次批处理 SHALL 记录镜像、Docling、模型、配置、GPU、驱动、CUDA 和推理精度信息。

#### Scenario: 运行环境被审计
- **WHEN** 操作者查看任一 cleaning run
- **THEN** run 记录 SHALL 足以复现该批次使用的运行环境和模型组合

### Requirement: 运行面仅提供批处理命令
本阶段 SHALL 提供容器批处理命令和健康预检，MUST NOT 新增 HTTP API 或常驻外部服务。

#### Scenario: 启动清洗任务
- **WHEN** 操作者运行容器清洗命令
- **THEN** 系统 SHALL 通过挂载输入输出目录执行批处理，且不要求启动 API 服务
