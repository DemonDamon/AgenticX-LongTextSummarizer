---
name: LongText Summarizer Phase 3
overview: 引入邮件/新闻意图识别与路由，基于 TokenCounter/truncate_text 实现多级 Token 溢出保护，极端输入优雅降级不抛 500。
todos:
  - id: t3-intent
    content: T3.1 意图识别 agenticx_service/intent.py（rule 默认 / llm|hybrid 可选）
    status: completed
  - id: t3-overflow
    content: T3.2 溢出保护 agenticx_service/overflow.py（L1-L4 降级，不用 OverflowRecoveryPipeline）
    status: completed
  - id: t3-prompts
    content: T3.3 新增 map_news / reduce_news 场景模板
    status: completed
  - id: t3-wire
    content: T3.4 串联 intent -> overflow -> summarizer/mapreduce，API 可选返回 scenario/overflow_level
    status: completed
  - id: t3-tests
    content: T3.5 冒烟测试 test_phase3_routing_overflow.py
    status: completed
isProject: false
---

# Phase 3 - 场景路由 + Token 溢出保护

**Author:** Damon Li
**Date:** 2026-06-17
**前置:** Phase 2 完成；务必先读 overview plan 第 2 节「设计纠偏」第 1 点。
## 目标

1. 引入**邮件 / 新闻意图识别与路由**，不同场景走不同 Map/Reduce 模板。
2. 增加**Token 溢出保护**：极端超长 / 异常输入时优雅降级，不抛 500。

## 新增/变更文件

```
examples/AgenticX-LongTextSummarizer/agenticx_service/
  intent.py
  overflow.py
  mapreduce.py          # 接入 scenario 选择模板 + overflow 守卫
  summarizer.py         # 扩展串联
  prompts/templates.yaml  # map_news / reduce_news
config_agenticx.yaml    # intent 段 + overflow 段
```

## 任务要点

- **IntentClassifier**：`mode="rule"` 启发式（Re:/转发 -> email；记者/报道 -> news），不确定默认 email；`llm`/`hybrid` 用 1 次轻量分类。
- **OverflowGuard**（**不用** `OverflowRecoveryPipeline`）：
  - L1 正常 -> 原样
  - L2 超限 -> Phase 2 Map-Reduce
  - L3 极端 -> `truncate_text` 硬截断 + 降级标注
  - L4 兜底 -> HTTP 200 + 友好提示
- API 响应可选返回 `scenario` 与 `overflow_level`（保持 `code/message/text` 兼容）。

## 验收标准

1. 邮件 / 新闻自动路由到对应模板，rule 模式零额外 LLM 调用。
2. 极端超长输入触发 L3/L4 降级，**不出现 500**。
3. 溢出保护仅依赖 `TokenCounter`/`truncate_text`，未误引入 `OverflowRecoveryPipeline`。

Made-with: Damon Li
