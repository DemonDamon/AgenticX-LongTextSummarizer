import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { trpc } from "@/lib/trpc";
import { useState } from "react";
import { Streamdown } from "streamdown";
import { Link } from "wouter";
import * as XLSX from "xlsx";

function formatDate(d: Date) {
  return new Date(d).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(ms: number | null | undefined) {
  if (!ms || ms <= 0) return "—";
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

// ─── Export helpers ───
function exportSingleToCSV(records: SingleRecord[]) {
  const header = ["ID", "时间", "场景", "输入片段", "输入字符数", "摘要文本", "调用次数", "Token消耗", "耗时(ms)", "处理阶段", "模型"];
  const rows = records.map((r) => [
    r.id,
    formatDate(r.createdAt),
    r.domain,
    r.inputSnippet,
    r.inputLength,
    r.summaryText,
    r.llmCalls,
    r.promptTokens,
    r.durationMs ?? "",
    r.stages,
    r.model ?? "",
  ]);
  const csv = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `single_summary_history_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportSingleToExcel(records: SingleRecord[]) {
  const ws_data = [
    ["ID", "时间", "场景", "输入片段", "输入字符数", "摘要文本", "调用次数", "Token消耗", "耗时(ms)", "处理阶段", "模型"],
    ...records.map((r) => [
      r.id,
      formatDate(r.createdAt),
      r.domain,
      r.inputSnippet,
      r.inputLength,
      r.summaryText,
      r.llmCalls,
      r.promptTokens,
      r.durationMs ?? "",
      r.stages,
      r.model ?? "",
    ]),
  ];
  const ws = XLSX.utils.aoa_to_sheet(ws_data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "单篇摘要历史");
  XLSX.writeFile(wb, `single_summary_history_${Date.now()}.xlsx`);
}

function exportCollectionToCSV(records: CollectionRecord[]) {
  const header = ["ID", "时间", "意图", "文档数量", "文档片段(JSON)", "综合摘要", "调用次数", "Token消耗", "耗时(ms)", "处理阶段", "模型"];
  const rows = records.map((r) => [
    r.id,
    formatDate(r.createdAt),
    r.intent,
    r.docCount,
    (r as CollectionRecord & { docSnippets?: string }).docSnippets ?? "",
    r.synthesisText,
    r.llmCalls,
    r.promptTokens,
    r.durationMs ?? "",
    r.stages,
    r.model ?? "",
  ]);
  const csv = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `collection_history_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportCollectionToExcel(records: CollectionRecord[]) {
  const ws_data = [
    ["ID", "时间", "意图", "文档数量", "文档片段(JSON)", "综合摘要", "调用次数", "Token消耗", "耗时(ms)", "处理阶段", "模型"],
    ...records.map((r) => [
      r.id,
      formatDate(r.createdAt),
      r.intent,
      r.docCount,
      (r as CollectionRecord & { docSnippets?: string }).docSnippets ?? "",
      r.synthesisText,
      r.llmCalls,
      r.promptTokens,
      r.durationMs ?? "",
      r.stages,
      r.model ?? "",
    ]),
  ];
  const ws = XLSX.utils.aoa_to_sheet(ws_data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "多文档历史");
  XLSX.writeFile(wb, `collection_history_${Date.now()}.xlsx`);
}

type SingleRecord = {
  id: number;
  createdAt: Date;
  domain: string;
  inputSnippet: string;
  inputLength: number;
  summaryText: string;
  llmCalls: number;
  promptTokens: number;
  durationMs: number | null;
  stages: string;
  model?: string | null;
};

type CollectionRecord = {
  id: number;
  createdAt: Date;
  intent: string;
  docCount: number;
  synthesisText: string;
  llmCalls: number;
  promptTokens: number;
  durationMs: number | null;
  stages: string;
  model?: string | null;
};

const INTENT_COLORS: Record<string, string> = {
  compare: "bg-blue-50 text-blue-700",
  aggregate: "bg-green-50 text-green-700",
  timeline: "bg-purple-50 text-purple-700",
};

export default function History() {
  const { user, isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<"single" | "collection">("single");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedCollId, setExpandedCollId] = useState<number | null>(null);

  const { data: history, isLoading } = trpc.history.list.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  const { data: collectionHistory, isLoading: collLoading } = trpc.history.listCollection.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  const ExportBar = ({ onCSV, onExcel, count }: { onCSV: () => void; onExcel: () => void; count: number }) => (
    <div className="flex items-center gap-2">
      <span className="mono-label text-[11px] text-muted-foreground">共 {count} 条记录</span>
      <div className="flex-1 h-px bg-border/40" />
      <button
        onClick={onCSV}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-border rounded-lg text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors font-mono"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        CSV
      </button>
      <button
        onClick={onExcel}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-border rounded-lg text-muted-foreground hover:text-foreground hover:border-green-500/50 transition-colors font-mono"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Excel
      </button>
    </div>
  );

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
            查看历史摘要记录，包含输入片段、场景、处理 Trace 和摘要结果，支持导出 CSV / Excel 进行分析。
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

        {/* Authenticated view */}
        {isAuthenticated && (
          <>
            {/* Tabs */}
            <div className="flex items-center gap-1 mb-6 border-b border-border/40">
              <button
                onClick={() => { setActiveTab("single"); setExpandedId(null); }}
                className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
                  activeTab === "single"
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                单篇摘要
                {history && history.length > 0 && (
                  <span className="ml-2 text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded font-mono">
                    {history.length}
                  </span>
                )}
                {activeTab === "single" && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />
                )}
              </button>
              <button
                onClick={() => { setActiveTab("collection"); setExpandedCollId(null); }}
                className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
                  activeTab === "collection"
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                多文档摘要
                {collectionHistory && collectionHistory.length > 0 && (
                  <span className="ml-2 text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded font-mono">
                    {collectionHistory.length}
                  </span>
                )}
                {activeTab === "collection" && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />
                )}
              </button>
            </div>

            {/* ── Single tab ── */}
            {activeTab === "single" && (
              <>
                {isLoading && (
                  <div className="flex items-center justify-center py-20">
                    <div className="relative w-10 h-10">
                      <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
                      <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                    </div>
                  </div>
                )}

                {!isLoading && (!history || history.length === 0) && (
                  <div className="blueprint-card rounded-2xl border border-dashed border-border/60 p-16 flex flex-col items-center justify-center gap-4 text-center max-w-md mx-auto">
                    <div className="text-sm font-medium text-muted-foreground">暂无单篇摘要历史</div>
                    <Link href="/demo" className="text-sm text-primary hover:text-primary/80 font-medium">去生成第一条摘要 →</Link>
                  </div>
                )}

                {!isLoading && history && history.length > 0 && (
                  <div className="space-y-3">
                    <ExportBar
                      count={history.length}
                      onCSV={() => exportSingleToCSV(history as unknown as SingleRecord[])}
                      onExcel={() => exportSingleToExcel(history as unknown as SingleRecord[])}
                    />
                    {history.map((item) => (
                      <div key={item.id} className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                        <button
                          onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                          className="w-full px-5 py-4 flex items-start gap-4 text-left hover:bg-muted/20 transition-colors"
                        >
                          <div className={`flex-shrink-0 mt-0.5 px-2 py-1 rounded text-[11px] font-mono font-bold ${
                            item.domain === "email" ? "bg-blue-50 text-blue-700" : "bg-cyan-50 text-cyan-700"
                          }`}>
                            {item.domain === "email" ? "邮件" : "新闻"}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-foreground truncate font-medium mb-1">{item.inputSnippet}</div>
                            <div className="flex items-center gap-3 flex-wrap">
                              <span className="mono-label text-[10px] text-muted-foreground">{formatDate(item.createdAt)}</span>
                              <span className="mono-label text-[10px] text-muted-foreground">{item.inputLength} chars</span>
                              <span className="mono-label text-[10px] text-primary">{item.llmCalls} calls · {item.promptTokens} tokens</span>
                              <span className="mono-label text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded">{item.stages}</span>
                              {item.durationMs != null && item.durationMs > 0 && (
                                <span className="mono-label text-[10px] text-cyan-600">⏱ {formatDuration(item.durationMs)}</span>
                              )}
                              {item.model && (
                                <span className="mono-label text-[10px] text-muted-foreground/60">{item.model}</span>
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
                                <div className="text-lg font-black font-mono text-cyan-600">{formatDuration(item.durationMs)}</div>
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
              </>
            )}

            {/* ── Collection tab ── */}
            {activeTab === "collection" && (
              <>
                {collLoading && (
                  <div className="flex items-center justify-center py-20">
                    <div className="relative w-10 h-10">
                      <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
                      <div className="absolute inset-0 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                    </div>
                  </div>
                )}

                {!collLoading && (!collectionHistory || collectionHistory.length === 0) && (
                  <div className="blueprint-card rounded-2xl border border-dashed border-border/60 p-16 flex flex-col items-center justify-center gap-4 text-center max-w-md mx-auto">
                    <div className="text-sm font-medium text-muted-foreground">暂无多文档摘要历史</div>
                    <Link href="/multidoc" className="text-sm text-primary hover:text-primary/80 font-medium">去执行多文档分析 →</Link>
                  </div>
                )}

                {!collLoading && collectionHistory && collectionHistory.length > 0 && (
                  <div className="space-y-3">
                    <ExportBar
                      count={collectionHistory.length}
                      onCSV={() => exportCollectionToCSV(collectionHistory as unknown as CollectionRecord[])}
                      onExcel={() => exportCollectionToExcel(collectionHistory as unknown as CollectionRecord[])}
                    />
                    {collectionHistory.map((item) => (
                      <div key={item.id} className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                        <button
                          onClick={() => setExpandedCollId(expandedCollId === item.id ? null : item.id)}
                          className="w-full px-5 py-4 flex items-start gap-4 text-left hover:bg-muted/20 transition-colors"
                        >
                          {/* Intent badge */}
                          <div className={`flex-shrink-0 mt-0.5 px-2 py-1 rounded text-[11px] font-mono font-bold ${INTENT_COLORS[item.intent] ?? "bg-muted text-foreground"}`}>
                            {item.intent}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-foreground font-medium mb-1 truncate">
                              {item.docCount} 篇文档 · {item.synthesisText.slice(0, 60)}{item.synthesisText.length > 60 ? "…" : ""}
                            </div>
                            <div className="flex items-center gap-3 flex-wrap">
                              <span className="mono-label text-[10px] text-muted-foreground">{formatDate(item.createdAt)}</span>
                              <span className="mono-label text-[10px] text-primary">{item.llmCalls} calls · {item.promptTokens} tokens</span>
                              <span className="mono-label text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded">{item.stages}</span>
                              {item.durationMs != null && item.durationMs > 0 && (
                                <span className="mono-label text-[10px] text-cyan-600">⏱ {formatDuration(item.durationMs)}</span>
                              )}
                              {item.model && (
                                <span className="mono-label text-[10px] text-muted-foreground/60">{item.model}</span>
                              )}
                            </div>
                          </div>

                          <svg
                            className={`w-4 h-4 text-muted-foreground flex-shrink-0 mt-1 transition-transform ${expandedCollId === item.id ? "rotate-180" : ""}`}
                            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {expandedCollId === item.id && (
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
                                <div className="text-lg font-black font-mono text-cyan-600">{formatDuration(item.durationMs)}</div>
                                <div className="text-[10px] text-muted-foreground mt-0.5">耗时</div>
                              </div>
                              <div className="text-center">
                                <div className="text-[11px] font-mono text-foreground font-semibold">{item.stages}</div>
                                <div className="text-[10px] text-muted-foreground mt-0.5">处理阶段</div>
                              </div>
                            </div>
                            {item.model && (
                              <div className="mb-3 text-xs text-muted-foreground font-mono">
                                model: <span className="text-primary">{item.model}</span>
                              </div>
                            )}
                            <div className="mono-label text-[11px] text-muted-foreground mb-2">// synthesis_output</div>
                            <div className="text-sm text-foreground leading-relaxed">
                              <Streamdown>{item.synthesisText}</Streamdown>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
