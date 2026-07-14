import { COOKIE_NAME } from "@shared/const";
import { z } from "zod";
import { getSessionCookieOptions } from "./_core/cookies";
import { invokeLLM, type Message } from "./_core/llm";
import { ENV } from "./_core/env";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import {
  getSummaryHistoryByUser,
  insertSummaryHistory,
  getCollectionHistoryByUser,
  insertCollectionHistory,
} from "./db";

// ─── Domestic model endpoint routing table ───
const DOMESTIC_MODEL_ENDPOINTS: Record<string, { baseUrl: string; name: string }> = {
  // DeepSeek
  "deepseek-chat":          { baseUrl: "https://api.deepseek.com", name: "DeepSeek" },
  "deepseek-reasoner":      { baseUrl: "https://api.deepseek.com", name: "DeepSeek" },
  // Alibaba Qwen
  "qwen-max":               { baseUrl: "https://dashscope.aliyuncs.com/compatible-mode", name: "Qwen" },
  "qwen-plus":              { baseUrl: "https://dashscope.aliyuncs.com/compatible-mode", name: "Qwen" },
  "qwen-turbo":             { baseUrl: "https://dashscope.aliyuncs.com/compatible-mode", name: "Qwen" },
  "qwen-long":              { baseUrl: "https://dashscope.aliyuncs.com/compatible-mode", name: "Qwen" },
  // ByteDance Doubao
  "doubao-pro-32k":         { baseUrl: "https://ark.cn-beijing.volces.com/api", name: "Doubao" },
  "doubao-pro-128k":        { baseUrl: "https://ark.cn-beijing.volces.com/api", name: "Doubao" },
  "doubao-lite-32k":        { baseUrl: "https://ark.cn-beijing.volces.com/api", name: "Doubao" },
  // Moonshot Kimi
  "moonshot-v1-8k":         { baseUrl: "https://api.moonshot.cn", name: "Kimi" },
  "moonshot-v1-32k":        { baseUrl: "https://api.moonshot.cn", name: "Kimi" },
  "moonshot-v1-128k":       { baseUrl: "https://api.moonshot.cn", name: "Kimi" },
  // Zhipu GLM
  "glm-4":                  { baseUrl: "https://open.bigmodel.cn/api/paas", name: "GLM" },
  "glm-4-flash":            { baseUrl: "https://open.bigmodel.cn/api/paas", name: "GLM" },
  "glm-4-air":              { baseUrl: "https://open.bigmodel.cn/api/paas", name: "GLM" },
  // Tencent Hunyuan
  "hunyuan-pro":            { baseUrl: "https://api.hunyuan.cloud.tencent.com", name: "Hunyuan" },
  "hunyuan-standard":       { baseUrl: "https://api.hunyuan.cloud.tencent.com", name: "Hunyuan" },
  "hunyuan-lite":           { baseUrl: "https://api.hunyuan.cloud.tencent.com", name: "Hunyuan" },
  // 01.AI Yi
  "yi-large":               { baseUrl: "https://api.lingyiwanwu.com", name: "Yi" },
  "yi-medium":              { baseUrl: "https://api.lingyiwanwu.com", name: "Yi" },
  "yi-spark":               { baseUrl: "https://api.lingyiwanwu.com", name: "Yi" },
  // Baidu ERNIE
  "ernie-4.0-8k":           { baseUrl: "https://qianfan.baidubce.com/v2", name: "ERNIE" },
  "ernie-3.5-8k":           { baseUrl: "https://qianfan.baidubce.com/v2", name: "ERNIE" },
  "ernie-speed-128k":       { baseUrl: "https://qianfan.baidubce.com/v2", name: "ERNIE" },
};

function getDomesticEndpoint(model: string): { baseUrl: string; name: string } | null {
  return DOMESTIC_MODEL_ENDPOINTS[model] ?? null;
}

// ─── Token estimation (rough: 1 token ≈ 1.5 Chinese chars or 4 English chars) ───
function estimateTokens(text: string): number {
  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const otherChars = text.length - chineseChars;
  return Math.ceil(chineseChars / 1.5 + otherChars / 4);
}

