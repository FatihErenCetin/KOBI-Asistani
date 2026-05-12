import Link from "next/link";

import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

export default async function OrdersPage({
  searchParams,
}: {
  searchParams: { status?: string; limit?: string };
}) {
  const params: Record<string, string> = { limit: searchParams.limit ?? "50" };
  if (searchParams.status) params.status = searchParams.status;
  const orders = await api.listOrders(params);

  return (
    <div className="max-w-6xl space-y-5">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Siparişler</h1>
        <div className="flex gap-2 text-sm">
          {["", "pending", "prepared", "shipped", "delivered"].map((s) => (
            <Link
              key={s || "all"}
              href={s ? `/orders?status=${s}` : "/orders"}
              className={`px-3 py-1 rounded border ${
                searchParams.status === s || (!searchParams.status && !s)
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white border-slate-300"
              }`}
            >
              {s ? s : "tüm"}
            </Link>
          ))}
        </div>
      </header>
      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50">
          <tr className="text-xs text-slate-600">
            <th className="text-left px-4 py-2">#</th>
            <th className="text-left px-4 py-2">Müşteri</th>
            <th className="text-left px-4 py-2">Durum</th>
            <th className="text-right px-4 py-2">Tutar</th>
            <th className="text-left px-4 py-2">Tarih</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o: any) => (
            <tr key={o.id} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-4 py-2">
                <Link href={`/orders/${o.id}`} className="text-brand-700 hover:underline">
                  #{o.id}
                </Link>
              </td>
              <td className="px-4 py-2">{o.customer.name}</td>
              <td className="px-4 py-2"><OrderStatusBadge status={o.status} /></td>
              <td className="px-4 py-2 text-right">{formatTRY(o.total)}</td>
              <td className="px-4 py-2 text-slate-600">{formatDateTime(o.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
