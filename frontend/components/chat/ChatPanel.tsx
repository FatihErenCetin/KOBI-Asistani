"use client";
import { useEffect, useRef, useState } from "react";
import {
  Send,
  Sparkles,
  BarChart3,
  PackageSearch,
  Users,
  Zap,
  Bot,
} from "lucide-react";

import { OrderListRender } from "./OrderListRender";
import { SalesChart } from "./SalesChart";
import { StockOverviewRender } from "./StockOverviewRender";
import { api } from "@/lib/api";

interface Turn {
  role: "user" | "assistant";
  text: string;
  data?: any;
}

function RenderData({ data }: { data: any }) {
  if (!data) return null;
  if (data.type === "order_list") return <OrderListRender data={data} />;
  if (data.type === "sales_summary") return <SalesChart data={data} />;
  if (data.type === "stock_overview") return <StockOverviewRender data={data} />;
  return null;
}

type Suggestion = {
  label: string;
  prompt: string;
  icon: React.ComponentType<{ className?: string }>;
  iconClass: string;
  bgClass: string;
  borderClass: string;
};

const SUGGESTIONS: Suggestion[] = [
  {
    label: "Bu hafta satış grafiği",
    prompt: "Bu hafta günlük satış grafiğini göster",
    icon: BarChart3,
    iconClass: "text-emerald-600",
    bgClass: "bg-emerald-50",
    borderClass: "border-emerald-100 hover:border-emerald-200",
  },
  {
    label: "Düşük stoklar",
    prompt: "Düşük stokta olan ürünleri listele",
    icon: PackageSearch,
    iconClass: "text-amber-600",
    bgClass: "bg-amber-50",
    borderClass: "border-amber-100 hover:border-amber-200",
  },
  {
    label: "Ayşe Yılmaz'ın son siparişleri",
    prompt: "Ayşe Yılmaz'ın son siparişlerini göster",
    icon: Users,
    iconClass: "text-indigo-600",
    bgClass: "bg-indigo-50",
    borderClass: "border-indigo-100 hover:border-indigo-200",
  },
  {
    label: "Bekleyen acil siparişler",
    prompt: "Bekleyen acil siparişleri listele",
    icon: Zap,
    iconClass: "text-rose-600",
    bgClass: "bg-rose-50",
    borderClass: "border-rose-100 hover:border-rose-200",
  },
];

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-1" aria-label="Asistan yazıyor">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400 motion-safe:animate-bounce [animation-delay:-0.3s]" />
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400 motion-safe:animate-bounce [animation-delay:-0.15s]" />
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400 motion-safe:animate-bounce" />
    </div>
  );
}

function AssistantAvatar() {
  return (
    <span
      aria-hidden="true"
      className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700 ring-1 ring-brand-100"
    >
      <Sparkles className="h-4 w-4" />
    </span>
  );
}

export function ChatPanel() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns, busy]);

  async function sendText(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    const userTurn: Turn = { role: "user", text: trimmed };
    setTurns((t) => [...t, userTurn]);
    setInput("");
    setBusy(true);
    try {
      const resp = await api.panelChat(trimmed);
      setTurns((t) => [...t, { role: "assistant", text: resp.text, data: resp.data }]);
    } catch (e: any) {
      setTurns((t) => [...t, { role: "assistant", text: `Hata: ${e.message}` }]);
    } finally {
      setBusy(false);
      // re-focus composer
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  function send() {
    return sendText(input);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  // Auto-resize textarea (single → up to ~5 lines)
  function autoResize(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  const isEmpty = turns.length === 0;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Mesaj alanı */}
      <div
        ref={scrollRef}
        aria-busy={busy}
        className="flex-1 overflow-y-auto"
      >
        <div className="mx-auto max-w-3xl px-1 py-6">
          {isEmpty ? (
            <div className="flex flex-col items-center text-center">
              <span
                aria-hidden="true"
                className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700 ring-1 ring-brand-100"
              >
                <Sparkles className="h-6 w-6" />
              </span>
              <h2 className="mt-4 text-xl font-semibold text-slate-900">
                Size nasıl yardımcı olabilirim?
              </h2>
              <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-600">
                Doğal dilde sorabilirsiniz. Siparişler, müşteriler, satış ve stok
                verilerinizin tamamına erişimim var.
              </p>

              {/* Suggested chips */}
              <ul className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                {SUGGESTIONS.map((s) => {
                  const Icon = s.icon;
                  return (
                    <li key={s.label}>
                      <button
                        type="button"
                        onClick={() => sendText(s.prompt)}
                        disabled={busy}
                        className={`group flex w-full items-center gap-3 rounded-xl border bg-white px-4 py-3 text-left text-sm font-medium text-slate-800 transition hover:bg-slate-50 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${s.borderClass}`}
                      >
                        <span
                          aria-hidden="true"
                          className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${s.bgClass} ${s.iconClass}`}
                        >
                          <Icon className="h-4 w-4" />
                        </span>
                        <span className="flex-1 text-slate-800">{s.label}</span>
                        <span
                          aria-hidden="true"
                          className="text-xs text-slate-400 transition group-hover:text-slate-600"
                        >
                          ↵
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>

              <p className="mt-6 text-xs text-slate-400">
                Tek seferlik ipucu: chip'e tıklayarak başlayabilirsiniz.
              </p>
            </div>
          ) : (
            <ol className="space-y-5">
              {turns.map((t, i) => {
                if (t.role === "user") {
                  return (
                    <li key={i} className="flex justify-end">
                      <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-slate-900 px-4 py-2.5 text-[15px] leading-relaxed text-white shadow-sm">
                        <p className="whitespace-pre-wrap">{t.text}</p>
                      </div>
                    </li>
                  );
                }
                return (
                  <li key={i} className="flex items-start gap-3">
                    <AssistantAvatar />
                    <div className="min-w-0 max-w-[85%] flex-1">
                      <div
                        className={`rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3 text-[15px] leading-relaxed text-slate-800 shadow-sm ${
                          t.data ? "rounded-b-none border-b-0" : ""
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{t.text}</p>
                      </div>
                      {t.data && (
                        <div className="overflow-hidden rounded-b-2xl border border-t-0 border-slate-200 bg-slate-50/60 p-3 shadow-sm">
                          <RenderData data={t.data} />
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
              {busy && (
                <li className="flex items-start gap-3" aria-live="polite">
                  <AssistantAvatar />
                  <div className="rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
                    <TypingIndicator />
                  </div>
                </li>
              )}
            </ol>
          )}
        </div>
      </div>

      {/* Compose box */}
      <div className="sticky bottom-0 border-t border-slate-200 bg-white/80 backdrop-blur">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="mx-auto max-w-3xl px-1 py-3"
        >
          <div className="group flex items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm transition focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/20">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center text-slate-400">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </div>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                autoResize(e.currentTarget);
              }}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="Doğal dilde sorun… (Enter ile gönder, Shift+Enter yeni satır)"
              aria-label="Mesajınızı yazın"
              className="max-h-40 flex-1 resize-none border-0 bg-transparent px-1 py-2 text-[15px] leading-relaxed text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="inline-flex h-10 shrink-0 items-center gap-1.5 rounded-xl bg-brand-600 px-3.5 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
            >
              <Send className="h-4 w-4" aria-hidden="true" />
              <span>Gönder</span>
            </button>
          </div>
          <p className="mt-2 text-center text-[11px] text-slate-400">
            Yanıtlar verilerinize göre üretilir. Hassas kararlar öncesi doğrulayın.
          </p>
        </form>
      </div>
    </div>
  );
}