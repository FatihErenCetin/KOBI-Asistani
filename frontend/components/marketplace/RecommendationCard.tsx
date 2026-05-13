"use client";

import { Sparkles, Trash2, Truck } from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";
import { formatTRY } from "@/lib/format";

interface Recommendation {
  id: number;
  product_id: number | null;
  product_name: string;
  suggested_supplier_id: number | null;
  suggested_supplier_name: string | null;
  suggested_quantity: number;
  estimated_unit_cost: number | null;
  confidence: number;
  reasoning: string;
  nearby_signal_count: number;
  status: string;
}

export function RecommendationCard({
  rec,
  onChange,
  onApply,
}: {
  rec: Recommendation;
  onChange: () => void;
  onApply: (rec: Recommendation) => void;
}) {
  const [busy, setBusy] = useState(false);

  async function dismiss() {
    if (!confirm("Bu öneri kapatılsın mı?")) return;
    setBusy(true);
    try {
      await api.dismissRecommendation(rec.id);
      onChange();
    } finally {
      setBusy(false);
    }
  }

  const conf = Math.round(rec.confidence * 100);
  const confTone =
    conf >= 75
      ? "bg-emerald-50 text-emerald-700"
      : conf >= 50
        ? "bg-amber-50 text-amber-700"
        : "bg-slate-100 text-slate-700";

  return (
    <article className="rounded-xl border border-amber-200 bg-amber-50/40 p-4 space-y-3">
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-xs text-amber-700">
            <Sparkles className="h-3 w-3" />
            AI Önerisi
          </div>
          <h3 className="mt-1 text-base font-semibold text-slate-900">
            {rec.product_name}
          </h3>
        </div>
        <span
          className={`shrink-0 rounded px-2 py-0.5 text-[11px] font-semibold ${confTone}`}
        >
          %{conf} güven
        </span>
      </header>

      <p className="text-sm leading-relaxed text-slate-700">{rec.reasoning}</p>

      <div className="grid grid-cols-3 gap-2 rounded-lg bg-white p-2.5 text-xs">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Önerilen
          </p>
          <p className="mt-0.5 font-semibold tabular-nums">
            {rec.suggested_quantity.toFixed(0)} br
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Tahmini birim
          </p>
          <p className="mt-0.5 font-semibold tabular-nums">
            {rec.estimated_unit_cost
              ? formatTRY(rec.estimated_unit_cost)
              : "—"}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Komşu sinyali
          </p>
          <p className="mt-0.5 font-semibold tabular-nums">
            {rec.nearby_signal_count} KOBİ
          </p>
        </div>
      </div>

      {rec.suggested_supplier_name && (
        <p className="inline-flex items-center gap-1.5 text-xs text-slate-600">
          <Truck className="h-3 w-3" />
          Önerilen tedarikçi:{" "}
          <span className="font-medium">{rec.suggested_supplier_name}</span>
        </p>
      )}

      <div className="flex items-center gap-2 pt-1 border-t border-amber-200/60">
        <button
          onClick={() => onApply(rec)}
          disabled={busy || !rec.suggested_supplier_id}
          className="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-600 disabled:opacity-50"
        >
          Sipariş Geç
        </button>
        <button
          onClick={dismiss}
          disabled={busy}
          className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-50"
          title="Öneriyi kapat"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    </article>
  );
}
