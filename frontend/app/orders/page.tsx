import Link from "next/link";
import { PackageCheck, Search, ShoppingBag } from "lucide-react";

import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY, statusLabel } from "@/lib/format";

const FILTERS = [
  { value: "", label: "Tümü" },
  { value: "pending", label: "Yeni" },
  { value: "prepared", label: "Hazırlandı" },
  { value: "shipped", label: "Kargoda" },
  { value: "delivered", label: "Teslim" },
];

export default async function OrdersPage({
  searchParams,
}: {
  searchParams: { status?: string; limit?: string };
}) {
  const params: Record<string, string> = { limit: searchParams.limit ?? "50" };
  if (searchParams.status) params.status = searchParams.status;
  const orders = await api.listOrders(params);
  const totalRevenue = orders.reduce((acc: number, order: any) => acc + Number(order.total ?? 0), 0);

  return (
    <div className="page-wrap">
      <header className="surface-card overflow-hidden px-7 py-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-bold text-brand-700">
              <ShoppingBag className="h-3.5 w-3.5" aria-hidden="true" />
              Sipariş operasyonu
            </div>
            <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-950">Siparişler</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Müşteri, durum, tutar ve oluşturulma tarihlerini tek tabloda takip edin.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:min-w-[360px]">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Kayıt</p>
              <p className="mt-2 text-2xl font-extrabold text-slate-950 tabular-nums">{orders.length}</p>
            </div>
            <div className="rounded-2xl border border-brand-200 bg-brand-50 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-brand-600">Toplam</p>
              <p className="mt-2 text-xl font-extrabold text-brand-800 tabular-nums">{formatTRY(totalRevenue)}</p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-col gap-3 rounded-3xl border border-white/70 bg-white/75 p-3 shadow-card backdrop-blur lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((filter) => {
            const active = searchParams.status === filter.value || (!searchParams.status && !filter.value);
            return (
              <Link
                key={filter.value || "all"}
                href={filter.value ? `/orders?status=${filter.value}` : "/orders"}
                className={active ? "filter-pill filter-pill-active" : "filter-pill"}
              >
                {filter.label}
              </Link>
            );
          })}
        </div>
        <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-400">
          <Search className="h-4 w-4" aria-hidden="true" />
          Arama demo içinde AI Asistan üzerinden yapılabilir
        </div>
      </div>

      <div className="table-shell">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-row">
                <th className="table-cell text-left">Sipariş</th>
                <th className="table-cell text-left">Müşteri</th>
                <th className="table-cell text-left">Durum</th>
                <th className="table-cell text-right">Tutar</th>
                <th className="table-cell text-left">Tarih</th>
                <th className="table-cell text-right">Detay</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {orders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center">
                    <PackageCheck className="mx-auto h-10 w-10 text-slate-300" aria-hidden="true" />
                    <p className="mt-3 text-sm font-semibold text-slate-500">Bu filtrede sipariş yok</p>
                  </td>
                </tr>
              ) : (
                orders.map((o: any) => (
                  <tr key={o.id} className="transition hover:bg-slate-50/90">
                    <td className="table-cell">
                      <Link href={`/orders/${o.id}`} className="font-mono font-bold text-brand-700 hover:underline">#{o.id}</Link>
                    </td>
                    <td className="table-cell font-semibold text-slate-900">{o.customer?.name ?? "-"}</td>
                    <td className="table-cell"><OrderStatusBadge status={o.status} /></td>
                    <td className="table-cell text-right font-bold text-slate-950 tabular-nums">{formatTRY(o.total)}</td>
                    <td className="table-cell text-xs font-medium text-slate-500">{formatDateTime(o.created_at)}</td>
                    <td className="table-cell text-right">
                      <Link href={`/orders/${o.id}`} className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700">
                        {statusLabel(o.status)}
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
