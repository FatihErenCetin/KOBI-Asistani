"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ComponentType, FormEvent, KeyboardEvent } from "react";
import {
  BarChart3,
  Bot,
  Clock3,
  MessageSquarePlus,
  MessagesSquare,
  PackageSearch,
  Truck,
  PanelLeftClose,
  PanelLeftOpen,
  Send,
  Sparkles,
  Trash2,
  Users,
  Zap,
} from "lucide-react";

import { api } from "@/lib/api";
import { CarrierAnalysisRender } from "./CarrierAnalysisRender";
import { ActionSuggestionRender } from "./ActionSuggestionRender";
import { OperationSummaryRender } from "./OperationSummaryRender";
import { OrderListRender } from "./OrderListRender";
import { SalesChart } from "./SalesChart";
import { StockOverviewRender } from "./StockOverviewRender";

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

type Suggestion = {
  label: string;
  prompt: string;
  icon: ComponentType<{ className?: string }>;
  tone: string;
};

const STORAGE_KEY = "kobi-chat-conversations";

const SUGGESTIONS: Suggestion[] = [
  {
    label: "Bu hafta satış grafiği",
    prompt: "Bu hafta günlük satış grafiğini göster",
    icon: BarChart3,
    tone: "bg-brand-50 text-brand-700 border-brand-100",
  },
  {
    label: "Düşük stokları listele",
    prompt: "Düşük stokta olan ürünleri listele",
    icon: PackageSearch,
    tone: "bg-amber-50 text-amber-700 border-amber-100",
  },
  {
    label: "Ayşe Yılmaz siparişleri",
    prompt: "Ayşe Yılmaz'ın son siparişlerini göster",
    icon: Users,
    tone: "bg-indigo-50 text-indigo-700 border-indigo-100",
  },
  {
    label: "Acil bekleyenler",
    prompt: "Bekleyen acil siparişleri listele",
    icon: Zap,
    tone: "bg-rose-50 text-rose-700 border-rose-100",
  },
  {
    label: "Kargo riskleri",
    prompt: "Kargo gecikme riski olan siparişleri göster",
    icon: Truck,
    tone: "bg-sky-50 text-sky-700 border-sky-100",
  },
  {
    label: "Sipariş #128",
    prompt: "128 numaralı sipariş nerede?",
    icon: Bot,
    tone: "bg-violet-50 text-violet-700 border-violet-100",
  },
];

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
}

function makeTitle(text: string): string {
  const clean = text.trim().replace(/\s+/g, " ");
  return clean.length > 42 ? `${clean.slice(0, 42)}…` : clean || "Yeni sohbet";
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "az önce";
  if (min < 60) return `${min} dk önce`;
  const hour = Math.floor(min / 60);
  if (hour < 24) return `${hour} saat önce`;
  const day = Math.floor(hour / 24);
  if (day === 1) return "dün";
  if (day < 7) return `${day} gün önce`;
  return new Date(iso).toLocaleDateString("tr-TR");
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
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, 25)));
  } catch {
    return;
  }
}

function RenderData({ data }: { data: any }) {
  if (!data) return null;
  if (data.type === "order_list") return <OrderListRender data={data} />;
  if (data.type === "sales_summary") return <SalesChart data={data} />;
  if (data.type === "stock_overview") return <StockOverviewRender data={data} />;
  if (data.type === "carrier_analysis" || data.type === "carrier_risks") return <CarrierAnalysisRender data={data} />;
  if (data.type === "operation_summary") return <OperationSummaryRender data={data} />;
  if (data.type === "action_suggestion") return <ActionSuggestionRender data={data} />;
  return null;
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5" aria-label="Asistan yazıyor">
      <span className="h-2 w-2 rounded-full bg-slate-400 motion-safe:animate-bounce [animation-delay:-0.25s]" />
      <span className="h-2 w-2 rounded-full bg-slate-400 motion-safe:animate-bounce [animation-delay:-0.12s]" />
      <span className="h-2 w-2 rounded-full bg-slate-400 motion-safe:animate-bounce" />
    </div>
  );
}

