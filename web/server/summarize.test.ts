import { describe, expect, it, vi } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

// Mock the LLM invocation
vi.mock("./_core/llm", () => ({
  invokeLLM: vi.fn().mockResolvedValue({
    id: "mock-id",
    created: Date.now(),
    model: "mock-model",
    choices: [
      {
        index: 0,
        message: { role: "assistant", content: "这是一段测试摘要内容，包含关键信息。" },
        finish_reason: "stop",
      },
    ],
    usage: { prompt_tokens: 100, completion_tokens: 50, total_tokens: 150 },
  }),
}));

function createPublicContext(): TrpcContext {
  return {
    user: null,
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: { clearCookie: vi.fn() } as unknown as TrpcContext["res"],
  };
}

describe("summarize.single", () => {
  it("returns summary and trace for short email text", async () => {
    const ctx = createPublicContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.summarize.single({
      content: "发件人：张伟\n主题：Q3产品路线图评审会议纪要\n内容：各位同事，以下是今天会议的纪要，请各负责人确认并跟进。用户增长模块8月15日前完成，支付系统重构推迟至Q4。",
      domain: "email",
    });

    expect(result.summary).toBeTruthy();
    expect(typeof result.summary).toBe("string");
    expect(result.trace).toBeDefined();
    expect(result.trace.llmCalls).toBeGreaterThanOrEqual(1);
    expect(result.trace.promptTokens).toBeGreaterThan(0);
    expect(Array.isArray(result.trace.stages)).toBe(true);
    expect(result.trace.stages.length).toBeGreaterThan(0);
    expect(result.trace.domain).toBe("email");
    expect(typeof result.trace.isMapReduce).toBe("boolean");
  });

  it("returns summary and trace for news domain", async () => {
    const ctx = createPublicContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.summarize.single({
      content: "【深度报道】人工智能大模型竞赛进入下半场。2024年，全球AI领域正在经历深刻的范式转变，竞争焦点从参数规模转向应用落地和商业化变现。OpenAI推出GPT-4o，Anthropic发布Claude 3，国内厂商也在垂直领域形成差异化竞争优势。",
      domain: "news",
    });

    expect(result.summary).toBeTruthy();
    expect(result.trace.domain).toBe("news");
    expect(result.trace.llmCalls).toBeGreaterThanOrEqual(1);
  });

  it("rejects content that is too short", async () => {
    const ctx = createPublicContext();
    const caller = appRouter.createCaller(ctx);

    await expect(
      caller.summarize.single({ content: "太短", domain: "email" })
    ).rejects.toThrow();
  });
});

describe("summarize.collection", () => {
  it("returns cross summary and per-doc summaries", async () => {
    const ctx = createPublicContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.summarize.collection({
      docs: [
        {
          docId: "d1",
          title: "文档一",
          content: "OpenAI今日正式发布GPT-5，这是迄今为止最强大的语言模型。GPT-5在推理能力、代码生成和多模态理解方面均取得重大突破。新模型支持最长200K token的上下文窗口。",
          domain: "news",
        },
        {
          docId: "d2",
          title: "文档二",
          content: "Anthropic发布了Claude 4系列模型，包括Haiku、Sonnet和Opus三个版本。Claude 4在长文档理解、复杂推理和安全性方面有显著提升，上下文窗口扩展至300K token。",
          domain: "news",
        },
      ],
      intent: "compare",
    });

    expect(result.crossSummary).toBeTruthy();
    expect(Array.isArray(result.perDoc)).toBe(true);
    expect(result.perDoc.length).toBe(2);
    expect(result.trace.docCount).toBe(2);
    expect(result.trace.intent).toBe("compare");
    expect(result.trace.llmCalls).toBeGreaterThanOrEqual(2);
  });

  it("rejects empty docs array", async () => {
    const ctx = createPublicContext();
    const caller = appRouter.createCaller(ctx);

    await expect(
      caller.summarize.collection({ docs: [], intent: "aggregate" })
    ).rejects.toThrow();
  });
});
