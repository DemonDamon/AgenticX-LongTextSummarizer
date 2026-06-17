---
name: LongText Summarizer Phase 4
overview: 用 LLMJudge/CompositeJudge 对摘要质量做自动化评估，固化 optimization_plan 四个测试用例为可重复评测集。
todos:
  - id: t4-judges
    content: T4.1 评委定义 evaluation/judges.py（faithfulness/conciseness + 场景维度）
    status: completed
  - id: t4-datasets
    content: T4.2 评测数据集 evaluation/datasets/*.json（4 个用例）
    status: completed
  - id: t4-runner
    content: T4.3 评测入口 evaluation/run_eval.py（json + markdown 报告）
    status: completed
  - id: t4-tests
    content: T4.4 冒烟测试 test_phase4_eval.py + README 评测说明
    status: completed
isProject: false
---

# Phase 4 - 自动化质量评估（LLMJudge）

**Author:** Damon Li
**Date:** 2026-06-17
**前置:** Phase 1-3 完成；先读 overview plan 评估 API。
## 目标

用 `agenticx.evaluation.LLMJudge` / `CompositeJudge` 对摘要质量做**自动化评估**，
并把 optimization_plan 第 4 节的 4 个测试用例固化为可重复运行的评测集。

## 新增/变更文件

```
examples/AgenticX-LongTextSummarizer/agenticx_service/evaluation/
  judges.py
  datasets/
    email_short.json
    email_long_chain.json
    news_deep.json
    news_overflow.json
  run_eval.py
```

## 任务要点

- **维度评委**：共用 `faithfulness`/`conciseness`；email 加 `action_item_coverage`；news 加 `fact_5w1h_coverage`；`CompositeJudge` 聚合。
- **4 个数据集**：短邮件、8000+ 字邮件链（lost-in-middle）、万字新闻、overflow 边界。
- **run_eval**：直接 import `SummarizerService`（不必起 HTTP）；PII 泄漏与 overflow 崩溃为**硬断言**；输出 `report_<timestamp>.json` + markdown。

## 验收标准

1. 4 个用例可一键评测，产出分维度评分报告。
2. PII 泄漏、overflow 崩溃为硬失败，不被 LLM 主观分掩盖。
3. 裁判模型可与业务模型分开配置。
4. Mock LLM 下可跑通 CI 冒烟。

## 收尾（可选）

- README 增加「评测如何运行」。
- 旧 `api_server.py` 标记 deprecated（保留不删）。

Made-with: Damon Li
