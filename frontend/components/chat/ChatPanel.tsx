"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Send,
  Sparkles,
  BarChart3,
  PackageSearch,
  Users,
  Zap,
  Bot,
  MessageSquarePlus,
  Trash2,
  MessagesSquare,
  Clock,
  PanelLeftOpen,
  PanelLeftClose,
} from "lucide-react";

import {
  CategoryStockRender,
  FastDepletingRender,
  FinancialOverviewRender,
  LowMarginRender,
  ProductAnalyticsCard,
  SupplierPerformanceRender,
} from "./AnalyticsRenders";
import { OrderListRender } from "./OrderListRender";
import { SalesChart } from "./SalesChart";
import { StockOverviewRender } from "./StockOverviewRender";
import { api } from "@/lib/api";

/* -------------------------------------------------------------------------- */
/*  Types & constants                                                         */
/* -------------------------------------------------------------------------- */

interface Turn {
  role: "user" | "assistant";
  text: string;
  data?: any;
}

interface Conversation {
  id: string;
  title: string;
  turns: Turn[];
  created_at: string;
  updated_at: string;
}

const STORAGE_KEY = "kobi-chat-conversations";

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

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                   */
/* -------------------------------------------------------------------------- */

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "az önce";
  if (min < 60) return `${min} dk önce`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} saat önce`;
  const day = Math.floor(hr / 24);
  if (day === 1) return "dün";
  if (day < 7) return `${day} gün önce`;
  return new Date(iso).toLocaleDateString("tr-TR");
}

function makeTitle(text: string): string {
  const clean = text.trim().replace(/\s+/g, " ");
  return clean.length > 40 ? clean.slice(0, 40) + "…" : clean || "Yeni sohbet";
}

function loadConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveConversations(list: Conversation[]) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {
    /* quota / private mode — silent */
  }
}

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

/* -------------------------------------------------------------------------- */
/*  Render data widget                                                        */
/* -------------------------------------------------------------------------- */

function RenderData({ data }: { data: any }) {
  if (!data) return null;
  if (data.type === "order_list") return <OrderListRender data={data} />;
  if (data.type === "sales_summary") return <SalesChart data={data} />;
  if (data.type === "stock_overview") return <StockOverviewRender data={data} />;
  if (data.type === "low_margin") return <LowMarginRender data={data} />;
  if (data.type === "fast_depleting") return <FastDepletingRender data={data} />;
  if (data.type === "supplier_performance")
    return <SupplierPerformanceRender data={data} />;
  if (data.type === "product_analytics")
    return <ProductAnalyticsCard data={data} />;
  if (data.type === "category_stock") return <CategoryStockRender data={data} />;
  if (data.type === "financial_overview")
    return <FinancialOverviewRender data={data} />;
  return null;
}

/* -------------------------------------------------------------------------- */
/*  Small inline components                                                   */
/* -------------------------------------------------------------------------- */

function TypingIndicator() {
  return (
    <div
      className="flex items-center gap-1.5 px-1 py-1"
      aria-label="Asistan yazıyor"
    >
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

function HistoryList({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  const sorted = useMemo(
    () =>
      [...conversations].sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      ),
    [conversations]
  );

  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <button
          type="button"
          onClick={onNew}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 shadow-sm transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          <MessageSquarePlus className="h-4 w-4" aria-hidden="true" />
          <span>Yeni Sohbet</span>
        </button>
      </div>

      <div className="flex items-center justify-between px-4 pb-2">
        <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
          Geçmiş
        </span>
        {sorted.length > 0 && (
          <span className="text-[11px] text-slate-400 tabular-nums">
            {sorted.length}
          </span>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-3" aria-label="Sohbet geçmişi">
        {sorted.length === 0 ? (
          <div className="mt-6 flex flex-col items-center px-3 text-center">
            <span
              aria-hidden="true"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-white ring-1 ring-slate-200"
            >
              <MessagesSquare className="h-5 w-5 text-slate-400" />
            </span>
            <p className="mt-3 text-xs text-slate-500">
              Henüz sohbet yok. İlk soruyu sorduğunuzda burada görünür.
            </p>
          </div>
        ) : (
          <ul className="space-y-0.5">
            {sorted.map((c) => {
              const active = c.id === activeId;
              return (
                <li key={c.id}>
                  <div
                    className={`group relative flex items-center rounded-lg transition ${
                      active
                        ? "bg-brand-50 ring-1 ring-inset ring-brand-100"
                        : "hover:bg-slate-100"
                    }`}
                  >
                    {active && (
                      <span
                        aria-hidden="true"
                        className="absolute left-0 bottom-1.5 top-1.5 w-0.5 rounded-full bg-brand-500"
                      />
                    )}
                    <button
                      type="button"
                      onClick={() => onSelect(c.id)}
                      aria-current={active ? "true" : undefined}
                      className="flex min-w-0 flex-1 flex-col items-start gap-0.5 rounded-lg px-3 py-2 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                    >
                      <span
                        className={`w-full truncate text-sm font-medium ${
                          active ? "text-brand-800" : "text-slate-800"
                        }`}
                      >
                        {c.title}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Clock className="h-3 w-3" aria-hidden="true" />
                        {relativeTime(c.updated_at)}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (
                          window.confirm(
                            `"${c.title}" sohbetini silmek istediğinize emin misiniz?`
                          )
                        ) {
                          onDelete(c.id);
                        }
                      }}
                      aria-label="Sohbeti sil"
                      className="mr-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-slate-400 opacity-0 transition hover:bg-rose-50 hover:text-rose-600 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </nav>
    </div>
  );
}

function CompactChipStrip({
  onPick,
  disabled,
}: {
  onPick: (prompt: string) => void;
  disabled?: boolean;
}) {
  return (
    <nav
      aria-label="Hızlı öneriler"
      className="-mx-1 overflow-x-auto px-1 pb-2"
    >
      <ul className="flex items-center gap-2 whitespace-nowrap">
        {SUGGESTIONS.map((s) => {
          const Icon = s.icon;
          return (
            <li key={s.label}>
              <button
                type="button"
                onClick={() => onPick(s.prompt)}
                disabled={disabled}
                className={`inline-flex items-center gap-1.5 rounded-full border ${s.borderClass} bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-60`}
              >
                <Icon
                  className={`h-3.5 w-3.5 ${s.iconClass}`}
                  aria-hidden="true"
                />
                <span>{s.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/* -------------------------------------------------------------------------- */
/*  ChatPanel                                                                 */
/* -------------------------------------------------------------------------- */

export function ChatPanel() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  /* Load from localStorage on mount */
  useEffect(() => {
    const list = loadConversations();
    setConversations(list);
    setHydrated(true);
  }, []);

  /* Persist whenever conversations change (after hydration) */
  useEffect(() => {
    if (!hydrated) return;
    saveConversations(conversations);
  }, [conversations, hydrated]);

  /* Auto-scroll on new turns */
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns, busy]);

  /* Close mobile drawer on Escape */
  useEffect(() => {
    if (!mobileHistoryOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileHistoryOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobileHistoryOpen]);

  function startNew() {
    setActiveId(null);
    setTurns([]);
    setInput("");
    setMobileHistoryOpen(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function selectConversation(id: string) {
    const conv = conversations.find((c) => c.id === id);
    if (!conv) return;
    setActiveId(id);
    setTurns(conv.turns);
    setInput("");
    setMobileHistoryOpen(false);
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  function deleteConversation(id: string) {
    setConversations((list) => list.filter((c) => c.id !== id));
    if (activeId === id) {
      setActiveId(null);
      setTurns([]);
    }
  }

  async function send(messageOverride?: string) {
    const text = (messageOverride ?? input).trim();
    if (!text || busy) return;

    const userTurn: Turn = { role: "user", text };
    const newTurns = [...turns, userTurn];
    setTurns(newTurns);
    setInput("");
    setBusy(true);

    const now = new Date().toISOString();
    let convId = activeId;
    if (!convId) {
      convId = newId();
      const conv: Conversation = {
        id: convId,
        title: makeTitle(text),
        turns: newTurns,
        created_at: now,
        updated_at: now,
      };
      setConversations((list) => [conv, ...list]);
      setActiveId(convId);
    } else {
      const id = convId;
      setConversations((list) =>
        list.map((c) =>
          c.id === id ? { ...c, turns: newTurns, updated_at: now } : c
        )
      );
    }

    try {
      const resp = await api.panelChat(text);
      const finalTurns: Turn[] = [
        ...newTurns,
        { role: "assistant", text: resp.text, data: resp.data },
      ];
      setTurns(finalTurns);
      const id = convId;
      setConversations((list) =>
        list.map((c) =>
          c.id === id
            ? { ...c, turns: finalTurns, updated_at: new Date().toISOString() }
            : c
        )
      );
    } catch (e: any) {
      const errTurns: Turn[] = [
        ...newTurns,
        { role: "assistant", text: `Hata: ${e?.message ?? "bilinmiyor"}` },
      ];
      setTurns(errTurns);
      const id = convId;
      setConversations((list) =>
        list.map((c) =>
          c.id === id
            ? { ...c, turns: errTurns, updated_at: new Date().toISOString() }
            : c
        )
      );
    } finally {
      setBusy(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function autoResize(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  const isEmpty = turns.length === 0;

  return (
    // Negative-margin trick so the panel can break out of the page-level
    // max-w-4xl wrapper and let the history sidebar claim its own column.
    <div className="relative -mx-4 sm:-mx-6 lg:-mx-8">
      <div className="flex h-[calc(100vh-9rem)] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {/* Desktop history sidebar */}
        <aside
          aria-label="Sohbet geçmişi"
          className="hidden w-[260px] shrink-0 border-r border-slate-200 bg-slate-50 lg:block"
        >
          <HistoryList
            conversations={conversations}
            activeId={activeId}
            onSelect={selectConversation}
            onNew={startNew}
            onDelete={deleteConversation}
          />
        </aside>

        {/* Mobile/tablet drawer */}
        {mobileHistoryOpen && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div
              className="absolute inset-0 bg-slate-900/30"
              onClick={() => setMobileHistoryOpen(false)}
              aria-hidden="true"
            />
            <aside
              role="dialog"
              aria-modal="true"
              aria-label="Sohbet geçmişi"
              className="absolute left-0 top-0 h-full w-[280px] max-w-[85vw] border-r border-slate-200 bg-slate-50 shadow-xl"
            >
              <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
                <span className="text-sm font-semibold text-slate-800">
                  Sohbet Geçmişi
                </span>
                <button
                  type="button"
                  onClick={() => setMobileHistoryOpen(false)}
                  aria-label="Kapat"
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 hover:bg-slate-200 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                >
                  <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>
              <HistoryList
                conversations={conversations}
                activeId={activeId}
                onSelect={selectConversation}
                onNew={startNew}
                onDelete={deleteConversation}
              />
            </aside>
          </div>
        )}

        {/* Chat column */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Mobile/tablet toolbar */}
          <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-3 py-2 lg:hidden">
            <button
              type="button"
              onClick={() => setMobileHistoryOpen(true)}
              aria-label="Sohbet geçmişini aç"
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              <PanelLeftOpen className="h-4 w-4" aria-hidden="true" />
            </button>
            <span className="truncate text-sm font-medium text-slate-700">
              {activeId
                ? conversations.find((c) => c.id === activeId)?.title ??
                  "Sohbet"
                : "Yeni Sohbet"}
            </span>
          </div>

          {/* Messages */}
          <div
            ref={scrollRef}
            aria-busy={busy}
            className="flex-1 overflow-y-auto"
          >
            <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
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
                  <p className="mt-2 max-w-md text-base leading-relaxed text-slate-600">
                    Doğal dilde sorabilirsiniz. Sipariş, müşteri, satış ve stok
                    verilerinizin tamamına erişimim var.
                  </p>

                  <ul className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                    {SUGGESTIONS.map((s) => {
                      const Icon = s.icon;
                      return (
                        <li key={s.label}>
                          <button
                            type="button"
                            onClick={() => send(s.prompt)}
                            disabled={busy}
                            className={`group flex w-full items-center gap-3 rounded-xl border bg-white px-4 py-3 text-left text-sm font-medium text-slate-800 transition hover:bg-slate-50 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${s.borderClass}`}
                          >
                            <span
                              aria-hidden="true"
                              className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${s.bgClass} ${s.iconClass}`}
                            >
                              <Icon className="h-4 w-4" />
                            </span>
                            <span className="flex-1 text-slate-800">
                              {s.label}
                            </span>
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
                    Tek seferlik ipucu: bir öneriye tıklayarak başlayabilirsiniz.
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
                    <li
                      className="flex items-start gap-3"
                      aria-live="polite"
                    >
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
          <div className="border-t border-slate-200 bg-white/90 backdrop-blur">
            <div className="mx-auto max-w-3xl px-4 pb-3 pt-2 sm:px-6">
              {!isEmpty && (
                <CompactChipStrip onPick={(p) => send(p)} disabled={busy} />
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  send();
                }}
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
                    placeholder="Doğal dilde sorun… (Enter ile gönderin, Shift+Enter yeni satır)"
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
                  Yanıtlar verilerinize göre üretilir. Hassas kararlar öncesi
                  doğrulayın.
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}