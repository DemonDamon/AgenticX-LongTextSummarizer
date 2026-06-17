# 基于 AgenticX 的长文本摘要（邮件/新闻）优化技术方案

**Author:** Damon Li
**Date:** 2026-06-17

## 1. 背景与现状分析

在深入分析 `AgenticX-EmailAbstraction` 仓库后，我们发现其当前实现是一个基于 Sanic 的轻量级 API 服务，核心流程为：接收文本 -> 正则脱敏 -> 组装 Prompt -> `requests` 直接调用 LLM API -> 解析 JSON 返回。

虽然该服务能满足基本的短邮件摘要需求，但在面对复杂的企业级应用场景时，暴露出以下局限性：
- **缺乏长文本处理机制：** 未引入 Chunking（分块）策略，当处理长篇邮件链或长篇新闻报道时，极易触发 LLM 的 Token 限制，或引发"Lost in the Middle"（中间注意力丢失）问题。
- **架构耦合度高：** 预处理逻辑与 API 服务硬编码绑定，LLM 调用未经过抽象层封装，难以无缝切换底层模型。
- **上下文无状态：** 服务缺乏记忆机制，无法支持多轮追问（例如用户要求"详细展开第二点的待回复内容"）。
- **缺乏异常恢复：** 遇到超长文本或模型报错时，缺乏 Token 溢出恢复和 Fallback 机制。

幸运的是，强大的 `AgenticX` 框架内置了丰富的组件。本方案旨在将 `EmailAbstraction` 服务全面迁移至 `AgenticX` 架构，利用其智能分块、分层记忆、工作流引擎等高级特性，打造一个鲁棒、可扩展的**智能长文本摘要服务**。

## 2. 优化架构设计

我们将基于 `AgenticX` 框架的核心组件，对原有服务进行彻底重构。整体架构分为接入层、工作流层、核心处理层和基础设施层。

### 2.1 核心组件映射与升级

| 原有实现 (`EmailAbstraction`) | AgenticX 框架替代方案 | 优势说明 |
| :--- | :--- | :--- |
| `requests.post` 直接调用 | `agenticx.llms.llm_factory.LlmFactory` | 支持 LiteLLM 等多模型无缝切换，自带重试机制。 |
| `preprocessor.py` (正则) | 封装为 `FunctionTool` (`agenticx.tools.function_tool`) | 统一工具接口，支持被 Agent 灵活调用或编排入工作流。 |
| 无分块机制 | `agenticx.knowledge.chunkers.AgenticChunker` | 基于 LLM 智能寻找自然断点，保证语义连贯。 |
| 简单 Prompt 模板 | `agenticx.core.prompt.PromptManager` | 支持动态上下文渲染和 XML 结构化高密度信息呈现。 |
| 报错直接返回空 | `agenticx.core.overflow_recovery.OverflowRecoveryPipeline` | 提供 L1-L3 多级 Token 溢出恢复机制。 |

### 2.2 摘要处理工作流设计 (Map-Reduce 模式)

针对长文本，我们设计了基于 Map-Reduce 的工作流（可利用 `agenticx.core.workflow` 实现）：

1. **输入与意图识别 (Intent Classification)：**
   - 接收文本后，首先通过简单的规则或轻量级 LLM 判断文本类型（邮件 Email vs 新闻 News）。
   - 不同类型将路由到不同的摘要 Prompt 模板。
2. **预处理 (Preprocessing Tool)：**
   - 调用原有的脱敏逻辑（已封装为 `BaseTool`），隐藏敏感信息（手机号、身份证等）。
3. **智能分块 (Chunking)：**
   - 调用 `AgenticChunker`，按语义段落将超长文本切分为多个 Chunk（控制在模型最佳上下文窗口内，如 4000 tokens）。
4. **并行子摘要 (Map Phase)：**
   - 利用 `AgenticX` 的并行执行能力（参考 `ParallelToolResult` 机制），对每个 Chunk 独立调用 LLM 生成子摘要。