function AssistantAvatar() {
  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-brand-50 text-brand-700 ring-1 ring-brand-100" aria-hidden="true">
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
    () => [...conversations].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()),
    [conversations]
  );

  return (
    <div className="flex h-full flex-col">
      <div className="p-4">
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <MessageSquarePlus className="h-4 w-4" aria-hidden="true" />
          Yeni sohbet
        </button>
      </div>

      <div className="flex items-center justify-between px-5 pb-2">
        <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">Geçmiş</span>
        <span className="text-xs font-bold text-slate-400">{sorted.length}</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-4" aria-label="Sohbet geçmişi">
        {sorted.length === 0 ? (
          <div className="mt-8 rounded-3xl border border-dashed border-slate-200 bg-white/70 p-5 text-center">
            <MessagesSquare className="mx-auto h-6 w-6 text-slate-300" aria-hidden="true" />
            <p className="mt-3 text-xs font-medium leading-5 text-slate-500">İlk mesajdan sonra sohbetler burada tutulur.</p>
          </div>
        ) : (
          <ul className="space-y-1">
            {sorted.map((conversation) => {
              const active = conversation.id === activeId;
              return (
                <li key={conversation.id}>
                  <div className={`group flex items-center rounded-2xl transition ${active ? "bg-brand-50 ring-1 ring-brand-100" : "hover:bg-white"}`}>
                    <button
                      type="button"
                      onClick={() => onSelect(conversation.id)}
                      className="min-w-0 flex-1 px-3 py-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                    >
                      <span className={`block truncate text-sm font-bold ${active ? "text-brand-800" : "text-slate-800"}`}>{conversation.title}</span>
                      <span className="mt-1 flex items-center gap-1 text-xs font-medium text-slate-400">
                        <Clock3 className="h-3 w-3" aria-hidden="true" />
                        {relativeTime(conversation.updated_at)}
                      </span>
                    </button>
                    <button
                      type="button"
                      aria-label="Sohbeti sil"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDelete(conversation.id);
                      }}
                      className="mr-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-slate-300 opacity-0 transition hover:bg-rose-50 hover:text-rose-600 group-hover:opacity-100 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
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

function SuggestionGrid({ onPick, disabled }: { onPick: (prompt: string) => void; disabled: boolean }) {
  return (
    <div className="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
      {SUGGESTIONS.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.label}
            type="button"
            onClick={() => onPick(item.prompt)}
            disabled={disabled}
            className="group rounded-3xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-soft disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className={`inline-flex h-10 w-10 items-center justify-center rounded-2xl border ${item.tone}`}>
              <Icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="mt-3 block text-sm font-extrabold text-slate-950 group-hover:text-brand-700">{item.label}</span>
            <span className="mt-1 block text-xs font-medium leading-5 text-slate-500">Veriye bakarak kısa sonuç üretir.</span>
          </button>
        );
      })}
    </div>
  );
}

export function ChatPanel() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const loaded = loadConversations();
    setConversations(loaded);
    setActiveId(loaded[0]?.id ?? null);
  }, []);

  useEffect(() => {
    saveConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [conversations, activeId, busy]);

  const activeConversation = conversations.find((c) => c.id === activeId) ?? null;
  const turns = activeConversation?.turns ?? [];
  const isEmpty = turns.length === 0;

  function startNew() {
    setActiveId(null);
    setInput("");
    setMobileHistoryOpen(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function selectConversation(id: string) {
    setActiveId(id);
    setMobileHistoryOpen(false);
  }

  function deleteConversation(id: string) {
    setConversations((prev) => prev.filter((item) => item.id !== id));
    if (activeId === id) setActiveId(null);
  }

  function addUserMessage(userText: string): string {
    const now = new Date().toISOString();
    const userTurn: Turn = { role: "user", text: userText };
    const targetId = activeId ?? newId();

    if (!activeId) setActiveId(targetId);

    setConversations((prev) => {
      const existing = prev.find((conversation) => conversation.id === targetId);
      if (!existing) {
        return [
          {
            id: targetId,
            title: makeTitle(userText),
            turns: [userTurn],
            created_at: now,
            updated_at: now,
          },
          ...prev,
        ];
      }

      return prev.map((conversation) => {
        if (conversation.id !== targetId) return conversation;
        return {
          ...conversation,
          title: conversation.turns.length === 0 ? makeTitle(userText) : conversation.title,
          turns: [...conversation.turns, userTurn],
          updated_at: now,
        };
      });
    });

    return targetId;
  }

  function addAssistantMessage(conversationId: string, assistantTurn: Turn) {
    const now = new Date().toISOString();
    setConversations((prev) =>
      prev.map((conversation) => {
        if (conversation.id !== conversationId) return conversation;
        return {
          ...conversation,
          turns: [...conversation.turns, assistantTurn],
          updated_at: now,
        };
      }),
    );
  }

  async function send(forcedPrompt?: string) {
    const text = (forcedPrompt ?? input).trim();
    if (!text || busy) return;

    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    setBusy(true);

    const conversationId = addUserMessage(text);
    const history = turns.map((turn) => ({ role: turn.role, text: turn.text }));

    try {
      const response = await api.panelChat(text, history);
      addAssistantMessage(conversationId, {
        role: "assistant",
        text: response.text,
        data: response.data,
      });
    } catch (error) {
      addAssistantMessage(conversationId, {
        role: "assistant",
        text: "Bağlantı sırasında hata oluştu. Backend veya API anahtarını kontrol edin.",
      });
    } finally {
      setBusy(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    send();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  function autoResize(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = `${Math.min(160, el.scrollHeight)}px`;
  }

  return (
    <div className="relative flex h-full overflow-hidden bg-slate-50/70">
      <aside className="hidden w-80 shrink-0 border-r border-slate-200/80 bg-slate-50/95 lg:block">
        <HistoryList conversations={conversations} activeId={activeId} onSelect={selectConversation} onNew={startNew} onDelete={deleteConversation} />
      </aside>

      {mobileHistoryOpen && (
        <div className="absolute inset-0 z-40 lg:hidden">
          <button type="button" className="absolute inset-0 bg-slate-950/35" onClick={() => setMobileHistoryOpen(false)} aria-label="Kapat" />
          <aside className="absolute left-0 top-0 h-full w-[300px] max-w-[86vw] border-r border-slate-200 bg-slate-50 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <span className="text-sm font-extrabold text-slate-900">Sohbet geçmişi</span>
              <button type="button" onClick={() => setMobileHistoryOpen(false)} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100" aria-label="Kapat">
                <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
            <HistoryList conversations={conversations} activeId={activeId} onSelect={selectConversation} onNew={startNew} onDelete={deleteConversation} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 py-3 backdrop-blur lg:px-6">
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => setMobileHistoryOpen(true)} className="rounded-xl p-2 text-slate-600 hover:bg-slate-100 lg:hidden" aria-label="Geçmişi aç">
              <PanelLeftOpen className="h-4 w-4" aria-hidden="true" />
            </button>
            <div>
              <p className="text-sm font-extrabold text-slate-950">AI Operasyon Asistanı</p>
              <p className="text-xs font-medium text-slate-500">Sipariş, stok, müşteri ve satış verisiyle konuşur</p>
            </div>
          </div>
          <span className="hidden rounded-full bg-brand-50 px-3 py-1.5 text-xs font-bold text-brand-700 sm:inline-flex">Veriye bağlı yanıt</span>
        </div>

        <div ref={scrollRef} aria-busy={busy} className="flex-1 overflow-y-auto">
          <div className="mx-auto flex min-h-full max-w-4xl flex-col px-4 py-8 sm:px-6">
            {isEmpty ? (
              <div className="flex flex-1 flex-col items-center justify-center text-center">
                <div className="relative">
                  <div className="absolute inset-0 rounded-[2rem] bg-brand-400/20 blur-2xl" />
                  <span className="relative flex h-16 w-16 items-center justify-center rounded-[2rem] bg-slate-950 text-white shadow-glow">
                    <Bot className="h-7 w-7" aria-hidden="true" />
                  </span>
                </div>
                <h2 className="mt-6 text-2xl font-extrabold tracking-tight text-slate-950">Operasyon verinize doğal dilde sorun.</h2>
                <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">
                  Müşteri siparişlerini, düşük stokları, kargo risklerini ve aksiyon önerilerini panel gezmeden sorgulayabilirsiniz.
                </p>
                <div className="mt-8 w-full">
                  <SuggestionGrid onPick={send} disabled={busy} />
                </div>
              </div>
            ) : (
              <ol className="space-y-6">
                {turns.map((turn, index) => {
                  if (turn.role === "user") {
                    return (
                      <li key={index} className="flex justify-end">
                        <div className="max-w-[82%] rounded-3xl rounded-tr-lg bg-slate-950 px-5 py-3 text-[15px] font-medium leading-7 text-white shadow-soft">
                          <p className="whitespace-pre-wrap">{turn.text}</p>
                        </div>
                      </li>
                    );
                  }

                  return (
                    <li key={index} className="flex items-start gap-3">
                      <AssistantAvatar />
                      <div className="min-w-0 max-w-[88%] flex-1">
                        <div className={`rounded-3xl rounded-tl-lg border border-slate-200 bg-white px-5 py-4 text-[15px] font-medium leading-7 text-slate-800 shadow-sm ${turn.data ? "rounded-b-none border-b-0" : ""}`}>
                          <p className="whitespace-pre-wrap">{turn.text}</p>
                        </div>
                        {turn.data && (
                          <div className="overflow-hidden rounded-b-3xl border border-t-0 border-slate-200 bg-white p-3 shadow-sm">
                            <RenderData data={turn.data} />
                          </div>
                        )}
                      </div>
                    </li>
                  );
                })}
                {busy && (
                  <li className="flex items-start gap-3" aria-live="polite">
                    <AssistantAvatar />
                    <div className="rounded-3xl rounded-tl-lg border border-slate-200 bg-white px-5 py-4 shadow-sm">
                      <TypingIndicator />
                    </div>
                  </li>
                )}
              </ol>
            )}
          </div>
        </div>

        <div className="border-t border-slate-200/80 bg-white/90 px-4 pb-4 pt-3 backdrop-blur sm:px-6">
          {!isEmpty && (
            <div className="mx-auto mb-3 flex max-w-4xl gap-2 overflow-x-auto pb-1">
              {SUGGESTIONS.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => send(item.prompt)}
                  disabled={busy}
                  className="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700 disabled:opacity-60"
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mx-auto max-w-4xl">
            <div className="flex items-end gap-2 rounded-[1.6rem] border border-slate-200 bg-white p-2 shadow-soft transition focus-within:border-brand-400 focus-within:ring-4 focus-within:ring-brand-500/10">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
                <Bot className="h-5 w-5" aria-hidden="true" />
              </div>
              <textarea
                ref={inputRef}
                value={input}
                rows={1}
                onChange={(event) => {
                  setInput(event.target.value);
                  autoResize(event.currentTarget);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Örnek: 128 numaralı sipariş nerede?"
                className="max-h-40 min-h-11 flex-1 resize-none border-0 bg-transparent px-1 py-3 text-[15px] font-medium leading-6 text-slate-950 placeholder:text-slate-400 focus:outline-none"
                aria-label="Mesajınızı yazın"
              />
              <button
                type="submit"
                disabled={busy || !input.trim()}
                className="flex h-11 shrink-0 items-center gap-2 rounded-2xl bg-brand-600 px-4 text-sm font-extrabold text-white shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
                Gönder
              </button>
            </div>
            <p className="mt-2 text-center text-[11px] font-medium text-slate-400">Yanıtlar sipariş, stok ve kargo verisine bağlıdır. Taslak aksiyonları göndermeden önce kontrol edin.</p>
          </form>
        </div>
      </div>
    </div>
  );
}
