import { useState } from "react";
import { Link } from "wouter";

interface CodeBlockProps {
  code: string;
  lang?: string;
}
function CodeBlock({ code, lang = "bash" }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="relative group rounded-lg overflow-hidden border border-border/60 bg-muted/30">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/40 bg-muted/50">
        <span className="mono-label text-[10px] text-muted-foreground">{lang}</span>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {copied ? (
            <>
              <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-500">已复制</span>
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              复制
            </>
          )}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-xs leading-relaxed text-foreground font-mono whitespace-pre">{code}</pre>
    </div>
  );
}

const ENDPOINTS = [
  {
    id: "single",
    method: "POST",
    path: "/api/trpc/summarize.single",
    title: "单篇文本摘要",
    desc: "对单篇文本进行摘要。短文本（<2500 tokens）直接调用 LLM；长文本自动触发分块 + Map-Reduce 并行处理。",
    request: `{
  "content": "文本内容（10 - 100000 字符）",
  "domain": "email" | "news",
  "userId": 123  // 可选，登录用户 ID，用于保存历史
}`,
    response: `{
  "result": {
    "data": {
      "summary": "生成的摘要文本",
      "trace": {
        "llmCalls": 1,           // 调用次数
        "promptTokens": 352,     // Token 消耗
        "stages": ["single"],    // 处理阶段: single | [map, reduce]
        "domain": "email",
        "isMapReduce": false
      }
    }
  }
}`,
    curl: `curl -X POST https://your-domain.manus.space/api/trpc/summarize.single \\
  -H "Content-Type: application/json" \\
  -d '{
    "json": {
      "content": "发件人：张伟\\n主题：Q3产品路线图评审会议纪要\\n\\n各位同事，以下是今天会议的纪要...",
      "domain": "email"
    }
  }'`,
  },
  {
    id: "collection",
    method: "POST",
    path: "/api/trpc/summarize.collection",
    title: "多文档聚合摘要",
    desc: "对多篇文档（1-10 篇）进行并行摘要后，按指定意图（compare / aggregate / timeline）执行跨篇聚合分析。",
    request: `{
  "docs": [
    {
      "docId": "doc-1",
      "title": "文档标题（可选）",
      "content": "文档内容",
      "domain": "news"
    }
  ],
  "intent": "compare" | "aggregate" | "timeline"
}`,
    response: `{
  "result": {
    "data": {
      "crossSummary": "跨篇综合结论",
      "perDoc": [
        {
          "docId": "doc-1",
          "title": "文档标题",
          "summary": "单篇摘要"
        }
      ],
      "trace": {
        "llmCalls": 4,           // 调用次数（各篇 + 聚合）
        "promptTokens": 1240,    // Token 消耗
        "intent": "compare",     // 处理阶段
        "docCount": 3
      }
    }
  }
}`,
    curl: `curl -X POST https://your-domain.manus.space/api/trpc/summarize.collection \\
  -H "Content-Type: application/json" \\
  -d '{
    "json": {
      "docs": [
        {"docId": "d1", "title": "GPT-5 发布", "content": "...", "domain": "news"},
        {"docId": "d2", "title": "Claude 4 报告", "content": "...", "domain": "news"}
      ],
      "intent": "compare"
    }
  }'`,
  },
  {
    id: "history",
    method: "GET",
    path: "/api/trpc/history.list",
    title: "摘要历史记录",
    desc: "获取当前登录用户的摘要历史记录（最近 50 条）。需要登录认证。",
    request: `// GET 请求，无请求体
// 需要携带 session cookie（登录后自动携带）`,
    response: `{
  "result": {
    "data": [
      {
        "id": 1,
        "userId": 123,
        "domain": "email",
        "inputSnippet": "发件人：张伟...",
        "inputLength": 856,
        "summaryText": "会议纪要摘要...",
        "llmCalls": 1,
        "promptTokens": 352,
        "stages": "single",
        "createdAt": "2024-07-14T08:00:00.000Z"
      }
    ]
  }
}`,
    curl: `curl https://your-domain.manus.space/api/trpc/history.list \\
  -H "Cookie: session=<your-session-cookie>"`,
  },
];

