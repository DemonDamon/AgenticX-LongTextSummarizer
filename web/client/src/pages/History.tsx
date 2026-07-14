import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { trpc } from "@/lib/trpc";
import { useState } from "react";
import { Streamdown } from "streamdown";
import { Link } from "wouter";

function formatDate(d: Date) {
  return new Date(d).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function History() {
  const { user, isAuthenticated, loading } = useAuth();
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: history, isLoading } = trpc.history.list.useQuery(undefined, {
    enabled: isAuthenticated,
  });

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
            <span className="text-sm text-muted-foreground">历史记录</span>
          </div>
          <div className="flex items-center gap-2">
            {[
              { href: "/demo", label: "单篇演示" },
              { href: "/multidoc", label: "多文档" },
              { href: "/docs", label: "API 文档" },
            ].map((item) => (
              <Link key={item.href} href={item.href} className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors">
                {item.label}
              </Link>
            ))}
            {isAuthenticated && user && (
              <div className="flex items-center gap-2 ml-2 px-3 py-1.5 bg-muted rounded-lg">
                <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">
                  {user.name?.charAt(0) ?? "U"}
                </div>
                <span className="text-xs text-muted-foreground">{user.name}</span>
              </div>
            )}
          </div>
        </div>
      </nav>

      <div className="container pt-24 pb-16">
        <div className="mb-8">
          <div className="mono-label text-[11px] text-muted-foreground mb-2">// summary_history.log</div>
          <h1 className="text-4xl font-black mb-2">摘要历史记录</h1>
          <p className="text-muted-foreground text-sm">
            查看您的历史摘要记录，包含输入片段、场景、处理 Trace 和摘要结果。
          </p>
        </div>

        {/* Not logged in */}
        {!loading && !isAuthenticated && (
          <div className="blueprint-card rounded-2xl border border-border/60 p-16 flex flex-col items-center justify-center gap-5 text-center max-w-md mx-auto">
            <div className="w-16 h-16 rounded-full border-2 border-border/40 flex items-center justify-center">
              <svg className="w-7 h-7 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <div className="text-base font-bold mb-1">需要登录</div>
              <div className="text-sm text-muted-foreground">历史记录仅对已登录用户开放</div>
              <div className="mono-label text-[10px] text-muted-foreground/50 mt-1">// auth_required: true</div>
            </div>
            <button
              onClick={() => startLogin()}
              className="px-6 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 transition-all duration-150 active:scale-[0.97]"
            >
              登录账号
            </button>
          </div>
        )}

        {/* Loading */}
        {isAuthenticated && isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="relative w-10 h-10">
              <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
              <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            </div>
          </div>
        )}

        {/* Empty */}
        {isAuthenticated && !isLoading && history?.length === 0 && (
          <div className="blueprint-card rounded-2xl border border-dashed border-border/60 p-16 flex flex-col items-center justify-center gap-4 text-center max-w-md mx-auto">
            <div className="w-14 h-14 rounded-full border-2 border-border/40 flex items-center justify-center">
              <svg className="w-6 h-6 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">暂无历史记录</div>
              <div className="mono-label text-[10px] text-muted-foreground/50 mt-1">// records: []</div>
            </div>
            <Link href="/demo" className="text-sm text-primary hover:text-primary/80 font-medium">去生成第一条摘要 →</Link>
          </div>
        )}

        {/* History list */}
        {isAuthenticated && !isLoading && history && history.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-4">
              <span className="mono-label text-[11px] text-muted-foreground">共 {history.length} 条记录</span>
              <div className="flex-1 h-px bg-border/40" />
            </div>
            {history.map((item) => (
              <div key={item.id} className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                <button
                  onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  className="w-full px-5 py-4 flex items-start gap-4 text-left hover:bg-muted/20 transition-colors"
                >
                  {/* Domain badge */}
                  <div className={`flex-shrink-0 mt-0.5 px-2 py-1 rounded text-[11px] font-mono font-bold ${
                    item.domain === "email"
                      ? "bg-blue-50 text-blue-700"
                      : "bg-cyan-50 text-cyan-700"
                  }`}>
                    {item.domain === "email" ? "邮件" : "新闻"}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-foreground truncate font-medium mb-1">
                      {item.inputSnippet}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="mono-label text-[10px] text-muted-foreground">
                        {formatDate(item.createdAt)}
                      </span>
                      <span className="mono-label text-[10px] text-muted-foreground">
                        {item.inputLength} chars
                      </span>
                      <span className="mono-label text-[10px] text-primary">
                        {item.llmCalls} calls · {item.promptTokens} tokens
                      </span>
                      <span className="mono-label text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                        {item.stages}
                      </span>
                      {item.durationMs != null && item.durationMs > 0 && (
                        <span className="mono-label text-[10px] text-cyan-600">
                          ⏱ {item.durationMs < 1000 ? `${item.durationMs}ms` : `${(item.durationMs / 1000).toFixed(1)}s`}
                        </span>
                      )}
                    </div>
                  </div>

                  <svg
                    className={`w-4 h-4 text-muted-foreground flex-shrink-0 mt-1 transition-transform ${expandedId === item.id ? "rotate-180" : ""}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {expandedId === item.id && (
                  <div className="px-5 pb-5 border-t border-border/40 pt-4">
                    <div className="grid grid-cols-4 gap-3 mb-4 p-3 bg-muted/30 rounded-lg">
                      <div className="text-center">
                        <div className="text-lg font-black font-mono text-primary">{item.llmCalls}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">调用次数</div>
                      </div>
                      <div className="text-center border-x border-border/40">
                        <div className="text-lg font-black font-mono text-primary">{item.promptTokens}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">Token 消耗</div>
                      </div>
                      <div className="text-center border-r border-border/40">
                        <div className="text-lg font-black font-mono text-cyan-600">
                          {item.durationMs != null && item.durationMs > 0
                            ? (item.durationMs < 1000 ? `${item.durationMs}ms` : `${(item.durationMs / 1000).toFixed(1)}s`)
                            : '—'}
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">耗时</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[11px] font-mono text-foreground font-semibold">{item.stages}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">处理阶段</div>
                      </div>
                    </div>
                    <div className="mono-label text-[11px] text-muted-foreground mb-2">// summary_output</div>
                    <div className="text-sm text-foreground leading-relaxed">
                      <Streamdown>{item.summaryText}</Streamdown>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
