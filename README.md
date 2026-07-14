# AgenticX-LongTextSummarizer

AgenticX-LongTextSummarizer 是一个基于 [AgenticX](https://github.com/DemonDamon/AgenticX) 框架构建的**智能长文本摘要服务**。

该项目从早期的「富邮件摘要 API」重构而来，现已升级为**业务无关的摘要内核**，通过**可插拔的领域插件（Domain Plugins）**无缝支持邮件、新闻等多种业务场景，并具备多模态接入、大批量并发处理以及跨文档摘要等企业级能力。

---

## 🌟 核心特性与技术亮点

本项目充分利用了 AgenticX 框架的底层能力，解决了传统大模型直接调用时的 Token 限制和"Lost in the Middle"问题：

- 🧩 **业务无关内核与领域插件化**：核心引擎（`SummarizationEngine`）与具体业务解耦，邮件（Email）和新闻（News）等场景作为独立的 `DomainPlugin` 接入，各自维护规则引擎和 Prompt 策略。
- ✂️ **智能分块与 Map-Reduce 并行处理**：内置 `AgenticChunker` 与 `RecursiveChunker`，自动对超长文本进行语义分块，基于 Map-Reduce 架构并行生成局部摘要后全局聚合，轻松应对万字长文。
- 🛡️ **多级 Token 溢出恢复 (Overflow Guard)**：内置资源评估（`ResourceEstimator`）与溢出保护（`OverflowGuard`），当输入超过模型安全上下文时，自动触发 L1-L3 多级截断或紧急压缩策略，避免系统崩溃。
- 🖼️ **多模态接入支持**：通过 `ModalityAdapter` 矩阵，支持文本、代码、文档等多种模态输入（预留音视频接口）。
- 📚 **多文档跨篇摘要 (Multi-doc Collection)**：支持对多篇独立文档进行单篇摘要后，执行聚合（Aggregate）、对比（Compare）或时间线（Timeline）分析。
- 🧠 **个性化 Prompt 记忆注入**：`PersonalizationStore` 记录用户反馈与偏好，在运行时动态注入 Prompt，实现"越用越懂你"的摘要体验。

---

## 🏗️ 架构概览

```text
agenticx_service/
├── core/                     # 业务无关摘要内核 (Engine, Pipeline, PromptResolver)
├── domains/                  # 可插拔领域插件 (Email, News 及规则引擎)
├── modality/                 # 多模态接入边界 (Text, Code, Document)
├── batch/                    # 批处理、资源评估与队列降级 (Resource, Queue)
├── multidoc/                 # 多篇长文档跨篇摘要 (Collection)
├── agentic/                  # 个性化记忆注入与动态 Prompt 生命周期
└── tools/                    # 工具层（如脱敏工具 desensitize）
```

---

## 🚀 安装指南

### 1. 环境要求

- Python 3.10+
- 推荐使用 `conda` 或 `venv` 创建虚拟环境。

### 2. 克隆仓库

```bash
git clone https://github.com/DemonDamon/AgenticX-LongTextSummarizer.git
cd AgenticX-LongTextSummarizer
```

### 3. 安装依赖

```bash
# 创建虚拟环境
conda create -n agenticx-summarizer python=3.10
conda activate agenticx-summarizer

# 安装项目依赖
pip install -r requirements.txt

# 安装核心 AgenticX 框架（开发模式）
pip install -e path/to/AgenticX
```

### 4. 配置环境变量

修改配置文件（默认读取 `config_agenticx.yaml`），并设置 LLM API Key：

```bash
export AGX_LLM_API_KEY="your-llm-api-key"
```

---

## 📖 使用示例

### 启动 API 服务

```bash
uvicorn agenticx_service.app:app --host 0.0.0.0 --port 8282 --reload
```

### API 调用示例

#### 1. 基础单篇长文本摘要 (v2 API)

```bash
curl -X POST http://localhost:8282/v2/summarize \
  -H "Content-Type: application/json" \
  -d '{"content": "这里是一段非常长的文本...", "domain": "email", "user_id": "user_123"}'
```

#### 2. 多文档聚合摘要

```bash
curl -X POST http://localhost:8282/v2/collection \
  -H "Content-Type: application/json" \
  -d '{"intent": "compare", "docs": [{"doc_id": "doc1", "content": "..."}, {"doc_id": "doc2", "content": "..."}]}'
```

#### 3. 提交用户个性化偏好

```bash
curl -X POST http://localhost:8282/v2/feedback \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "domain": "email", "instruction": "摘要请严格控制在50字以内。"}'
```

---

## 📄 演进规划与技术文档

- [AgenticX 长文本摘要优化技术方案](docs/agenticx_optimization_plan.md)
- 分阶段实施记录见 `plans/` 目录。

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request 参与共建。

## 📜 许可证

MIT License