export default function Docs() {
  const [activeEndpoint, setActiveEndpoint] = useState("single");

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
            <span className="text-sm text-muted-foreground">API 文档</span>
          </div>
          <div className="flex items-center gap-2">
            {[
              { href: "/demo", label: "单篇演示" },
              { href: "/multidoc", label: "多文档" },
              { href: "/history", label: "历史" },
            ].map((item) => (
              <Link key={item.href} href={item.href} className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors">
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      <div className="container pt-24 pb-16">
        <div className="mb-8">
          <div className="mono-label text-[11px] text-muted-foreground mb-2">// api_reference.docs</div>
          <h1 className="text-4xl font-black mb-2">API 文档</h1>
          <p className="text-muted-foreground text-sm">
            所有 API 通过 tRPC 协议暴露，兼容标准 HTTP POST/GET 调用。
          </p>
        </div>

        {/* Base URL */}
        <div className="blueprint-card rounded-xl border border-border/60 p-4 mb-8">
          <div className="mono-label text-[11px] text-muted-foreground mb-2">// base_url</div>
          <div className="flex items-center gap-3">
            <code className="font-mono text-sm text-primary bg-primary/5 px-3 py-1.5 rounded">
              https://your-domain.manus.space/api/trpc
            </code>
            <span className="text-xs text-muted-foreground">tRPC v11 · HTTP Batch · Superjson</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="blueprint-card rounded-xl border border-border/60 overflow-hidden sticky top-20">
              <div className="px-4 py-2.5 bg-muted/50 border-b border-border/40">
                <span className="mono-label text-[11px] text-muted-foreground">// endpoints[]</span>
              </div>
              <div className="p-2">
                {ENDPOINTS.map((ep) => (
                  <button
                    key={ep.id}
                    onClick={() => setActiveEndpoint(ep.id)}
                    className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left transition-colors ${
                      activeEndpoint === ep.id
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    }`}
                  >
                    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                      ep.method === "POST" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
                    }`}>
                      {ep.method}
                    </span>
                    <span className="text-xs font-medium truncate">{ep.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            {ENDPOINTS.filter((ep) => ep.id === activeEndpoint).map((ep) => (
              <div key={ep.id} className="space-y-6">
                {/* Endpoint header */}
                <div className="blueprint-card rounded-xl border border-border/60 p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`text-xs font-mono font-bold px-2 py-1 rounded ${
                      ep.method === "POST" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
                    }`}>
                      {ep.method}
                    </span>
                    <code className="font-mono text-sm text-foreground">{ep.path}</code>
                  </div>
                  <h2 className="text-xl font-black mb-2">{ep.title}</h2>
                  <p className="text-sm text-muted-foreground leading-relaxed">{ep.desc}</p>
                </div>

                {/* Request */}
                <div>
                  <div className="mono-label text-[11px] text-muted-foreground mb-2">// request_body</div>
                  <CodeBlock code={ep.request} lang="json" />
                </div>

                {/* Response */}
                <div>
                  <div className="mono-label text-[11px] text-muted-foreground mb-2">// response_body</div>
                  <CodeBlock code={ep.response} lang="json" />
                </div>

                {/* cURL */}
                <div>
                  <div className="mono-label text-[11px] text-muted-foreground mb-2">// curl_example</div>
                  <CodeBlock code={ep.curl} lang="bash" />
                </div>

                {/* Trace fields */}
                {ep.id !== "history" && (
                  <div className="blueprint-card rounded-xl border border-border/60 overflow-hidden">
                    <div className="px-4 py-2.5 bg-muted/50 border-b border-border/40">
                      <span className="mono-label text-[11px] text-muted-foreground">// trace_fields</span>
                    </div>
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border/40">
                          <th className="text-left px-4 py-2 font-mono text-muted-foreground">字段</th>
                          <th className="text-left px-4 py-2 font-mono text-muted-foreground">类型</th>
                          <th className="text-left px-4 py-2 font-mono text-muted-foreground">说明</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/30">
                        <tr>
                          <td className="px-4 py-2 font-mono text-primary">llmCalls</td>
                          <td className="px-4 py-2 text-muted-foreground">number</td>
                          <td className="px-4 py-2 text-muted-foreground">LLM 调用次数（单篇=1，Map-Reduce=N+1）</td>
                        </tr>
                        <tr>
                          <td className="px-4 py-2 font-mono text-primary">promptTokens</td>
                          <td className="px-4 py-2 text-muted-foreground">number</td>
                          <td className="px-4 py-2 text-muted-foreground">输入 Token 消耗估算</td>
                        </tr>
                        <tr>
                          <td className="px-4 py-2 font-mono text-primary">stages</td>
                          <td className="px-4 py-2 text-muted-foreground">string[]</td>
                          <td className="px-4 py-2 text-muted-foreground">处理阶段：["single"] 或 ["map", "reduce"]</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
