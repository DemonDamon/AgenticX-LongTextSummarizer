import { trpc } from "@/lib/trpc";
import ModelKeyPanel, { useModelKeyState } from "@/components/ModelKeyPanel";
import { useState } from "react";
import { Streamdown } from "streamdown";
import { Link } from "wouter";

interface Doc {
  docId: string;
  title: string;
  content: string;
  domain: "email" | "news";
}

const SAMPLE_DOCS: Doc[] = [
  {
    docId: "doc-1",
    title: "OpenAI GPT-5 发布公告",
    domain: "news",
    content: `OpenAI今日正式发布GPT-5，这是迄今为止最强大的语言模型。GPT-5在推理能力、代码生成和多模态理解方面均取得重大突破。据OpenAI CEO Sam Altman表示，GPT-5在数学推理基准测试中超越了人类专家水平，在代码生成任务上的通过率达到92%。新模型支持最长200K token的上下文窗口，并原生支持图像、音频和视频输入。定价方面，API调用价格较GPT-4降低约40%，企业版将于下月正式上线。`,
  },
  {
    docId: "doc-2",
    title: "Anthropic Claude 4 技术报告",
    domain: "news",
    content: `Anthropic发布了Claude 4系列模型，包括Claude 4 Haiku、Sonnet和Opus三个版本。技术报告显示，Claude 4在长文档理解、复杂推理和安全性方面有显著提升。Claude 4 Opus在MMLU基准测试中得分达到89.7%，在HumanEval代码测试中达到85.3%。Anthropic特别强调了Constitutional AI的改进，新版本在拒绝有害请求的同时，显著减少了误拒率。上下文窗口扩展至300K token，特别适合法律文档分析和科研论文处理场景。`,
  },
  {
    docId: "doc-3",
    title: "Google Gemini Ultra 2.0 评测",
    domain: "news",
    content: `Google DeepMind发布Gemini Ultra 2.0，在多模态能力上实现质的飞跃。该模型能够同时处理文本、图像、音频、视频和代码，在跨模态推理任务上表现卓越。Gemini Ultra 2.0在Google内部测试中，在医学影像诊断辅助任务上达到专科医生水平。模型还集成了Google搜索和Google Workspace，实现了真正意义上的"AI助手"体验。在价格方面，Gemini Ultra 2.0的API价格与GPT-4 Turbo持平，但提供更长的免费额度。`,
  },
];

const INTENT_LABELS = {
  compare: { label: "对比分析", desc: "找出共同点与差异", icon: "⚖️" },
  aggregate: { label: "聚合摘要", desc: "整合为综合摘要", icon: "🔗" },
  timeline: { label: "时间线", desc: "按时序梳理事件", icon: "📅" },
};

