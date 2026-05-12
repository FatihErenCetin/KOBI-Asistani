import Link from "next/link";
import { notFound } from "next/navigation";

import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { ShipmentTimeline } from "@/components/orders/ShipmentTimeline";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

export default async function OrderDetailPage({ params }: { params: { id: string } }) {
  let order: any;
  try {
    order = await api.getOrder(Number(params.id));
  } catch {
    notFound();
  }
  return (
    <div className="max-w-5xl space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">Sipariş</p>
          <h1 className="text-2xl font-bold">#{order.id}</h1>
        </div>
        <div className="text-right">
          <OrderStatusBadge status={order.status} />
          <p className="text-xs text-slate-500 mt-1">{formatDateTime(order.created_at)}</p>
        </div>
      </header>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <p className="text-sm text-slate-500">Müşteri</p>
        <Link
          href={`/customers/${order.customer.id}`}
          className="text-brand-700 hover:underline font-medium"
        >
          {order.customer.name}
        </Link>
        <p className="text-sm text-slate-600">{order.customer.phone ?? "—"}</p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="bg-white border border-slate-200 rounded-lg p-5">
          <h2 className="font-semibold mb-3">Sipariş Kalemleri</h2>
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                <th className="text-left">Ürün</th>
                <th className="text-right">Miktar</th>
                <th className="text-right">Birim</th>
                <th className="text-right">Toplam</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((it: any) => (
                <tr key={it.id} className="border-t border-slate-100">
                  <td className="py-2">{it.product_name}</td>
                  <td className="py-2 text-right">{it.quantity}</td>
                  <td className="py-2 text-right">{formatTRY(it.unit_price)}</td>
                  <td className="py-2 text-right">{formatTRY(it.quantity * it.unit_price)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-slate-200 font-semibold">
                <td colSpan={3} className="py-2 text-right">Toplam</td>
                <td className="py-2 text-right">{formatTRY(order.total)}</td>
              </tr>
            </tfoot>
          </table>
        </section>

        <section className="bg-white border border-slate-200 rounded-lg p-5">
          <h2 className="font-semibold mb-3">Kargo</h2>
          <ShipmentTimeline shipment={order.shipment} />
        </section>
      </div>
    </div>
  );
}
