import { Link } from "wouter";

// ─── Blueprint SVG Architecture Diagram ───
function ArchDiagram() {
  return (
    <svg viewBox="0 0 800 320" className="w-full max-w-3xl mx-auto" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
      {/* Background grid */}
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="oklch(0.86 0.015 220 / 0.4)" strokeWidth="0.5" />
        </pattern>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill="oklch(0.52 0.18 220)" />
        </marker>
        <marker id="arrow-cyan" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill="oklch(0.60 0.16 195)" />
        </marker>
      </defs>
      <rect width="800" height="320" fill="url(#grid)" />

      {/* Input Box */}
      <rect x="20" y="120" width="130" height="80" rx="4" fill="none" stroke="oklch(0.52 0.18 220)" strokeWidth="1.5" />
      <text x="85" y="153" textAnchor="middle" fontSize="11" fill="oklch(0.12 0.02 240)" fontWeight="600">INPUT</text>
      <text x="85" y="170" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.03 220)">邮件 / 新闻</text>
      <text x="85" y="185" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.03 220)">长文本</text>

      {/* Arrow: Input → Intent */}
      <line x1="150" y1="160" x2="200" y2="160" stroke="oklch(0.52 0.18 220)" strokeWidth="1.5" markerEnd="url(#arrow)" />
      <text x="175" y="152" textAnchor="middle" fontSize="8" fill="oklch(0.52 0.18 220)">detect</text>

      {/* Intent Box */}
      <rect x="200" y="120" width="120" height="80" rx="4" fill="none" stroke="oklch(0.60 0.16 195)" strokeWidth="1.5" />
      <text x="260" y="153" textAnchor="middle" fontSize="11" fill="oklch(0.12 0.02 240)" fontWeight="600">INTENT</text>
      <text x="260" y="170" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.03 220)">domain plugin</text>
      <text x="260" y="185" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.03 220)">rule engine</text>

      {/* Arrow: Intent → Chunker */}
      <line x1="320" y1="160" x2="370" y2="160" stroke="oklch(0.52 0.18 220)" strokeWidth="1.5" markerEnd="url(#arrow)" />
      <text x="345" y="152" textAnchor="middle" fontSize="8" fill="oklch(0.52 0.18 220)">chunk</text>

      {/* Chunker Box */}
      <rect x="370" y="100" width="120" height="120" rx="4" fill="none" stroke="oklch(0.65 0.18 345)" strokeWidth="1.5" />
      <text x="430" y="130" textAnchor="middle" fontSize="11" fill="oklch(0.12 0.02 240)" fontWeight="600">CHUNKER</text>
      <text x="430" y="148" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.03 220)">recursive</text>
      <text x="430" y="163" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.03 220)">/ agentic</text>
      {/* Chunk lines */}
      <rect x="385" y="172" width="90" height="8" rx="2" fill="oklch(0.65 0.18 345 / 0.3)" stroke="oklch(0.65 0.18 345)" strokeWidth="0.8" />
      <rect x="385" y="184" width="70" height="8" rx="2" fill="oklch(0.65 0.18 345 / 0.3)" stroke="oklch(0.65 0.18 345)" strokeWidth="0.8" />
      <rect x="385" y="196" width="80" height="8" rx="2" fill="oklch(0.65 0.18 345 / 0.3)" stroke="oklch(0.65 0.18 345)" strokeWidth="0.8" />

      {/* Arrows: Chunker → Map LLMs */}
      <line x1="490" y1="130" x2="540" y2="80" stroke="oklch(0.60 0.16 195)" strokeWidth="1.2" markerEnd="url(#arrow-cyan)" strokeDasharray="4,2" />
      <line x1="490" y1="160" x2="540" y2="160" stroke="oklch(0.60 0.16 195)" strokeWidth="1.2" markerEnd="url(#arrow-cyan)" strokeDasharray="4,2" />
      <line x1="490" y1="190" x2="540" y2="240" stroke="oklch(0.60 0.16 195)" strokeWidth="1.2" markerEnd="url(#arrow-cyan)" strokeDasharray="4,2" />

      {/* Map LLM boxes */}
      {[60, 140, 220].map((y, i) => (
        <g key={i}>
          <rect x="540" y={y} width="80" height="40" rx="3" fill="none" stroke="oklch(0.60 0.16 195)" strokeWidth="1.2" />
          <text x="580" y={y + 16} textAnchor="middle" fontSize="9" fill="oklch(0.12 0.02 240)" fontWeight="600">LLM MAP</text>
          <text x="580" y={y + 30} textAnchor="middle" fontSize="8" fill="oklch(0.52 0.03 220)">chunk {i + 1}</text>
        </g>
      ))}

      {/* Arrows: Map → Reduce */}
      <line x1="620" y1="80" x2="660" y2="130" stroke="oklch(0.52 0.18 220)" strokeWidth="1.2" markerEnd="url(#arrow)" />
      <line x1="620" y1="160" x2="660" y2="160" stroke="oklch(0.52 0.18 220)" strokeWidth="1.2" markerEnd="url(#arrow)" />
      <line x1="620" y1="240" x2="660" y2="190" stroke="oklch(0.52 0.18 220)" strokeWidth="1.2" markerEnd="url(#arrow)" />

      {/* Reduce Box */}
      <rect x="660" y="120" width="110" height="80" rx="4" fill="none" stroke="oklch(0.52 0.18 220)" strokeWidth="1.8" />
      <text x="715" y="153" textAnchor="middle" fontSize="11" fill="oklch(0.12 0.02 240)" fontWeight="700">REDUCE</text>
      <text x="715" y="170" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.18 220)">aggregate</text>
      <text x="715" y="185" textAnchor="middle" fontSize="9" fill="oklch(0.52 0.18 220)">→ summary</text>

      {/* Labels */}
      <text x="430" y="260" textAnchor="middle" fontSize="8" fill="oklch(0.52 0.03 220)">// AgenticChunker</text>
      <text x="580" y="280" textAnchor="middle" fontSize="8" fill="oklch(0.60 0.16 195)">// parallel map()</text>
      <text x="715" y="260" textAnchor="middle" fontSize="8" fill="oklch(0.52 0.18 220)">// reduce()</text>

      {/* Overflow Guard label */}
      <rect x="20" y="240" width="150" height="30" rx="3" fill="none" stroke="oklch(0.65 0.18 345 / 0.6)" strokeWidth="1" strokeDasharray="3,2" />
      <text x="95" y="259" textAnchor="middle" fontSize="9" fill="oklch(0.65 0.18 345)">⚡ OverflowGuard L1-L3</text>
    </svg>
  );
}

