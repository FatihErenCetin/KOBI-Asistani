import Link from "next/link";

import { formatDateTime, formatTRY, statusColor, statusLabel } from "@/lib/format";

interface Row {
  id: number;
  customer_name: string;
  total: number;
  status: string;
  created_at: string;
  promised_delivery: string | null;
}

export function PendingOrdersTable({ rows, title }: { rows: Row[]; title: string }) {
  return (
    <section className="table-shell">
      <header className="border-b border-slate-100 px-6 py-5">
        <h2 className="section-title">{title}</h2>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="table-head-row">
              <th className="table-cell text-left">Sipariş</th>
              <th className="table-cell text-left">Müşteri</th>
              <th className="table-cell text-left">Durum</th>
              <th className="table-cell text-right">Tutar</th>
              <th className="table-cell text-left">Oluşturuldu</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length === 0 && (
              <tr><td colSpan={5} className="px-6 py-10 text-center text-sm font-medium text-slate-400">Kayıt yok</td></tr>
            )}
            {rows.map((r) => (
              <tr key={r.id} className="transition hover:bg-slate-50/90">
                <td className="table-cell"><Link href={`/orders/${r.id}`} className="font-mono font-bold text-brand-700 hover:underline">#{r.id}</Link></td>
                <td className="table-cell font-semibold text-slate-900">{r.customer_name}</td>
                <td className="table-cell"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${statusColor(r.status)}`}>{statusLabel(r.status)}</span></td>
                <td className="table-cell text-right font-bold text-slate-950 tabular-nums">{formatTRY(r.total)}</td>
                <td className="table-cell text-xs font-medium text-slate-500">{formatDateTime(r.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
