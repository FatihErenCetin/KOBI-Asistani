"use client";

import { AlertOctagon, Check, MessageSquareWarning } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

interface Complaint {
  id: number;
  customer_id: number | null;
  telegram_user_id: number | null;
  message_text: string;
  risk_score: number;
  signals: string[];
  resolved: boolean;
  created_at: string;
}

export default function ComplaintsPage() {
  const [rows, setRows] = useState<Complaint[]>([]);

  async function reload() {
    setRows(await api.listComplaints());
  }

  useEffect(() => {
    reload();
  }, []);

  async function resolve(id: number) {
    if (!confirm("Bu şikayet çözüldü olarak işaretlensin mi?")) return;
    await api.resolveComplaint(id);
    reload();
  }

  return (
    <div className="max-w-5xl space-y-5">
      <header>
        <h1 className="text-2xl font-bold inline-flex items-center gap-2">
          <MessageSquareWarning className="h-6 w-6 text-rose-500" />
          Şikayet Riski Tespitleri
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Telegram konuşmalarında otomatik algılanan şikayet sinyalleri.
          Resmi şikayet olduğu anlamına gelmez — incelemek için açın.
        </p>
      </header>

      {rows.length === 0 ? (
        <p className="text-emerald-600 bg-emerald-50 border border-emerald-200 rounded p-4">
          ✓ Açık şikayet bildirimi yok.
        </p>
      ) : (
        <ul className="space-y-3">
          {rows.map((c) => (
            <li
              key={c.id}
              className={`bg-white border rounded-lg p-4 ${
                c.risk_score >= 0.85
                  ? "border-rose-300"
                  : "border-amber-300"
              }`}
            >
              <header className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AlertOctagon
                    className={`h-4 w-4 ${
                      c.risk_score >= 0.85
                        ? "text-rose-600"
                        : "text-amber-600"
                    }`}
                  />
                  <span className="font-medium">
                    Risk skoru: %{Math.round(c.risk_score * 100)}
                  </span>
                  <span className="text-xs text-slate-500">
                    · {formatDateTime(c.created_at)}
                  </span>
                </div>
                <button
                  onClick={() => resolve(c.id)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded border border-slate-300 hover:bg-slate-50"
                >
                  <Check className="h-3 w-3" /> Çözüldü
                </button>
              </header>
              <p className="text-sm text-slate-700 italic border-l-2 border-slate-300 pl-3 my-2">
                "{c.message_text}"
              </p>
              {c.signals.length > 0 && (
                <p className="text-xs text-slate-500">
                  Sinyaller:{" "}
                  {c.signals.map((s) => (
                    <span
                      key={s}
                      className="inline-block bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded ml-1"
                    >
                      {s}
                    </span>
                  ))}
                </p>
              )}
              <p className="text-xs text-slate-400 mt-1">
                Müşteri:{" "}
                {c.customer_id
                  ? `#${c.customer_id}`
                  : `TG ${c.telegram_user_id ?? "?"}`}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
