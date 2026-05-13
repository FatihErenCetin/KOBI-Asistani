import Link from "next/link";
import { AlertTriangle, Boxes, PackageSearch } from "lucide-react";

import { api } from "@/lib/api";
import { formatTRY } from "@/lib/format";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: { low?: string };
}) {
  const products = await api.listProducts({ low_stock_only: searchParams.low === "1" });
  const lowCount = products.filter((p: any) => p.is_low).length;
  const totalValue = products.reduce((acc: number, p: any) => acc + Number(p.price ?? 0) * Number(p.stock ?? 0), 0);

  return (
    <div className="page-wrap">
      <header className="surface-card px-7 py-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-bold text-brand-700">
              <Boxes className="h-3.5 w-3.5" aria-hidden="true" />
              Stok ve ürün yönetimi
            </div>
            <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-950">Ürünler & Stok</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Kritik stokları erken görün, fiyat ve envanter yoğunluğunu hızlıca takip edin.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:min-w-[360px]">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Ürün</p>
              <p className="mt-2 text-2xl font-extrabold text-slate-950 tabular-nums">{products.length}</p>
            </div>
            <div className={`rounded-2xl border p-4 ${lowCount > 0 ? "border-rose-200 bg-rose-50" : "border-brand-200 bg-brand-50"}`}>
              <p className={`text-xs font-bold uppercase tracking-[0.14em] ${lowCount > 0 ? "text-rose-600" : "text-brand-600"}`}>Düşük stok</p>
              <p className={`mt-2 text-2xl font-extrabold tabular-nums ${lowCount > 0 ? "text-rose-700" : "text-brand-800"}`}>{lowCount}</p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-col gap-3 rounded-3xl border border-white/70 bg-white/75 p-3 shadow-card backdrop-blur sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <Link className={!searchParams.low ? "filter-pill filter-pill-active" : "filter-pill"} href="/products">Tümü</Link>
          <Link className={searchParams.low ? "filter-pill filter-pill-active" : "filter-pill"} href="/products?low=1">Düşük Stok</Link>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-600">
          Tahmini stok değeri: <span className="text-slate-950">{formatTRY(totalValue)}</span>
        </div>
      </div>

      <div className="table-shell">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-row">
                <th className="table-cell text-left">Ürün</th>
                <th className="table-cell text-left">Birim</th>
                <th className="table-cell text-right">Stok</th>
                <th className="table-cell text-right">Eşik</th>
                <th className="table-cell text-right">Fiyat</th>
                <th className="table-cell text-left">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {products.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center">
                    <PackageSearch className="mx-auto h-10 w-10 text-slate-300" aria-hidden="true" />
                    <p className="mt-3 text-sm font-semibold text-slate-500">Ürün bulunamadı</p>
                  </td>
                </tr>
              ) : (
                products.map((p: any) => {
                  const pct = Math.min(100, Math.round((Number(p.stock ?? 0) / Math.max(1, Number(p.low_stock_threshold ?? 1))) * 100));
                  return (
                    <tr key={p.id} className={`transition hover:bg-slate-50/90 ${p.is_low ? "bg-rose-50/40" : ""}`}>
                      <td className="table-cell font-bold text-slate-950">{p.name}</td>
                      <td className="table-cell text-slate-500">{p.unit}</td>
                      <td className="table-cell text-right font-extrabold text-slate-950 tabular-nums">{p.stock}</td>
                      <td className="table-cell text-right font-medium text-slate-500 tabular-nums">{p.low_stock_threshold}</td>
                      <td className="table-cell text-right font-bold text-slate-950 tabular-nums">{formatTRY(p.price)}</td>
                      <td className="table-cell">
                        {p.is_low ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-700">
                            <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" /> Kritik
                          </span>
                        ) : (
                          <span className="inline-flex rounded-full bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-700">Yeterli</span>
                        )}
                        <div className="mt-2 h-1.5 w-28 overflow-hidden rounded-full bg-slate-100">
                          <div className={p.is_low ? "h-full rounded-full bg-rose-500" : "h-full rounded-full bg-brand-500"} style={{ width: `${Math.max(8, pct)}%` }} />
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
