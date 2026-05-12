"use client";
import Link from "next/link";

import { formatDateTime, formatTRY, statusColor, statusLabel } from "@/lib/format";

export function OrderListRender({ data }: { data: any }) {
  const orders = data?.orders ?? [];
  if (!Array.isArray(orders) || orders.length === 0) return null;
  return (
    <table className="w-full bg-white border border-slate-200 rounded text-xs mt-2">
      <thead className="bg-slate-50 text-slate-600">
        <tr>
          <th className="text-left px-3 py-1.5">#</th>
          <th className="text-left px-3 py-1.5">Müşteri</th>
          <th className="text-left px-3 py-1.5">Durum</th>
          <th className="text-right px-3 py-1.5">Tutar</th>
          <th className="text-left px-3 py-1.5">Tarih</th>
        </tr>
      </thead>
      <tbody>
        {orders.map((o: any) => (
          <tr key={o.order_id ?? o.id} className="border-t border-slate-100">
            <td className="px-3 py-1.5">
              <Link href={`/orders/${o.order_id ?? o.id}`} className="text-brand-700 hover:underline">
                #{o.order_id ?? o.id}
              </Link>
            </td>
            <td className="px-3 py-1.5">{o.customer_name ?? "—"}</td>
            <td className="px-3 py-1.5">
              <span className={`px-1.5 py-0.5 rounded text-[10px] ${statusColor(o.status)}`}>
                {statusLabel(o.status)}
              </span>
            </td>
            <td className="px-3 py-1.5 text-right">{formatTRY(o.total)}</td>
            <td className="px-3 py-1.5 text-slate-600">{formatDateTime(o.created_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
