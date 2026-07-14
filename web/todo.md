# AgenticX-LongTextSummarizer TODO

## Phase 1: 基础结构
- [x] 全局样式（数学蓝图风格：白色网格背景、青色/粉色线框、等宽字体）
- [x] 数据库 Schema（summaryHistory 表）
- [x] 路由配置（/, /demo, /multidoc, /docs, /history）
- [x] 顶部导航组件

## Phase 2: 落地页
- [x] Hero 区域（超大标题 + 副标题 + CTA）
- [x] 核心特性卡片（Map-Reduce、智能分块、溢出恢复、多模态、个性化记忆）
- [x] 架构概览图示（SVG 流程图）
- [x] GitHub 链接入口

## Phase 3: 后端 API
- [x] summarize.single tRPC procedure（短文本直接调用 LLM）
- [x] summarize.single 长文本分块 + Map-Reduce 并行处理
- [x] summarize.collection tRPC procedure（多文档聚合：compare/aggregate/timeline）
- [x] 历史记录写入数据库

## Phase 4: 演示页面
- [x] 单篇摘要演示页（文本输入、场景选择、Trace 展示）
- [x] 多文档对比摘要页（多文档添加、意图选择、结果展示）

## Phase 5: 文档与历史
- [x] API 文档页（端点说明、curl 示例、一键复制）
- [x] 历史记录页（登录用户专属，展示历史摘要）
- [x] 单元测试（6 tests passed）
- [x] 发布上线

## Phase 6: 模型选择与自定义 Key
- [x] 后端 summarize.single 和 summarize.collection 支持传入 model 和 apiKey 参数
- [x] 后端新增 models.list tRPC procedure，返回可用模型列表
- [x] 后端使用自定义 apiKey 时走独立 fetch（不使用内置 forgeApiKey）
- [x] 前端单篇演示页添加模型选择器 + API Key 输入面板
- [x] 前端多文档页添加模型选择器 + API Key 输入面板
- [x] Key 存储在 localStorage，页面刷新后自动恢复

## Phase 7: 国产大模型支持
- [x] 后端 fallback 模型列表补充国产模型（DeepSeek、Qwen、Doubao、Kimi、GLM、Hunyuan、Yi）
- [x] 前端模型选择器按厂商分组展示（国产 / Anthropic / OpenAI / Google）
- [x] 国产模型使用自定义 API Key 时，base_url 自动切换到对应厂商端点

## Phase 8: 耗时显示 + 历史记录
- [x] 后端 summarize.single 和 summarize.collection 返回值中增加 durationMs 字段
- [x] 前端 Demo 页 Trace 面板增加耗时展示（第 4 个指标卡）
- [x] 前端 Demo 页摘要完成后在右侧展示历史记录列表（最近 10 条）
- [x] 历史记录支持点击展开查看完整摘要
