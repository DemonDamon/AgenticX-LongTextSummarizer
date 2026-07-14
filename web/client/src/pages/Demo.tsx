import { useAuth } from "@/_core/hooks/useAuth";
import ModelKeyPanel, { useModelKeyState } from "@/components/ModelKeyPanel";
import { trpc } from "@/lib/trpc";
import { useState } from "react";
import { Streamdown } from "streamdown";
import { Link } from "wouter";

const SAMPLE_TEXTS = {
  email: `发件人：张伟 <zhangwei@company.com>
收件人：产品团队 <product@company.com>
主题：Q3 产品路线图评审会议纪要
时间：2024年7月10日 14:00-16:00

各位同事，

以下是今天产品路线图评审会议的纪要，请各负责人确认并跟进。

一、用户增长模块
前端团队负责，预计8月15日前完成开发。预期新增DAU约12%，主要通过优化注册流程和新增社交分享功能实现。李明负责技术实现，王芳负责产品设计。

二、支付系统重构
原计划Q3完成，现推迟至Q4。主要原因是第三方支付接口存在合规风险，需要法务部门完成审核后方可继续推进。预计法务审核周期为4-6周。陈刚负责跟进法务进度，每周向产品委员会汇报。

三、AI推荐算法升级
A/B测试计划9月1日上线，测试周期4周。数据团队主导，算法团队配合。预期点击率提升15-20%，转化率提升8%。赵雷负责算法模型，刘洋负责数据埋点。

四、下次会议
定于7月28日（周日）上午10:00，地点：3楼大会议室。各负责人需在会议前提交进度报告，格式参照附件模板。

如有问题请及时沟通。

张伟
产品总监`,
  news: `【深度报道】人工智能大模型竞赛进入下半场：从参数规模到应用落地的范式转移

2024年，全球人工智能领域正在经历一场深刻的范式转变。在经历了2023年的"百模大战"之后，AI大模型竞争的焦点已从单纯追求参数规模，逐步转向实际应用落地和商业化变现。

一、技术路线的分化

以OpenAI、Anthropic、Google为代表的国际头部玩家，正在将研发重心从基础模型转向垂直应用。OpenAI推出的GPT-4o实现了文本、图像、语音的多模态融合，而Anthropic的Claude 3系列则在长上下文处理和代码生成领域取得突破。与此同时，国内厂商如百度文心、阿里通义、华为盘古等也在特定垂直领域形成差异化竞争优势。

二、商业化路径的探索

据IDC最新报告显示，2024年全球AI大模型市场规模预计达到1320亿美元，同比增长78%。然而，盈利模式仍是行业面临的核心挑战。订阅制、API调用计费、企业定制化部署成为主流商业模式。值得注意的是，开源模型的崛起正在重塑竞争格局——Meta的Llama 3、Mistral等开源模型以极低成本提供接近闭源模型的性能，倒逼商业模型加速降价。

三、监管与合规的压力

欧盟《人工智能法案》已于2024年8月正式生效，对高风险AI系统提出严格的透明度和可解释性要求。中国国家互联网信息办公室也相继出台多项AI治理规范，要求大模型服务商完成安全评估备案。合规成本的上升正在加速行业整合，中小厂商面临更大的生存压力。

四、未来展望

业界普遍预计，2025年将是AI应用爆发的关键年份。具身智能（Embodied AI）、AI Agent、多模态交互等方向被视为下一个增长极。投资机构对AI基础设施（算力、数据、网络）的投入持续加码，英伟达H100/H200芯片供不应求的局面预计延续至2025年底。

在这场技术与商业的双重竞赛中，真正能够穿越周期的，将是那些既掌握核心技术、又能持续创造用户价值的企业。`,
};

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function TracePanel({ trace }: {
  trace: {
    llmCalls: number;
    promptTokens: number;
    stages: string[];
    domain: string;
    isMapReduce: boolean;
    model?: string;
    durationMs?: number;
  }
}) {
  return (
    <div className="border border-border/60 rounded-lg overflow-hidden">
      <div className="px-4 py-2.5 bg-muted/50 border-b border-border/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="mono-label text-[11px] text-muted-foreground">// trace_info</span>
        </div>
        {trace.model && (
          <span className="mono-label text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded">
            {trace.model}
          </span>
        )}
      </div>
      <div className="p-4 grid grid-cols-4 gap-3">
        <div className="text-center">
          <div className="text-2xl font-black font-mono text-primary">{trace.llmCalls}</div>
          <div className="text-xs text-muted-foreground mt-1">调用次数</div>
        </div>
        <div className="text-center border-x border-border/40">
          <div className="text-2xl font-black font-mono text-primary">{trace.promptTokens}</div>
          <div className="text-xs text-muted-foreground mt-1">Token 消耗</div>
        </div>
        <div className="text-center border-r border-border/40">
          <div className="text-2xl font-black font-mono text-cyan-600">
            {trace.durationMs != null ? formatDuration(trace.durationMs) : "—"}
          </div>
          <div className="text-xs text-muted-foreground mt-1">耗时</div>
        </div>
        <div className="text-center">
          <div className="flex flex-wrap justify-center gap-1">
            {trace.stages.map((s, i) => (
              <span key={i} className="font-mono text-[11px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                {s}
              </span>
            ))}
          </div>
          <div className="text-xs text-muted-foreground mt-1">处理阶段</div>
        </div>
      </div>
      {trace.isMapReduce && (
        <div className="px-4 pb-3">
          <div className="flex items-center gap-1.5 text-xs text-cyan-600 bg-cyan-50 rounded px-2 py-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="font-mono">长文本触发 Map-Reduce 并行处理</span>
          </div>
        </div>
      )}
    </div>
  );
}

