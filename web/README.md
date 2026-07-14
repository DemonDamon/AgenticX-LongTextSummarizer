# AgenticX-LongTextSummarizer Web Platform

基于 AgenticX 框架构建的智能长文本摘要平台 Web 界面。

## 技术栈

- **前端**: React 19 + Tailwind CSS 4 + shadcn/ui
- **后端**: Express 4 + tRPC 11
- **数据库**: MySQL / TiDB (Drizzle ORM)
- **LLM**: 支持 34 个模型（国产 + 国际），含 DeepSeek、Qwen、Kimi、GLM、GPT、Claude、Gemini 等

## 功能

- 单篇摘要演示（邮件 / 新闻场景，短文本直接调用，长文本 Map-Reduce 并行处理）
- 多文档对比摘要（compare / aggregate / timeline 三种聚合意图）
- 模型选择器（34 个模型，按厂商分组，支持自定义 API Key）
- Trace 信息展示（调用次数 / Token 消耗 / 耗时 / 处理阶段）
- 摘要历史记录（登录用户可查看，含完整指标）
- API 文档页面（含 curl 示例）

## 快速启动

```bash
cd web
pnpm install
pnpm dev
```
