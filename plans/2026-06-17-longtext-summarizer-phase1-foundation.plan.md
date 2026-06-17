---
name: LongText Summarizer Phase 1
overview: 接入 LlmFactory、脱敏封装 FunctionTool、搭建 agenticx_service 骨架，跑通短文本单块摘要端到端。
todos:
  - id: t1-config
    content: T1.1 配置模型 agenticx_service/config.py（LLMSettings + to_llm_config）
    status: completed
  - id: t1-llm
    content: T1.2 LLM 客户端 agenticx_service/llm_client.py（LlmFactory + ainvoke）
    status: completed
  - id: t1-desensitize
    content: T1.3 脱敏工具 agenticx_service/tools/desensitize.py（@tool + mask_pii）
    status: completed
  - id: t1-prompts
    content: T1.4 Prompt 注册表 agenticx_service/prompts/（迁移 v4 模板）
    status: completed
  - id: t1-summarizer
    content: T1.5 单块摘要编排 agenticx_service/summarizer.py
    status: completed
  - id: t1-app
    content: T1.6 新 Sanic 入口 agenticx_service/app.py（兼容旧 API 形状）
    status: completed
  - id: t1-tests
    content: T1.7 冒烟测试 test_phase1_smoke.py + README 启动说明
    status: completed
isProject: false
---

# Phase 1 - 基础集成（LlmFactory + FunctionTool + Service 骨架）

**Author:** Damon Li
**Date:** 2026-06-17
**前置:** 先读 `2026-06-17-longtext-summarizer-overview.plan.md` 的「真实 API」与「设计纠偏」。
## 目标

把旧 `EmailAbstraction` 的「正则脱敏 -> 拼 Prompt -> requests 调 LLM -> 解析 JSON」流程，
迁移为基于 AgenticX 抽象的可扩展骨架：
- LLM 调用统一走 `LlmFactory` + `BaseLLMProvider.ainvoke`，剥离硬编码 `requests`。
- 脱敏逻辑封装为 `FunctionTool`。
- 引入结构化配置与可切换模型，跑通**短文本（单块）摘要**端到端。

本阶段**不引入分块**，只保证「短邮件」基线链路可用。

## 新增/变更文件

```
examples/AgenticX-LongTextSummarizer/agenticx_service/
  __init__.py
  config.py
  llm_client.py
  tools/desensitize.py
  prompts/registry.py + templates.yaml
  summarizer.py
  app.py
config_agenticx.yaml
```

## 验收标准

1. 启动 `python -m agenticx_service.app`，POST 短邮件，返回结构与旧服务一致且摘要非空。
2. 切换 `config_agenticx.yaml` 中 `model`/`provider` 即可换模型，无需改代码。
3. PII 脱敏在进入 LLM 前生效。
4. 冒烟测试全绿；未触碰 `agenticx/` 框架源码。

Made-with: Damon Li
