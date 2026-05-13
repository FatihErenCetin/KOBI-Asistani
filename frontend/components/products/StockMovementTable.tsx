"use client";

import { formatDateTime } from "@/lib/format";

const LABELS: Record<string, string> = {
  purchase: "Alım",
  sale: "Satış",
  adjustment: "Düzeltme",
  return: "İade",
  waste: "Fire",
  initial: "Açılış",
};

const COLORS: Record<string, string> = {
  purchase: "bg-emerald-100 text-emerald-700",
  sale: "bg-blue-100 text-blue-700",
  adjustment: "bg-amber-100 text-amber-700",
  return: "bg-sky-100 text-sky-700",
  waste: "bg-rose-100 text-rose-700",
  initial: "bg-slate-100 text-slate-700",
};

interface Row {
  id: number;
  delta: number;
  reason: string;
  note: string | null;
  balance_after: number;
  created_at: string;
}

export function StockMovementTable({ rows }: { rows: Row[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">Stok hareketi yok.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="text-xs text-slate-500">
        <tr>
          <th className="text-left py-1">Sebep</th>
          <th className="text-right py-1">Miktar</th>
          <th className="text-right py-1">Bakiye</th>
          <th className="text-left py-1 px-3">Not</th>
          <th className="text-left py-1">Tarih</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className="border-t border-slate-100">
            <td className="py-1.5">
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  COLORS[r.reason] ?? ""
                }`}
              >
                {LABELS[r.reason] ?? r.reason}
              </span>
            </td>
            <td
              className={`py-1.5 text-right font-medium ${
                r.delta >= 0 ? "text-emerald-700" : "text-rose-700"
              }`}
            >
              {r.delta >= 0 ? "+" : ""}
              {r.delta}
            </td>
            <td className="py-1.5 text-right text-slate-700">
              {r.balance_after}
            </td>
            <td className="py-1.5 px-3 text-slate-600">{r.note ?? "—"}</td>
            <td className="py-1.5 text-slate-500 text-xs">
              {formatDateTime(r.created_at)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