function HistoryPanel({ userId }: { userId?: number }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const { data: history, isLoading } = trpc.history.list.useQuery(undefined, {
    enabled: !!userId,
    refetchOnWindowFocus: false,
  });

  if (!userId) {
    return (
      <div className="blueprint-card rounded-xl border border-dashed border-border/60 p-5 text-center">
        <div className="mono-label text-[11px] text-muted-foreground mb-2">// history_records</div>
        <p className="text-xs text-muted-foreground">登录后可查看历史摘要记录</p>
      </div>
    );
  }

  return (
    <div className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
      <div className="px-4 py-2.5 bg-muted/50 border-b border-border/40 flex items-center justify-between">
        <span className="mono-label text-[11px] text-muted-foreground">// history_records</span>
        {history && (
          <span className="mono-label text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded">
            {history.length} 条
          </span>
        )}
      </div>
      {isLoading && (
        <div className="p-6 flex justify-center">
          <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>
      )}
      {!isLoading && (!history || history.length === 0) && (
        <div className="p-6 text-center text-xs text-muted-foreground font-mono">暂无历史记录</div>
      )}
      {history && history.length > 0 && (
        <div className="divide-y divide-border/40 max-h-80 overflow-y-auto">
          {history.slice(0, 10).map((item) => (
            <div key={item.id} className="group">
              <button
                onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                className="w-full px-4 py-3 text-left hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        item.domain === "email"
                          ? "bg-blue-50 text-blue-600"
                          : "bg-orange-50 text-orange-600"
                      }`}>
                        {item.domain === "email" ? "邮件" : "新闻"}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {new Date(item.createdAt).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {item.stages}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate font-mono leading-relaxed">
                      {item.inputSnippet}
                    </p>
                  </div>
                  <svg
                    className={`w-3.5 h-3.5 text-muted-foreground/50 flex-shrink-0 mt-0.5 transition-transform duration-150 ${expanded === item.id ? "rotate-180" : ""}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>
              {expanded === item.id && (
                <div className="px-4 pb-3 bg-muted/20">
                  <div className="flex items-center gap-3 mb-2 text-[10px] text-muted-foreground font-mono">
                    <span>调用 {item.llmCalls} 次</span>
                    <span>·</span>
                    <span>{item.promptTokens} tokens</span>
                    <span>·</span>
                    <span>{item.inputLength} 字符</span>
                    {item.durationMs != null && item.durationMs > 0 && (
                      <>
                        <span>·</span>
                        <span className="text-cyan-600">耗时 {item.durationMs < 1000 ? `${item.durationMs}ms` : `${(item.durationMs / 1000).toFixed(1)}s`}</span>
                      </>
                    )}
                  </div>
                  <div className="text-xs text-foreground leading-relaxed bg-background/60 rounded p-2.5 border border-border/40 max-h-40 overflow-y-auto">
                    <Streamdown>{item.summaryText}</Streamdown>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Demo() {
  const { user } = useAuth();
  const [content, setContent] = useState("");
  const [domain, setDomain] = useState<"email" | "news">("email");
  const [result, setResult] = useState<{
    summary: string;
    trace: {
      llmCalls: number;
      promptTokens: number;
      stages: string[];
      domain: string;
      isMapReduce: boolean;
      model?: string;
      durationMs?: number;
    };
  } | null>(null);

  const { model, apiKey, setModel, setApiKey } = useModelKeyState();
  const utils = trpc.useUtils();

  const mutation = trpc.summarize.single.useMutation({
    onSuccess: (data) => {
      setResult(data);
      // Refresh history list after new summary
      utils.history.list.invalidate();
    },
  });

  const handleSubmit = () => {
    if (!content.trim()) return;
    setResult(null);
    mutation.mutate({
      content,
      domain,
      userId: user?.id,
      model: model || undefined,
      apiKey: apiKey || undefined,
    });
  };

  const loadSample = () => {
    setContent(SAMPLE_TEXTS[domain]);
    setResult(null);
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
            <span className="text-sm text-muted-foreground">单篇摘要演示</span>
          </div>
          <div className="flex items-center gap-2">
            {[
              { href: "/multidoc", label: "多文档" },
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
          <div className="mono-label text-[11px] text-muted-foreground mb-2">// single_doc_summarizer.demo</div>
          <h1 className="text-4xl font-black mb-2">单篇摘要演示</h1>
          <p className="text-muted-foreground text-sm">
            输入文本，选择场景，实时查看摘要结果与处理 Trace。长文本自动触发 Map-Reduce 并行处理。
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Input */}
          <div className="space-y-4">
            {/* Domain selector */}
            <div className="blueprint-card rounded-xl border border-border/60 p-4">
              <div className="mono-label text-[11px] text-muted-foreground mb-3">// domain_selector</div>
              <div className="flex gap-2">
                {(["email", "news"] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => { setDomain(d); setContent(""); setResult(null); }}
                    className={`flex-1 py-2.5 rounded-lg text-sm font-semibold border transition-all duration-150 ${
                      domain === d
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-transparent text-muted-foreground border-border hover:border-primary/50 hover:text-foreground"
                    }`}
                  >
                    {d === "email" ? "📧 邮件" : "📰 新闻"}
                  </button>
                ))}
              </div>
            </div>

            {/* Text input */}
            <div className="blueprint-card rounded-xl border border-border/60 p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="mono-label text-[11px] text-muted-foreground">// input_text</span>
                <button
                  onClick={loadSample}
                  className="text-xs text-primary hover:text-primary/80 font-mono underline underline-offset-2 transition-colors"
                >
                  加载示例文本
                </button>
              </div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={`粘贴${domain === "email" ? "邮件" : "新闻"}文本，或点击"加载示例文本"...`}
                className="w-full h-72 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none font-mono leading-relaxed"
              />
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/40">
                <span className="mono-label text-[10px] text-muted-foreground">
                  {content.length} chars · ~{Math.ceil(content.length / 4)} tokens
                  {content.length > 10000 && (
                    <span className="ml-2 text-cyan-600">⚡ Map-Reduce 模式</span>
                  )}
                </span>
                <button
                  onClick={handleSubmit}
                  disabled={!content.trim() || mutation.isPending}
                  className="flex items-center gap-2 px-5 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 active:scale-[0.97]"
                >
                  {mutation.isPending ? (
                    <>
                      <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      处理中...
                    </>
                  ) : (
                    <>
                      生成摘要
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* History panel (below input on left column) */}
            <HistoryPanel userId={user?.id} />
          </div>

          {/* Right: Result */}
          <div className="space-y-4">
            {mutation.isPending && (
              <div className="blueprint-card rounded-xl border border-border/60 p-8 flex flex-col items-center justify-center gap-4">
                <div className="relative w-12 h-12">
                  <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
                  <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                </div>
                <div className="text-center">
                  <div className="text-sm font-semibold text-foreground mb-1">正在生成摘要</div>
                  <div className="mono-label text-[11px] text-muted-foreground">
                    {content.length > 10000 ? "长文本 → 分块 → Map-Reduce 并行处理..." : "调用 LLM 生成摘要..."}
                  </div>
                </div>
              </div>
            )}

            {mutation.isError && (
              <div className="blueprint-card rounded-xl border border-red-200 p-4">
                <div className="flex items-center gap-2 text-red-600">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="text-sm font-medium">生成失败，请重试</span>
                </div>
                <p className="text-xs text-red-500 mt-1 font-mono">{mutation.error?.message}</p>
              </div>
            )}

            {result && !mutation.isPending && (
              <>
                <TracePanel trace={result.trace} />
                <div className="blueprint-card rounded-xl border border-border/60 p-4">
                  <div className="mono-label text-[11px] text-muted-foreground mb-3">// summary_output</div>
                  <div className="prose prose-sm max-w-none text-foreground">
                    <Streamdown>{result.summary}</Streamdown>
                  </div>
                </div>
              </>
            )}

            {!result && !mutation.isPending && !mutation.isError && (
              <div className="blueprint-card rounded-xl border border-dashed border-border/60 p-8 flex flex-col items-center justify-center gap-3 text-center">
                <div className="w-12 h-12 rounded-full border-2 border-border/40 flex items-center justify-center">
                  <svg className="w-5 h-5 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">摘要结果将在此显示</div>
                  <div className="mono-label text-[10px] text-muted-foreground/50 mt-1">// awaiting_input</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
