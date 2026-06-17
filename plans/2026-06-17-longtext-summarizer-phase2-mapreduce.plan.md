---
name: LongText Summarizer Phase 2
overview: 引入 RecursiveChunker（默认）/ AgenticChunker（可选）与 Map-Reduce 流水线，解决长文本 Token 超限与 Lost in the Middle。
todos:
  - id: t2-chunking
    content: T2.1 分块封装 agenticx_service/chunking.py（ChunkerFactory + split 统一接口）
    status: completed
  - id: t2-mapreduce
    content: T2.2 Map-Reduce 引擎 agenticx_service/mapreduce.py（asyncio.gather + Semaphore）
    status: completed
  - id: t2-routing
    content: T2.3 扩展 summarizer.py 按 count_tokens 路由单块/Map-Reduce
    status: completed
  - id: t2-prompts
    content: T2.4 新增 map_email / reduce_email 模板
    status: completed
  - id: t2-tests
    content: T2.5 冒烟测试 test_phase2_mapreduce.py（含 lost_in_middle）
    status: completed
isProject: false
---

# Phase 2 - 长文本处理（Chunker + Map-Reduce）

**Author:** Damon Li
**Date:** 2026-06-17
**前置:** Phase 1 完成。
## 目标

当文本超过单次上下文阈值时，自动 **Chunk -> 并行 Map 子摘要 -> Reduce 全局摘要**。
短文本仍走 Phase 1 单块快路径。

## 新增/变更文件

```
agenticx_service/chunking.py
agenticx_service/mapreduce.py
agenticx_service/summarizer.py  # 扩展
prompts/templates.yaml          # map_email / reduce_email
config_agenticx.yaml            # chunking 段
```

## 验收标准

1. 短文本走单块、长文本走 Map-Reduce，由 token 阈值自动路由。
2. 8000 字邮件链能成功产出最终摘要，且首尾关键信息均被覆盖。
3. 并发受 `Semaphore` 限制；多级 Reduce 有轮数上限。
4. 默认 `recursive` 策略零额外 LLM 成本。

Made-with: Damon Li