// ─── Split text into chunks ───
function splitIntoChunks(text: string, chunkSize = 2000): string[] {
  const chunks: string[] = [];
  const paragraphs = text.split(/\n\n+/);
  let current = "";
  for (const para of paragraphs) {
    if (estimateTokens(current + "\n\n" + para) > chunkSize && current) {
      chunks.push(current.trim());
      current = para;
    } else {
      current = current ? current + "\n\n" + para : para;
    }
  }
  if (current.trim()) chunks.push(current.trim());
  return chunks.length > 0 ? chunks : [text];
}

// ─── Domain-specific system prompts ───
function getSystemPrompt(domain: "email" | "news"): string {
  if (domain === "email") {
    return `You are an expert email summarizer. Extract key information from emails concisely in Chinese.
Focus on: action items, decisions, deadlines, and key stakeholders.
Format: Use numbered points. Keep it under 5 sentences.`;
  }
  return `You are an expert news summarizer. Summarize news articles using the 5W1H framework in Chinese.
Focus on: What happened, Who is involved, When, Where, Why, and How.
Format: Start with a one-sentence headline, then 3-4 key points.`;
}

// ─── LLM call with optional model + custom apiKey override ───
async function callLLM(
  systemPrompt: string,
  userContent: string,
  opts?: { model?: string; apiKey?: string }
): Promise<string> {
  const messages: Message[] = [
    { role: "system" as const, content: systemPrompt },
    { role: "user" as const, content: userContent },
  ];

  // If a custom apiKey is provided, route to the correct endpoint
  if (opts?.apiKey && opts.apiKey.trim()) {
    // Check if this is a domestic model with its own endpoint
    const domesticEndpoint = opts.model ? getDomesticEndpoint(opts.model) : null;
    const baseUrl = domesticEndpoint
      ? domesticEndpoint.baseUrl
      : (ENV.forgeApiUrl && ENV.forgeApiUrl.trim()
          ? ENV.forgeApiUrl.replace(/\/$/, "")
          : "https://forge.manus.im");
    const payload: Record<string, unknown> = {
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
    };
    if (opts.model) payload.model = opts.model;
    const res = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${opts.apiKey.trim()}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`LLM API error ${res.status}: ${errText.slice(0, 200)}`);
    }
    const data = await res.json() as { choices: Array<{ message: { content: string } }> };
    const raw = data.choices[0]?.message?.content;
    return typeof raw === "string" ? raw : "";
  }

  // Default: use built-in invokeLLM
  const response = await invokeLLM({
    messages,
    ...(opts?.model ? { model: opts.model } : {}),
  });
  const raw = response.choices[0]?.message?.content;
  return typeof raw === "string" ? raw : "";
}