// ─── Feature Card ───
interface FeatureCardProps {
  icon: string;
  title: string;
  desc: string;
  tag: string;
  color: "blue" | "cyan" | "pink";
}
function FeatureCard({ icon, title, desc, tag, color }: FeatureCardProps) {
  const borderColor = {
    blue: "border-blue-300/60 hover:border-blue-400",
    cyan: "border-cyan-300/60 hover:border-cyan-400",
    pink: "border-pink-300/60 hover:border-pink-400",
  }[color];
  const tagColor = {
    blue: "text-blue-600 bg-blue-50",
    cyan: "text-cyan-700 bg-cyan-50",
    pink: "text-pink-600 bg-pink-50",
  }[color];

  return (
    <div className={`blueprint-card rounded-lg p-5 border transition-all duration-200 ${borderColor} group`}>
      <div className="flex items-start gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-bold text-sm text-foreground">{title}</h3>
            <span className={`mono-label px-1.5 py-0.5 rounded text-[10px] ${tagColor}`}>{tag}</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Nav ───
function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/60 bg-background/90 backdrop-blur-md">
      <div className="container flex items-center justify-between h-14">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded border-2 border-primary flex items-center justify-center">
            <div className="w-2.5 h-2.5 bg-primary rounded-sm" />
          </div>
          <span className="font-bold text-sm tracking-tight">AgenticX Summarizer</span>
          <span className="mono-label text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">v2.0</span>
        </div>
        <div className="flex items-center gap-1">
          {[
            { href: "/demo", label: "演示" },
            { href: "/multidoc", label: "多文档" },
            { href: "/docs", label: "API 文档" },
            { href: "/history", label: "历史" },
          ].map((item) => (
            <Link key={item.href} href={item.href} className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors">
              {item.label}
            </Link>
          ))}
          <a
            href="https://github.com/DemonDamon/AgenticX-LongTextSummarizer"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 flex items-center gap-1.5 px-3 py-1.5 text-sm bg-foreground text-background rounded-md hover:bg-foreground/90 transition-colors"
          >
            <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 fill-current">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            GitHub
          </a>
        </div>
      </div>
    </nav>
  );
}

