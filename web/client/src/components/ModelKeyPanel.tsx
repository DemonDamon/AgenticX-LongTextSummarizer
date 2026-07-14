import { trpc } from "@/lib/trpc";
import { useEffect, useRef, useState } from "react";

const LS_MODEL_KEY = "agx_selected_model";
const LS_APIKEY_KEY = "agx_api_key";

// ─── Vendor grouping ───
const VENDOR_GROUPS: { label: string; flag: string; prefix: string[] }[] = [
  { label: "DeepSeek", flag: "🇨🇳", prefix: ["deepseek"] },
  { label: "Qwen (通义)", flag: "🇨🇳", prefix: ["qwen"] },
  { label: "Kimi (月之暗面)", flag: "🇨🇳", prefix: ["moonshot"] },
  { label: "GLM (智谱)", flag: "🇨🇳", prefix: ["glm"] },
  { label: "Doubao (豆包)", flag: "🇨🇳", prefix: ["doubao"] },
  { label: "Hunyuan (混元)", flag: "🇨🇳", prefix: ["hunyuan"] },
  { label: "Yi (零一万物)", flag: "🇨🇳", prefix: ["yi-"] },
  { label: "ERNIE (文心)", flag: "🇨🇳", prefix: ["ernie"] },
  { label: "Anthropic", flag: "🇺🇸", prefix: ["claude"] },
  { label: "OpenAI", flag: "🇺🇸", prefix: ["gpt"] },
  { label: "Google", flag: "🇺🇸", prefix: ["gemini"] },
];

function getVendorLabel(modelId: string): string {
  for (const g of VENDOR_GROUPS) {
    if (g.prefix.some((p) => modelId.toLowerCase().startsWith(p))) {
      return `${g.flag} ${g.label}`;
    }
  }
  return "其他";
}

function groupModels(models: string[]): { group: string; models: string[] }[] {
  const map = new Map<string, string[]>();
  for (const m of models) {
    const g = getVendorLabel(m);
    if (!map.has(g)) map.set(g, []);
    map.get(g)!.push(m);
  }
  // Sort: domestic first (🇨🇳), then foreign (🇺🇸), then others
  const order = VENDOR_GROUPS.map((g) => `${g.flag} ${g.label}`);
  const sorted = Array.from(map.entries()).sort(([a], [b]) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });
  return sorted.map(([group, models]) => ({ group, models }));
}

interface ModelKeyPanelProps {
  model: string;
  apiKey: string;
  onModelChange: (m: string) => void;
  onApiKeyChange: (k: string) => void;
}

export function useModelKeyState() {
  const [model, setModelState] = useState<string>(() => {
    try { return localStorage.getItem(LS_MODEL_KEY) ?? ""; } catch { return ""; }
  });
  const [apiKey, setApiKeyState] = useState<string>(() => {
    try { return localStorage.getItem(LS_APIKEY_KEY) ?? ""; } catch { return ""; }
  });

  const setModel = (m: string) => {
    setModelState(m);
    try { localStorage.setItem(LS_MODEL_KEY, m); } catch { /* ignore */ }
  };
  const setApiKey = (k: string) => {
    setApiKeyState(k);
    try { localStorage.setItem(LS_APIKEY_KEY, k); } catch { /* ignore */ }
  };

  return { model, apiKey, setModel, setApiKey };
}