// ─── Map-Reduce summarization ───
async function mapReduceSummarize(
  text: string,
  domain: "email" | "news",
  opts?: { model?: string; apiKey?: string }
): Promise<{ summary: string; llmCalls: number; promptTokens: number; stages: string[] }> {
  const systemPrompt = getSystemPrompt(domain);
  const chunks = splitIntoChunks(text, 2000);
  if (chunks.length === 1) {
    const tokens = estimateTokens(text);
    const summary = await callLLM(systemPrompt, `请对以下内容进行摘要：\n\n${text}`, opts);
    return { summary, llmCalls: 1, promptTokens: tokens, stages: ["single"] };
  }
  // Map phase: summarize each chunk in parallel
  const mapPromises = chunks.map((chunk, i) =>
    callLLM(systemPrompt, `这是长文本的第 ${i + 1}/${chunks.length} 段，请对这段内容进行摘要：\n\n${chunk}`, opts)
  );
  const partials = await Promise.all(mapPromises);
  // Reduce phase: merge partial summaries
  const mergedPartials = partials
    .map((s, i) => `【第${i + 1}段摘要】\n${s}`)
    .join("\n\n");
  const reducedSummary = await callLLM(
    systemPrompt,
    `以下是一篇长文本各段的摘要，请将它们整合为一份完整、连贯的最终摘要：\n\n${mergedPartials}`,
    opts
  );
  const totalTokens = chunks.reduce((acc, c) => acc + estimateTokens(c), 0);
  return {
    summary: reducedSummary,
    llmCalls: chunks.length + 1,
    promptTokens: totalTokens,
    stages: ["map", "reduce"],
  };
}

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query((opts) => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),

  // ─── Model list ───
  models: router({
    list: publicProcedure
      .input(z.object({ apiKey: z.string().optional() }))
      .query(async ({ input }) => {
        // Domestic models are always included regardless of Forge API availability
        const DOMESTIC_MODELS = [
          "deepseek-chat",
          "deepseek-reasoner",
          "qwen-max",
          "qwen-plus",
          "qwen-turbo",
          "qwen-long",
          "moonshot-v1-8k",
          "moonshot-v1-32k",
          "moonshot-v1-128k",
          "glm-4",
          "glm-4-flash",
          "glm-4-air",
          "doubao-pro-32k",
          "doubao-pro-128k",
          "doubao-lite-32k",
          "hunyuan-pro",
          "hunyuan-standard",
          "hunyuan-lite",
          "yi-large",
          "yi-medium",
          "yi-spark",
          "ernie-4.0-8k",
          "ernie-3.5-8k",
          "ernie-speed-128k",
        ];

        const FORGE_FALLBACK = [
          "claude-haiku-4-5",
          "claude-sonnet-4-6",
          "claude-opus-4-6",
          "claude-opus-4-7",
          "gpt-5-nano",
          "gpt-5-mini",
          "gpt-5",
          "gpt-5.5",
          "gemini-2.5-flash",
          "gemini-3-flash-preview",
          "gemini-3.1-pro-preview",
        ];

        let forgeModels: string[] = [];
        try {
          const key = (input.apiKey && input.apiKey.trim()) ? input.apiKey.trim() : ENV.forgeApiKey;
          const baseUrl = ENV.forgeApiUrl && ENV.forgeApiUrl.trim()
            ? ENV.forgeApiUrl.replace(/\/$/, "")
            : "https://forge.manus.im";
          const res = await fetch(`${baseUrl}/v1/models`, {
            headers: { Authorization: `Bearer ${key}` },
          });
          if (res.ok) {
            const data = await res.json() as { data: Array<{ id: string }> };
            forgeModels = (data.data ?? []).map((m) => m.id).filter(Boolean);
          }
        } catch { /* ignore, use fallback */ }

        if (forgeModels.length === 0) forgeModels = FORGE_FALLBACK;

        // Merge: forge models first, then domestic models (deduplicated)
        const forgeSet = new Set(forgeModels);
        const merged = [
          ...forgeModels,
          ...DOMESTIC_MODELS.filter((m) => !forgeSet.has(m)),
        ];
        return merged;
      }),
  }),

  // ─── Single document summarization ───
  summarize: router({
    single: publicProcedure
      .input(
        z.object({
          content: z.string().min(10).max(100000),
          domain: z.enum(["email", "news"]),
          userId: z.number().optional(),
          model: z.string().optional(),
          apiKey: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        const { content, domain, userId, model, apiKey } = input;
        const opts = { model, apiKey };
        const t0 = Date.now();
        const tokens = estimateTokens(content);
        const isLong = tokens > 2500;
        let result: { summary: string; llmCalls: number; promptTokens: number; stages: string[] };
        if (isLong) {
          result = await mapReduceSummarize(content, domain, opts);
        } else {
          const systemPrompt = getSystemPrompt(domain);
          const summary = await callLLM(systemPrompt, `请对以下内容进行摘要：\n\n${content}`, opts);
          result = { summary, llmCalls: 1, promptTokens: tokens, stages: ["single"] };
        }
        const durationMs = Date.now() - t0;
        // Save to history if user is logged in
        if (userId) {
          try {
            await insertSummaryHistory({
              userId,
              domain,
              inputSnippet: content.slice(0, 280) + (content.length > 280 ? "…" : ""),
              inputLength: content.length,
              summaryText: result.summary,
              llmCalls: result.llmCalls,
              promptTokens: result.promptTokens,
              stages: result.stages.join(" → "),
              durationMs,
              model: model ?? "gemini-2.5-flash",
            });
          } catch (e) {
            console.warn("[History] Failed to save:", e);
          }
        }
        return {
          summary: result.summary,
          trace: {
            llmCalls: result.llmCalls,
            promptTokens: result.promptTokens,
            stages: result.stages,
            domain,
            isMapReduce: result.stages.includes("map"),
            model: model ?? "gemini-2.5-flash (default)",
            durationMs,
          },
        };
      }),

    // ─── Multi-document collection summarization ───
    collection: publicProcedure
      .input(
        z.object({
          docs: z
            .array(
              z.object({
                docId: z.string(),
                title: z.string().optional(),
                content: z.string().min(10).max(50000),
                domain: z.enum(["email", "news"]).default("news"),
              })
            )
            .min(1)
            .max(10),
          intent: z.enum(["compare", "aggregate", "timeline"]),
          userId: z.number().optional(),
          model: z.string().optional(),
          apiKey: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        const { docs, intent, userId, model, apiKey } = input;
        const opts = { model, apiKey };
        const t0 = Date.now();
        // Step 1: Summarize each doc individually
        const perDocResults = await Promise.all(
          docs.map(async (doc) => {
            const tokens = estimateTokens(doc.content);
            const isLong = tokens > 2500;
            let result: { summary: string; llmCalls: number; promptTokens: number; stages: string[] };
            if (isLong) {
              result = await mapReduceSummarize(doc.content, doc.domain, opts);
            } else {
              const systemPrompt = getSystemPrompt(doc.domain);
              const summary = await callLLM(systemPrompt, `请对以下内容进行摘要：\n\n${doc.content}`, opts);
              result = { summary, llmCalls: 1, promptTokens: tokens, stages: ["single"] };
            }
            return { docId: doc.docId, title: doc.title ?? doc.docId, ...result };
          })
        );
        // Step 2: Cross-document synthesis
        const perDocSummaries = perDocResults
          .map((r, i) => `【文档${i + 1}：${r.title}】\n${r.summary}`)
          .join("\n\n");
        const intentPrompts: Record<string, string> = {
          compare: `以下是多篇文档各自的摘要，请进行深度对比分析，找出它们的共同点、差异点，并给出综合结论：`,
          aggregate: `以下是多篇文档各自的摘要，请将它们整合为一份全面的综合摘要，涵盖所有关键信息：`,
          timeline: `以下是多篇文档各自的摘要，请按时间顺序梳理关键事件，构建一条清晰的时间线：`,
        };
        const crossSummary = await callLLM(
          "You are an expert document analyst. Provide structured analysis in Chinese.",
          `${intentPrompts[intent]}\n\n${perDocSummaries}`,
          opts
        );
        const totalCalls = perDocResults.reduce((acc, r) => acc + r.llmCalls, 0) + 1;
        const totalTokens = perDocResults.reduce((acc, r) => acc + r.promptTokens, 0);
        const durationMs = Date.now() - t0;

        // Save to collection history if user is logged in
        if (userId) {
          try {
            const docSnippets = JSON.stringify(
              docs.map((d) => ({
                title: d.title ?? d.docId,
                snippet: d.content.slice(0, 100) + (d.content.length > 100 ? "…" : ""),
              }))
            ).slice(0, 3900);
            const individualSummaries = JSON.stringify(
              perDocResults.map((r) => ({ docId: r.docId, title: r.title, summary: r.summary }))
            );
            await insertCollectionHistory({
              userId,
              intent,
              docCount: docs.length,
              docSnippets,
              individualSummaries,
              synthesisText: crossSummary,
              llmCalls: totalCalls,
              promptTokens: totalTokens,
              stages: "collection → synthesis",
              durationMs,
              model: model ?? "gemini-2.5-flash",
            });
          } catch (e) {
            console.warn("[CollectionHistory] Failed to save:", e);
          }
        }

        return {
          crossSummary,
          perDoc: perDocResults.map((r) => ({ docId: r.docId, title: r.title, summary: r.summary })),
          trace: {
            llmCalls: totalCalls,
            promptTokens: totalTokens,
            intent,
            docCount: docs.length,
            model: model ?? "gemini-2.5-flash (default)",
            durationMs,
          },
        };
      }),
  }),

  // ─── History (protected) ───
  history: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return await getSummaryHistoryByUser(ctx.user.id, 50);
    }),
    listCollection: protectedProcedure.query(async ({ ctx }) => {
      return await getCollectionHistoryByUser(ctx.user.id, 50);
    }),
  }),
});

export type AppRouter = typeof appRouter;