export default function Home() {
  return (
    <div className="min-h-screen blueprint-bg">
      <Nav />

      {/* Hero */}
      <section className="pt-32 pb-20 relative overflow-hidden">
        {/* Decorative geometric elements */}
        <div className="absolute top-20 right-10 w-64 h-64 rounded-full border border-cyan-300/30 pointer-events-none" />
        <div className="absolute top-32 right-24 w-40 h-40 rounded-full border border-pink-300/20 pointer-events-none" />
        <div className="absolute bottom-10 left-10 w-32 h-32 border border-blue-300/20 rotate-45 pointer-events-none" />

        <div className="container relative">
          <div className="max-w-4xl">
            {/* Tag */}
            <div className="flex items-center gap-2 mb-6">
              <span className="mono-label text-[11px] border border-primary/40 text-primary px-2 py-1 rounded">
                AGENTICX FRAMEWORK
              </span>
              <span className="mono-label text-[11px] text-muted-foreground">// long-text-summarizer v2.0</span>
            </div>

            {/* Title */}
            <h1 className="text-6xl font-black tracking-tight text-foreground leading-none mb-4">
              智能长文本
              <br />
              <span className="text-primary">摘要引擎</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mb-8 leading-relaxed">
              基于 AgenticX 框架构建的业务无关摘要内核。通过{" "}
              <span className="font-mono text-sm text-primary">Map-Reduce</span> 并行处理、
              语义分块与多级溢出恢复，轻松应对邮件、新闻等场景的万字长文。
            </p>

            {/* CTA */}
            <div className="flex items-center gap-3 flex-wrap">
              <Link href="/demo" className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-lg hover:bg-primary/90 transition-all duration-150 active:scale-[0.97]">
                <span>立即体验</span>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link href="/multidoc" className="inline-flex items-center gap-2 px-6 py-3 border border-border text-foreground font-semibold rounded-lg hover:bg-muted transition-all duration-150 active:scale-[0.97]">
                多文档对比
              </Link>
              <a
                href="https://github.com/DemonDamon/AgenticX-LongTextSummarizer"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 border border-border text-muted-foreground font-semibold rounded-lg hover:bg-muted transition-all duration-150 active:scale-[0.97]"
              >
                <svg viewBox="0 0 16 16" className="w-4 h-4 fill-current">
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
                </svg>
                查看源码
              </a>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-8 mt-10 pt-8 border-t border-border/50">
              {[
                { value: "Map-Reduce", label: "并行处理架构" },
                { value: "L1-L3", label: "溢出恢复等级" },
                { value: "120K", label: "最大 Token 支持" },
                { value: "∞", label: "可插拔领域插件" },
              ].map((stat) => (
                <div key={stat.label}>
                  <div className="font-mono font-bold text-xl text-primary">{stat.value}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Architecture Diagram */}
      <section className="py-16 border-t border-border/40">
        <div className="container">
          <div className="flex items-center gap-3 mb-8">
            <span className="mono-label text-[11px] text-muted-foreground">// architecture_overview.svg</span>
            <div className="flex-1 h-px bg-border/50" />
          </div>
          <h2 className="text-3xl font-black mb-2">架构概览</h2>
          <p className="text-muted-foreground text-sm mb-8">Map-Reduce 并行摘要流水线</p>
          <div className="blueprint-card rounded-xl p-6 border border-border/60">
            <ArchDiagram />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 border-t border-border/40">
        <div className="container">
          <div className="flex items-center gap-3 mb-8">
            <span className="mono-label text-[11px] text-muted-foreground">// core_features[]</span>
            <div className="flex-1 h-px bg-border/50" />
          </div>
          <h2 className="text-3xl font-black mb-2">核心特性</h2>
          <p className="text-muted-foreground text-sm mb-8">AgenticX 框架底层能力的完整释放</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <FeatureCard
              icon="⚡"
              title="Map-Reduce 并行处理"
              desc="自动对超长文本进行语义分块，并行生成局部摘要后全局聚合，轻松应对万字长文，避免 Lost in the Middle 问题。"
              tag="core"
              color="blue"
            />
            <FeatureCard
              icon="✂️"
              title="智能语义分块"
              desc="内置 RecursiveChunker 与 AgenticChunker，按段落语义边界切分，保证每块内容完整，避免信息截断。"
              tag="chunking"
              color="cyan"
            />
            <FeatureCard
              icon="🛡️"
              title="多级 Token 溢出恢复"
              desc="内置资源评估与 OverflowGuard，当输入超过模型安全上下文时，自动触发 L1-L3 多级截断或紧急压缩策略。"
              tag="safety"
              color="pink"
            />
            <FeatureCard
              icon="🧩"
              title="可插拔领域插件"
              desc="核心引擎与业务解耦，邮件（Email）和新闻（News）作为独立 DomainPlugin 接入，各自维护规则引擎和 Prompt 策略。"
              tag="plugin"
              color="blue"
            />
            <FeatureCard
              icon="📚"
              title="多文档跨篇摘要"
              desc="支持对多篇独立文档进行单篇摘要后，执行聚合（aggregate）、对比（compare）或时间线（timeline）分析。"
              tag="multidoc"
              color="cyan"
            />
            <FeatureCard
              icon="🧠"
              title="个性化 Prompt 记忆"
              desc="PersonalizationStore 记录用户反馈与偏好，在运行时动态注入 Prompt，实现越用越懂你的摘要体验。"
              tag="agentic"
              color="pink"
            />
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="py-16 border-t border-border/40">
        <div className="container">
          <div className="flex items-center gap-3 mb-8">
            <span className="mono-label text-[11px] text-muted-foreground">// quick_start.sh</span>
            <div className="flex-1 h-px bg-border/50" />
          </div>
          <h2 className="text-3xl font-black mb-8">快速开始</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "单篇摘要演示",
                desc: "输入邮件或新闻文本，选择场景，实时查看摘要结果与 Trace 信息。",
                href: "/demo",
                cta: "进入演示",
              },
              {
                step: "02",
                title: "多文档对比",
                desc: "添加多篇文档，选择 compare / aggregate / timeline 意图，获取跨篇综合结论。",
                href: "/multidoc",
                cta: "多文档演示",
              },
              {
                step: "03",
                title: "API 文档",
                desc: "查看完整 API 端点说明、请求响应示例和 curl 调用示例，一键复制代码。",
                href: "/docs",
                cta: "查看文档",
              },
            ].map((item) => (
              <div key={item.step} className="blueprint-card rounded-xl p-6 border border-border/60">
                <div className="mono-label text-3xl font-black text-primary/20 mb-3">{item.step}</div>
                <h3 className="font-bold text-base mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground mb-4 leading-relaxed">{item.desc}</p>
                <Link href={item.href} className="inline-flex items-center gap-1 text-sm text-primary font-medium hover:gap-2 transition-all">
                  {item.cta}
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-border/40">
        <div className="container flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm">AgenticX-LongTextSummarizer</span>
            <span className="mono-label text-[10px] text-muted-foreground">// MIT License</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/DemonDamon/AgenticX-LongTextSummarizer"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://github.com/DemonDamon/AgenticX"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              AgenticX Framework
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
