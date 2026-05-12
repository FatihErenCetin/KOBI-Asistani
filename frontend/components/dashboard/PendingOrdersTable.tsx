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
    <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <header className="px-5 py-3 border-b border-slate-200">
        <h2 className="font-semibold">{title}</h2>
      </header>
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-slate-600 text-xs">
          <tr>
            <th className="text-left px-5 py-2">#</th>
            <th className="text-left px-5 py-2">Müşteri</th>
            <th className="text-left px-5 py-2">Durum</th>
            <th className="text-right px-5 py-2">Tutar</th>
            <th className="text-left px-5 py-2">Oluşturuldu</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr><td colSpan={5} className="px-5 py-6 text-center text-slate-500">Kayıt yok</td></tr>
          )}
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-5 py-2">
                <Link href={`/orders/${r.id}`} className="text-brand-700 hover:underline">#{r.id}</Link>
              </td>
              <td className="px-5 py-2">{r.customer_name}</td>
              <td className="px-5 py-2">
                <span className={`px-2 py-1 rounded text-xs ${statusColor(r.status)}`}>
                  {statusLabel(r.status)}
                </span>
              </td>
              <td className="px-5 py-2 text-right">{formatTRY(r.total)}</td>
              <td className="px-5 py-2 text-slate-600">{formatDateTime(r.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