5. **全局聚合 (Reduce Phase)：**
   - 将所有子摘要汇总，交给最终的 `ReActAgent` 或 `SummarizerAgent`，根据用户要求（如"100字以内"、"核心内容+待回复内容"）生成最终结果。

## 3. 场景适配与 Prompt 设计

不同的文本类型需要关注的信息维度不同，我们在方案中引入动态 Prompt 策略。

### 3.1 邮件场景 (Email)
继承并优化原有 `v4` 版本的逻辑，重点关注行动点。

**Reduce Prompt 示例：**
> 你是一个专业的邮件处理助手。请根据以下从长邮件中提取的各个片段摘要，生成一份最终的全局摘要。
> 要求：
> 1. 字数控制在 100 字以内。
> 2. 【核心内容】：用两句话概括邮件的最核心事件或决策。
> 3. 【需要回复内容】：列出需要我（收件人）明确回复、确认或执行的行动点（Action Items）。如果没有，请忽略此项。

### 3.2 新闻场景 (News)
新闻场景通常较长，且包含大量背景信息，重点在于提取事实要素。

**Reduce Prompt 示例：**
> 你是一个资深的新闻编辑。请根据以下从长篇报道中提取的片段摘要，生成一份精炼的新闻简报。
> 要求：
> 1. 提炼出核心的 5W1H（时间、地点、人物、事件、原因、过程）。
> 2. 总结出文章的核心观点或结论。
> 3. 保持客观中立，语言精炼，适合快速阅读。

## 4. 测试方案设计

为了验证重构后的系统在处理长文本时的稳定性与准确性，我们设计了以下测试用例：

### 4.1 邮件场景测试
- **测试用例 1：短邮件（Baseline）**
  - **输入：** 日常会议通知（约 200 字）。
  - **预期：** 快速返回，准确提取会议时间和需要确认是否参会的行动点。验证预处理正则（如屏蔽手机号）是否正常工作。
- **测试用例 2：超长跨国项目讨论邮件链（Lost in the Middle 测试）**
  - **输入：** 包含 10 次以上往复回复、夹杂大量技术细节和不同人员意见的邮件链（约 8000 字）。
  - **预期：** 触发 `AgenticChunker`，成功执行 Map-Reduce。最终摘要必须能准确捕捉到邮件链**开头**提出的问题以及**结尾**达成的最终结论，且明确列出当前需要用户推进的最终 Action Item。

### 4.2 新闻场景测试
- **测试用例 3：长篇深度调查报道**
  - **输入：** 一篇关于行业趋势的万字深度分析文章。
  - **预期：** 触发智能分块。能够准确提炼出文章的核心论点和主要论据，没有遗漏关键事实。
- **测试用例 4：极端边界测试（Token 溢出恢复）**
  - **输入：** 构造一篇极长（超过模型上下文限制）的无意义或重复文本。
  - **预期：** 触发 `OverflowRecoveryPipeline`，系统不会崩溃抛出 500 错误，而是通过截断或紧急压缩策略（Emergency Compaction）返回部分摘要或合理的错误提示。

## 5. 实施路径规划

1. **Phase 1：基础集成。** 在 AgenticX 框架中创建新的 `EmailAbstraction` 模块，接入 `LlmFactory`，将原有正则逻辑封装为 `FunctionTool`。
2. **Phase 2：长文本处理。** 引入 `AgenticChunker` 和 Map-Reduce 工作流，实现基础的长文本摘要能力。
3. **Phase 3：场景扩展与优化。** 增加新闻场景的 Prompt 模板和意图识别路由，引入 Token 溢出保护机制。
4. **Phase 4：测试与评估。** 使用 `agenticx.evaluation` 模块中的 `LLMJudge` 对生成的摘要质量进行自动化评估，跑通上述测试用例。