export default function ModelKeyPanel({ model, apiKey, onModelChange, onApiKeyChange }: ModelKeyPanelProps) {
  const [open, setOpen] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [localKey, setLocalKey] = useState(apiKey);
  const panelRef = useRef<HTMLDivElement>(null);

  const { data: models = [], isLoading: loadingModels } = trpc.models.list.useQuery(
    { apiKey: apiKey || undefined },
    { staleTime: 60_000 }
  );

  const grouped = groupModels(models);
  const displayModel = model || (models[0] ?? "gemini-2.5-flash");
  const vendorLabel = getVendorLabel(displayModel);
  const isDomestic = vendorLabel.includes("🇨🇳");

  useEffect(() => { setLocalKey(apiKey); }, [apiKey]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div className="relative" ref={panelRef}>
      {/* Trigger button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border/60 bg-background hover:bg-muted transition-all duration-150 active:scale-[0.97] text-sm font-mono"
        title="模型与 API Key 设置"
      >
        <span className="text-sm leading-none">{isDomestic ? "🇨🇳" : "🌐"}</span>
        <span className="max-w-[130px] truncate text-foreground/80">{displayModel}</span>
        {apiKey && (
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" title="自定义 Key 已启用" />
        )}
        <svg className={`w-3 h-3 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-88 blueprint-card rounded-xl border border-border/60 shadow-xl z-50 p-4 space-y-4"
          style={{ width: "22rem", transformOrigin: "top right", animation: "scale-in 150ms cubic-bezier(0.23,1,0.32,1)" }}
        >
          {/* Model selector */}
          <div>
            <div className="mono-label text-[10px] text-muted-foreground mb-2">// model_selector</div>
            <label className="block text-xs font-semibold text-foreground mb-1.5">选择模型</label>
            {loadingModels ? (
              <div className="h-9 rounded-lg bg-muted animate-pulse" />
            ) : (
              <select
                value={model || displayModel}
                onChange={(e) => onModelChange(e.target.value)}
                className="w-full h-9 px-3 rounded-lg border border-border/60 bg-background text-sm font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 cursor-pointer"
                size={1}
              >
                {grouped.map(({ group, models: gModels }) => (
                  <optgroup key={group} label={group}>
                    {gModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            )}
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-muted-foreground mono-label">{models.length} 个可用模型</span>
              {isDomestic && (
                <span className="text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded mono-label">
                  国产模型需填写对应 Key
                </span>
              )}
            </div>
          </div>

          {/* Vendor hint for domestic models */}
          {isDomestic && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 space-y-1.5">
              <div className="mono-label text-[10px] text-blue-600">// domestic_model_routing</div>
              <div className="text-[11px] text-blue-700 leading-relaxed">
                选中的模型 <span className="font-mono font-bold">{displayModel}</span> 属于
                <span className="font-semibold"> {vendorLabel}</span>，
                请在下方填写该厂商的 API Key，请求将自动路由到对应端点。
              </div>
              <div className="text-[10px] text-blue-500 font-mono">
                {getEndpointHint(displayModel)}
              </div>
            </div>
          )}

          {/* API Key input */}
          <div className="border-t border-border/40 pt-4">
            <div className="mono-label text-[10px] text-muted-foreground mb-2">// api_key_config</div>
            <label className="block text-xs font-semibold text-foreground mb-1.5">
              API Key
              <span className="ml-1.5 text-[10px] font-normal text-muted-foreground">（留空使用内置 Key）</span>
            </label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                value={localKey}
                onChange={(e) => setLocalKey(e.target.value)}
                onBlur={() => onApiKeyChange(localKey)}
                placeholder={isDomestic ? `填写 ${vendorLabel.replace(/🇨🇳\s*/, "")} API Key...` : "sk-... 或留空使用内置 Key"}
                className="w-full h-9 pl-3 pr-9 rounded-lg border border-border/60 bg-background text-sm font-mono text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-primary/50"
                autoComplete="off"
                spellCheck={false}
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={-1}
              >
                {showKey ? (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                ) : (
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                )}
              </button>
            </div>
            {localKey && localKey !== apiKey && (
              <button
                onClick={() => { onApiKeyChange(localKey); setOpen(false); }}
                className="mt-2 w-full h-8 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 transition-all duration-150 active:scale-[0.97]"
              >
                应用 Key
              </button>
            )}
            {apiKey && (
              <button
                onClick={() => { setLocalKey(""); onApiKeyChange(""); }}
                className="mt-1.5 w-full h-7 border border-border/60 text-muted-foreground text-xs rounded-lg hover:bg-muted transition-all duration-150"
              >
                清除 Key（恢复内置）
              </button>
            )}
          </div>

          {/* Status footer */}
          <div className="border-t border-border/40 pt-3">
            <div className="text-[10px] text-muted-foreground mono-label leading-relaxed">
              {apiKey
                ? `// using: custom_key → ${isDomestic ? getEndpointHint(displayModel) : "forge_api"} ✓`
                : "// using: built_in_forge_key (default)"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getEndpointHint(model: string): string {
  const hints: Record<string, string> = {
    deepseek: "api.deepseek.com",
    qwen: "dashscope.aliyuncs.com",
    moonshot: "api.moonshot.cn",
    glm: "open.bigmodel.cn",
    doubao: "ark.cn-beijing.volces.com",
    hunyuan: "api.hunyuan.cloud.tencent.com",
    "yi-": "api.lingyiwanwu.com",
    ernie: "qianfan.baidubce.com",
  };
  for (const [prefix, hint] of Object.entries(hints)) {
    if (model.toLowerCase().startsWith(prefix)) return hint;
  }
  return "forge.manus.im";
}
