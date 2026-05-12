"use client";
import { useState } from "react";

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

export function ChatPanel() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!input.trim() || busy) return;
    const userTurn: Turn = { role: "user", text: input };
    setTurns((t) => [...t, userTurn]);
    setInput("");
    setBusy(true);
    try {
      const resp = await api.panelChat(userTurn.text);
      setTurns((t) => [...t, { role: "assistant", text: resp.text, data: resp.data }]);
    } catch (e: any) {
      setTurns((t) => [...t, { role: "assistant", text: `Hata: ${e.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {turns.length === 0 && (
          <div className="text-slate-500 text-sm">
            Örnek: <em>&ldquo;Bu hafta Ayşe Yılmaz&apos;dan kaç sipariş geldi?&rdquo;</em>
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "text-right" : ""}>
            <div
              className={`inline-block max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                t.role === "user"
                  ? "bg-slate-900 text-white"
                  : "bg-white border border-slate-200"
              }`}
            >
              {t.text}
            </div>
            {t.role === "assistant" && t.data && (
              <div className="mt-2 max-w-[80%]">
                <RenderData data={t.data} />
              </div>
            )}
          </div>
        ))}
        {busy && <p className="text-sm text-slate-400">Düşünüyorum...</p>}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Doğal dilde sor..."
          className="flex-1 border border-slate-300 rounded px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={busy}
          className="px-4 py-2 bg-brand-600 text-white rounded text-sm disabled:opacity-50"
        >
          Gönder
        </button>
      </form>
    </div>
  );
}