export default function MultiDoc() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [intent, setIntent] = useState<"compare" | "aggregate" | "timeline">("compare");
  const [result, setResult] = useState<{
    crossSummary: string;
    perDoc: { docId: string; title: string; summary: string }[];
    trace: { llmCalls: number; promptTokens: number; intent: string; docCount: number; model?: string };
  } | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);
  const { model, apiKey, setModel, setApiKey } = useModelKeyState();

  const mutation = trpc.summarize.collection.useMutation({
    onSuccess: (data) => setResult(data),
  });

  const loadSamples = () => {
    setDocs(SAMPLE_DOCS);
    setResult(null);
  };

  const addDoc = () => {
    const newDoc: Doc = {
      docId: `doc-${Date.now()}`,
      title: `文档 ${docs.length + 1}`,
      content: "",
      domain: "news",
    };
    setDocs([...docs, newDoc]);
  };

  const updateDoc = (docId: string, field: keyof Doc, value: string) => {
    setDocs(docs.map((d) => (d.docId === docId ? { ...d, [field]: value } : d)));
  };

  const removeDoc = (docId: string) => {
    setDocs(docs.filter((d) => d.docId !== docId));
  };

  const handleSubmit = () => {
    if (docs.length === 0) return;
    const validDocs = docs.filter((d) => d.content.trim().length >= 10);
    if (validDocs.length === 0) return;
    setResult(null);
    mutation.mutate({ docs: validDocs, intent, model: model || undefined, apiKey: apiKey || undefined });
  };

  return (
    <div className="min-h-screen blueprint-bg">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/60 bg-background/90 backdrop-blur-md">
        <div className="container flex items-center justify-between h-14">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 text-sm font-bold hover:text-primary transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                AgenticX Summarizer
            </Link>
            <span className="text-border">/</span>
            <span className="text-sm text-muted-foreground">多文档对比摘要</span>
          </div>
          <div className="flex items-center gap-2">
            {[
              { href: "/demo", label: "单篇演示" },
              { href: "/docs", label: "API 文档" },
              { href: "/history", label: "历史" },
            ].map((item) => (
              <Link key={item.href} href={item.href} className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors">
                {item.label}
              </Link>
            ))}
            <div className="ml-2 border-l border-border/40 pl-2">
              <ModelKeyPanel
                model={model}
                apiKey={apiKey}
                onModelChange={setModel}
                onApiKeyChange={setApiKey}
              />
            </div>
          </div>
        </div>
      </nav>

      <div className="container pt-24 pb-16">
        {/* Header */}
        <div className="mb-8">
          <div className="mono-label text-[11px] text-muted-foreground mb-2">// multi_doc_summarizer.demo</div>
          <h1 className="text-4xl font-black mb-2">多文档对比摘要</h1>
          <p className="text-muted-foreground text-sm">
            添加多篇文档，选择聚合意图，获取各篇单独摘要及跨篇综合结论。
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          {/* Left: Config (2/5) */}
          <div className="xl:col-span-2 space-y-4">
            {/* Intent selector */}
            <div className="blueprint-card rounded-xl border border-border/60 p-4">
              <div className="mono-label text-[11px] text-muted-foreground mb-3">// intent_selector</div>
              <div className="space-y-2">
                {(Object.entries(INTENT_LABELS) as [string, typeof INTENT_LABELS["compare"]][]).map(([key, val]) => (
                  <button
                    key={key}
                    onClick={() => setIntent(key as "compare" | "aggregate" | "timeline")}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg border text-left transition-all duration-150 ${
                      intent === key
                        ? "bg-primary/5 border-primary text-foreground"
                        : "bg-transparent border-border/50 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    }`}
                  >
                    <span className="text-lg">{val.icon}</span>
                    <div>
                      <div className="font-semibold text-sm font-mono">{key}</div>
                      <div className="text-xs opacity-70">{val.label} — {val.desc}</div>
                    </div>
                    {intent === key && (
                      <svg className="w-4 h-4 ml-auto text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={loadSamples}
                className="flex-1 py-2 text-sm border border-border rounded-lg text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors font-mono"
              >
                加载示例
              </button>
              <button
                onClick={addDoc}
                className="flex-1 py-2 text-sm border border-border rounded-lg text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
              >
                + 添加文档
              </button>
            </div>

            {/* Doc list */}
            <div className="space-y-3">
              {docs.map((doc, idx) => (
                <div key={doc.docId} className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                  <div className="px-4 py-2.5 bg-muted/30 border-b border-border/40 flex items-center gap-2">
                    <span className="mono-label text-[10px] text-primary">doc_{idx + 1}</span>
                    <input
                      value={doc.title}
                      onChange={(e) => updateDoc(doc.docId, "title", e.target.value)}
                      className="flex-1 bg-transparent text-xs font-semibold focus:outline-none text-foreground"
                    />
                    <select
                      value={doc.domain}
                      onChange={(e) => updateDoc(doc.docId, "domain", e.target.value as "email" | "news")}
                      className="text-xs bg-transparent text-muted-foreground focus:outline-none border-none"
                    >
                      <option value="email">邮件</option>
                      <option value="news">新闻</option>
                    </select>
                    <button
                      onClick={() => removeDoc(doc.docId)}
                      className="text-muted-foreground/50 hover:text-red-500 transition-colors ml-1"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <textarea
                    value={doc.content}
                    onChange={(e) => updateDoc(doc.docId, "content", e.target.value)}
                    placeholder="粘贴文档内容..."
                    className="w-full h-28 resize-none bg-transparent text-xs text-foreground placeholder:text-muted-foreground/40 focus:outline-none p-3 font-mono leading-relaxed"
                  />
                </div>
              ))}
            </div>

            {docs.length > 0 && (
              <button
                onClick={handleSubmit}
                disabled={mutation.isPending || docs.filter((d) => d.content.trim().length >= 10).length === 0}
                className="w-full py-3 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 active:scale-[0.97] flex items-center justify-center gap-2"
              >
                {mutation.isPending ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    处理中...
                  </>
                ) : (
                  `执行 ${intent} 分析 (${docs.length} 篇文档)`
                )}
              </button>
            )}

            {docs.length === 0 && (
              <div className="blueprint-card rounded-xl border border-dashed border-border/60 p-6 text-center">
                <div className="text-muted-foreground/50 text-sm">点击"加载示例"或"添加文档"开始</div>
                <div className="mono-label text-[10px] text-muted-foreground/40 mt-1">// min_docs: 1</div>
              </div>
            )}
          </div>

          {/* Right: Results (3/5) */}
          <div className="xl:col-span-3 space-y-4">
            {mutation.isPending && (
              <div className="blueprint-card rounded-xl border border-border/60 p-10 flex flex-col items-center justify-center gap-4">
                <div className="relative w-14 h-14">
                  <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
                  <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                  <div className="absolute inset-2 rounded-full border border-cyan-300/40 border-b-transparent animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.5s" }} />
                </div>
                <div className="text-center">
                  <div className="text-sm font-semibold mb-1">正在执行多文档分析</div>
                  <div className="mono-label text-[11px] text-muted-foreground">
                    并行摘要各篇文档 → {intent} 跨篇聚合...
                  </div>
                </div>
              </div>
            )}

            {result && !mutation.isPending && (
              <>
                {/* Trace */}
                <div className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                  <div className="px-4 py-2.5 bg-muted/50 border-b border-border/40 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="mono-label text-[11px] text-muted-foreground">// trace_info</span>
                  </div>
                  <div className="p-4 grid grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-xl font-black font-mono text-primary">{result.trace.llmCalls}</div>
                      <div className="text-xs text-muted-foreground mt-1">调用次数</div>
                    </div>
                    <div className="text-center border-x border-border/40">
                      <div className="text-xl font-black font-mono text-primary">{result.trace.promptTokens}</div>
                      <div className="text-xs text-muted-foreground mt-1">Token 消耗</div>
                    </div>
                    <div className="text-center border-r border-border/40">
                      <div className="text-xl font-black font-mono text-cyan-600">{result.trace.docCount}</div>
                      <div className="text-xs text-muted-foreground mt-1">文档数量</div>
                    </div>
                    <div className="text-center">
                      <div className="font-mono font-bold text-sm text-pink-600 bg-pink-50 rounded px-2 py-1">{result.trace.intent}</div>
                      <div className="text-xs text-muted-foreground mt-1">处理阶段</div>
                    </div>
                  </div>
                </div>

                {/* Cross summary */}
                <div className="blueprint-card rounded-xl border border-primary/30 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="mono-label text-[11px] text-primary">// cross_doc_synthesis</span>
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">{result.trace.intent}</span>
                  </div>
                  <div className="prose prose-sm max-w-none text-foreground">
                    <Streamdown>{result.crossSummary}</Streamdown>
                  </div>
                </div>

                {/* Per-doc summaries */}
                <div className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                  <div className="px-4 py-2.5 bg-muted/50 border-b border-border/40">
                    <span className="mono-label text-[11px] text-muted-foreground">// per_doc_summaries[]</span>
                  </div>
                  <div className="divide-y divide-border/40">
                    {result.perDoc.map((doc, i) => (
                      <div key={doc.docId} className="p-4">
                        <button
                          onClick={() => setExpandedDoc(expandedDoc === doc.docId ? null : doc.docId)}
                          className="w-full flex items-center justify-between gap-2 text-left"
                        >
                          <div className="flex items-center gap-2">
                            <span className="mono-label text-[10px] text-primary">doc_{i + 1}</span>
                            <span className="text-sm font-semibold">{doc.title}</span>
                          </div>
                          <svg
                            className={`w-4 h-4 text-muted-foreground transition-transform ${expandedDoc === doc.docId ? "rotate-180" : ""}`}
                            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        {expandedDoc === doc.docId && (
                          <div className="mt-3 text-sm text-muted-foreground leading-relaxed pl-2 border-l-2 border-primary/30">
                            <Streamdown>{doc.summary}</Streamdown>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {mutation.isError && (
              <div className="blueprint-card rounded-xl border border-red-200 p-4 mb-2">
                <div className="flex items-center gap-2 text-red-600 mb-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="text-sm font-medium">分析失败，请重试</span>
                </div>
                <p className="text-xs text-red-500 font-mono">{mutation.error?.message}</p>
              </div>
            )}

            {!result && !mutation.isPending && (
              <div className="blueprint-card rounded-xl border border-dashed border-border/60 p-12 flex flex-col items-center justify-center gap-3 text-center">
                <div className="w-14 h-14 rounded-full border-2 border-border/40 flex items-center justify-center">
                  <svg className="w-6 h-6 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">添加文档并执行分析</div>
                  <div className="mono-label text-[10px] text-muted-foreground/50 mt-1">// cross_summary: pending</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
