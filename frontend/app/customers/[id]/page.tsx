import Link from "next/link";

import { api } from "@/lib/api";
import { formatDateTime, formatTRY, statusColor, statusLabel } from "@/lib/format";

export default async function CustomerDetailPage({ params }: { params: { id: string } }) {
  const orders = await api.customerOrders(Number(params.id));
  const customer = orders[0]?.customer ?? { name: "?", phone: null };
  const total = orders.reduce((acc: number, o: any) => acc + o.total, 0);
  return (
    <div className="max-w-5xl space-y-6">
      <header>
        <p className="text-sm text-slate-500">Müşteri</p>
        <h1 className="text-2xl font-bold">{customer.name}</h1>
        <p className="text-sm text-slate-600">{customer.phone ?? "—"}</p>
      </header>

      <section className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs uppercase tracking-wider text-slate-500">Toplam sipariş</p>
          <p className="text-2xl font-semibold">{orders.length}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs uppercase tracking-wider text-slate-500">Toplam harcama</p>
          <p className="text-2xl font-semibold">{formatTRY(total)}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs uppercase tracking-wider text-slate-500">Son sipariş</p>
          <p className="text-sm font-medium mt-1">
            {orders[0] ? formatDateTime(orders[0].created_at) : "—"}
          </p>
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <header className="px-5 py-3 border-b border-slate-200">
          <h2 className="font-semibold">Sipariş Geçmişi</h2>
        </header>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-600">
            <tr>
              <th className="text-left px-4 py-2">#</th>
              <th className="text-left px-4 py-2">Tarih</th>
              <th className="text-left px-4 py-2">Durum</th>
              <th className="text-right px-4 py-2">Tutar</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o: any) => (
              <tr key={o.id} className="border-t border-slate-100">
                <td className="px-4 py-2">
                  <Link href={`/orders/${o.id}`} className="text-brand-700 hover:underline">
                    #{o.id}
                  </Link>
                </td>
                <td className="px-4 py-2 text-slate-600">{formatDateTime(o.created_at)}</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-1 rounded text-xs ${statusColor(o.status)}`}>
                    {statusLabel(o.status)}
                  </span>
                </td>
                <td className="px-4 py-2 text-right">{formatTRY(o.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
