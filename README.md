# AgenticX-LongTextSummarizer

AgenticX-LongTextSummarizer 是一个基于 [AgenticX](https://github.com/DemonDamon/AgenticX) 框架构建的**智能长文本摘要服务**。

该项目从早期的「富邮件摘要 API」重构而来，现已升级为**业务无关的摘要内核**，通过**可插拔的领域插件（Domain Plugins）**无缝支持邮件、新闻等多种业务场景，并具备多模态接入、大批量并发处理以及跨文档摘要等企业级能力。

---

## 🌟 核心特性与技术亮点

本项目充分利用了 AgenticX 框架的底层能力，解决了传统大模型直接调用时的 Token 限制和“Lost in the Middle”问题：

- 🧩 **业务无关内核与领域插件化**
  - 核心引擎（`SummarizationEngine`）与具体业务解耦。
  - 邮件（Email）和新闻（News）等场景作为独立的 `DomainPlugin` 接入，各自维护规则引擎和 Prompt 策略。
- ✂️ **智能分块与 Map-Reduce 并行处理**
  - 内置 `AgenticChunker` 与 `RecursiveChunker`，自动对超长文本进行语义分块。
  - 基于 Map-Reduce 架构，并行生成局部摘要后全局聚合，轻松应对万字长文。
- 🛡️ **多级 Token 溢出恢复 (Overflow Guard)**
  - 内置资源评估（`ResourceEstimator`）与溢出保护（`OverflowGuard`）。
  - 当输入超过模型安全上下文时，自动触发 L1-L3 多级截断或紧急压缩策略，避免系统崩溃。
- 🖼️ **多模态接入支持**
  - 通过 `ModalityAdapter` 矩阵，支持文本、代码、文档等多种模态输入（预留音视频接口）。
- 📚 **多文档跨篇摘要 (Multi-doc Collection)**
  - 支持对多篇独立文档进行单篇摘要后，执行聚合（Aggregate）、对比（Compare）或时间线（Timeline）分析。
- 🧠 **个性化 Prompt 记忆注入**
  - `PersonalizationStore` 记录用户反馈与偏好，在运行时动态注入 Prompt，实现“越用越懂你”的摘要体验。

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

# 如果需要运行核心 AgenticX 框架，请确保已安装 AgenticX
# pip install -e path/to/AgenticX
```

### 4. 配置环境变量
修改或创建配置文件（默认读取 `config_agenticx.yaml`），并设置你的 LLM API Key：
```bash
export AGX_LLM_API_KEY="your-llm-api-key"
```

---

## 📖 使用示例

### 启动 API 服务
项目基于 FastAPI 构建，可以直接启动服务：
```bash
uvicorn agenticx_service.app:app --host 0.0.0.0 --port 8282 --reload
```

### API 调用示例

#### 1. 基础单篇长文本摘要 (v2 API)
自动根据文本内容路由到邮件或新闻领域，并执行智能分块与 Map-Reduce。
```bash
curl -X POST http://localhost:8282/v2/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这里是一段非常长的文本内容，可能是几千字的会议记录或新闻报道...",
    "domain": "email",
    "user_id": "user_123"
  }'
```

#### 2. 多文档聚合摘要
对多份文档进行综合对比或聚合。
```bash
curl -X POST http://localhost:8282/v2/collection \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "compare",
    "docs": [
      {"doc_id": "doc1", "title": "竞品A分析报告", "content": "竞品A的优势在于..."},
      {"doc_id": "doc2", "title": "竞品B分析报告", "content": "竞品B的价格策略是..."}
    ]
  }'
```

#### 3. 提交用户个性化偏好
让系统记住你的摘要风格。
```bash
curl -X POST http://localhost:8282/v2/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "domain": "email",
    "instruction": "以后的邮件摘要请严格控制在50字以内，并且不要使用敬语。"
  }'
```

---

## 📄 演进规划与技术文档

本项目详细的架构重构思路、长文本优化策略以及测试方案，请参阅：
- [AgenticX 长文本摘要优化技术方案](docs/agenticx_optimization_plan.md)
- 更多重构设计请查看 `plans/` 目录下的设计文档。

---

## 🤝 贡献与反馈
欢迎提交 Issue 或 Pull Request 参与共建。

## 📜 许可证
MIT License
