"use client";

import { ArrowDown, ArrowUp } from "lucide-react";

import { formatDateTime, formatTRY } from "@/lib/format";

interface Row {
  id: number;
  field: string;
  old_value: number | null;
  new_value: number;
  reason: string | null;
  changed_at: string;
  changed_by_admin_name: string | null;
}

export function PriceHistoryTable({ rows }: { rows: Row[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-slate-500">Fiyat değişiklik kaydı yok.</p>
    );
  }
  return (
    <table className="w-full text-sm">
      <thead className="text-xs text-slate-500">
        <tr>
          <th className="text-left py-1">Alan</th>
          <th className="text-right py-1">Eski</th>
          <th className="text-right py-1">Yeni</th>
          <th className="text-left py-1 px-3">Sebep</th>
          <th className="text-left py-1">Değiştiren</th>
          <th className="text-left py-1">Tarih</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const isUp = r.new_value > (r.old_value ?? 0);
          return (
            <tr key={r.id} className="border-t border-slate-100">
              <td className="py-1.5">
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    r.field === "price"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-purple-100 text-purple-700"
                  }`}
                >
                  {r.field === "price" ? "Fiyat" : "Maliyet"}
                </span>
              </td>
              <td className="py-1.5 text-right text-slate-500">
                {r.old_value != null ? formatTRY(r.old_value) : "—"}
              </td>
              <td className="py-1.5 text-right font-medium">
                <span className="inline-flex items-center justify-end gap-1">
                  {r.old_value != null &&
                    (isUp ? (
                      <ArrowUp className="h-3 w-3 text-rose-600" />
                    ) : (
                      <ArrowDown className="h-3 w-3 text-emerald-600" />
                    ))}
                  {formatTRY(r.new_value)}
                </span>
              </td>
              <td className="py-1.5 px-3 text-slate-600">
                {r.reason ?? "—"}
              </td>
              <td className="py-1.5 text-xs text-slate-600">
                {r.changed_by_admin_name ?? (
                  <span className="text-slate-400">Sistem</span>
                )}
              </td>
              <td className="py-1.5 text-slate-500 text-xs">
                {formatDateTime(r.changed_at)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
