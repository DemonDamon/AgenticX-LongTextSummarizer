---
name: LongText Summarizer Overview
overview: 将 AgenticX-LongTextSummarizer 迁移为基于 AgenticX 框架的长文本摘要服务；复用 LlmFactory、Chunkers、TokenCounter、LLMJudge 等现有能力，分四阶段实施。
todos:
  - id: read-apis
    content: 实施前阅读本 plan「已核实真实 API」与「设计纠偏」章节
    status: completed
  - id: phase1
    content: "Phase 1: LlmFactory + FunctionTool + service 骨架（见 phase1 plan）"
    status: completed
  - id: phase2
    content: "Phase 2: Chunker + Map-Reduce 长文本摘要（见 phase2 plan）"
    status: completed
  - id: phase3
    content: "Phase 3: 邮件/新闻意图路由 + Token 溢出保护（见 phase3 plan）"
    status: completed
  - id: phase4
    content: "Phase 4: LLMJudge 自动化质量评估（见 phase4 plan）"
    status: completed
isProject: false
---

# AgenticX 长文本摘要服务 - 重构实施总览

**Author:** Damon Li
**Date:** 2026-06-17
**关联文档:** `examples/AgenticX-LongTextSummarizer/docs/agenticx_optimization_plan.md`
**Plan 目录:** `examples/AgenticX-LongTextSummarizer/plans/`

## 0. 阅读指引（给实施者 / Composer 2.5）

本 plan 将 optimization 文档的设计落地为**可执行的分阶段任务**。
核心原则：**复用 AgenticX 现有能力，不重复造轮子**。每个阶段独立可交付、独立可验收，按编号顺序实施。

实施前请务必先读本文件的「1. 已核实的真实 API」与「2. 设计纠偏」，避免引用不存在或被误解的接口。

### 阶段索引

| 阶段 | Plan 文件 | 目标 | 依赖 |
| :-- | :-- | :-- | :-- |
| Phase 1 | `2026-06-17-longtext-summarizer-phase1-foundation.plan.md` | 接入 `LlmFactory`，预处理封装为 `FunctionTool`，搭建新 service 骨架 | 无 |
| Phase 2 | `2026-06-17-longtext-summarizer-phase2-mapreduce.plan.md` | 引入 chunker + Map-Reduce 长文本摘要 | Phase 1 |
| Phase 3 | `2026-06-17-longtext-summarizer-phase3-routing-overflow.plan.md` | 邮件/新闻意图路由 + Token 溢出保护 | Phase 2 |
| Phase 4 | `2026-06-17-longtext-summarizer-phase4-evaluation.plan.md` | 用 `LLMJudge` 做自动化质量评估 | Phase 1-3 |

### 目录与命名约定

新增代码统一放在 `examples/AgenticX-LongTextSummarizer/agenticx_service/` 包内（与旧 `api_server.py` 并存，逐步替换）。
- 旧文件（`api_server.py` / `preprocessor.py` / `prompts.py` / `config.py`）**保留**，作为 Phase 1 迁移参照，不直接删除。
- 所有新文件遵循 `.cursor/rules/google-python-style.mdc`：英文注释/docstring、文件头含 `Author: Damon Li`、禁用相对导入（统一 `from agenticx...`）、代码内无 emoji。

## 1. 已核实的真实 API（实施时直接引用，已在仓库核对）

### 1.1 LLM 工厂与调用
```python
from agenticx.llms import LlmFactory
from agenticx.knowledge.graphers.config import LLMConfig  # 注意：LLMConfig 在此模块

config = LLMConfig(provider="litellm", model="...", api_key="...", base_url="...", temperature=0.7)
llm = LlmFactory.create_llm(config)            # -> BaseLLMProvider
resp = await llm.ainvoke(prompt_or_messages)   # -> LLMResponse；同步用 llm.invoke(...)
text = resp.content                             # LLMResponse.content 为字符串
```

### 1.2 分块（Chunkers）
```python
from agenticx.knowledge.chunkers import RecursiveChunker, AgenticChunker
from agenticx.knowledge.base import ChunkingConfig

cfg = ChunkingConfig(chunk_size=4000, chunk_overlap=200)
chunker = RecursiveChunker(cfg)
chunks = chunker.chunk_text(text)              # -> List[Dict]，每项含 'content' / 'metadata'
```
- 默认 `RecursiveChunker`（无额外 LLM 成本）；`AgenticChunker` 走异步 `chunk_document_async`，成本更高，配置开关启用。

### 1.3 预处理工具封装
```python
from agenticx.tools import FunctionTool, tool
```

### 1.4 Token 计数与截断
```python
from agenticx.core.token_counter import count_tokens, truncate_text
```

### 1.5 评估
```python
from agenticx.evaluation import LLMJudge, CompositeJudge
```

## 2. 设计纠偏（务必遵守）

1. **`OverflowRecoveryPipeline` 不是通用文本截断器** — 与 Agent compiler/EventLog 强耦合；本服务改用 `TokenCounter` + `truncate_text` + Map-Reduce 降级。
2. **并行 Map** 用 `asyncio.gather` + `llm.ainvoke`，加 `Semaphore` 限流；不依赖 `ParallelToolResult`。
3. **`WorkflowEngine` 为可选项** — Map-Reduce 用纯 async 函数即可。
4. **`LLMConfig` 导入路径是 `agenticx.knowledge.graphers.config`**，不是 `agenticx.core`。

## 3. 全局验收基线

- 每个 Phase 结束须 pytest 跑通该阶段冒烟测试。
- 不修改 `agenticx/` 框架源码；只在 example 目录内新增/调整。
- 新增依赖写入 `requirements.txt`，注明用途。

Made-with: Damon Li
