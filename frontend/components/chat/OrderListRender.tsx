"use client";

import Link from "next/link";

import { formatDateTime, formatTRY, statusColor, statusLabel } from "@/lib/format";

export function OrderListRender({ data }: { data: any }) {
  const orders = data?.orders ?? [];
  if (!Array.isArray(orders) || orders.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
              <th className="px-3 py-2 text-left">Sipariş</th>
              <th className="px-3 py-2 text-left">Müşteri</th>
              <th className="px-3 py-2 text-left">Durum</th>
              <th className="px-3 py-2 text-right">Tutar</th>
              <th className="px-3 py-2 text-left">Tarih</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((o: any) => (
              <tr key={o.order_id ?? o.id} className="transition hover:bg-slate-50">
                <td className="px-3 py-2.5">
                  <Link href={`/orders/${o.order_id ?? o.id}`} className="font-mono font-bold text-brand-700 hover:underline">
                    #{o.order_id ?? o.id}
                  </Link>
                </td>
                <td className="px-3 py-2.5 font-semibold text-slate-900">{o.customer_name ?? "-"}</td>
                <td className="px-3 py-2.5">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${statusColor(o.status)}`}>
                    {statusLabel(o.status)}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right font-bold text-slate-900 tabular-nums">{formatTRY(o.total)}</td>
                <td className="px-3 py-2.5 font-medium text-slate-500">{formatDateTime(o.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
