"use client";

import { AlertTriangle, Clock, Package, TrendingDown } from "lucide-react";
import Link from "next/link";

import { formatDateTime, formatTRY } from "@/lib/format";

/* -------------------------------------------------------------------------- */
/*  LowMarginRender                                                            */
/* -------------------------------------------------------------------------- */

export function LowMarginRender({ data }: { data: any }) {
  const products = data?.products ?? [];
  if (products.length === 0) {
    return (
      <p className="text-xs text-slate-500 mt-2">Eşik altında ürün yok.</p>
    );
  }
  return (
    <div className="mt-2">
      <p className="text-xs text-slate-500 mb-1">
        Marj eşiği: %{data.threshold} · {data.count} ürün
      </p>
      <table className="w-full bg-white border border-slate-200 rounded text-xs">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="text-left px-3 py-1.5">Ürün</th>
            <th className="text-right px-3 py-1.5">Fiyat</th>
            <th className="text-right px-3 py-1.5">Maliyet</th>
            <th className="text-right px-3 py-1.5">Marj</th>
            <th className="text-right px-3 py-1.5">Stok</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p: any) => (
            <tr key={p.id} className="border-t border-slate-100">
              <td className="px-3 py-1.5">
                <Link
                  href={`/products/${p.id}`}
                  className="text-brand-700 hover:underline"
                >
                  {p.name}
                </Link>
              </td>
              <td className="px-3 py-1.5 text-right">
                {formatTRY(p.price)}
              </td>
              <td className="px-3 py-1.5 text-right text-slate-500">
                {formatTRY(p.cost)}
              </td>
              <td className="px-3 py-1.5 text-right">
                <span className="inline-flex items-center gap-1 text-rose-700 font-medium">
                  <TrendingDown className="h-3 w-3" />%{p.margin_pct}
                </span>
              </td>
              <td className="px-3 py-1.5 text-right text-slate-600">
                {p.stock} {p.unit}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  FastDepletingRender                                                        */
/* -------------------------------------------------------------------------- */

export function FastDepletingRender({ data }: { data: any }) {
  const products = data?.products ?? [];
  if (products.length === 0) {
    return (
      <p className="text-xs text-slate-500 mt-2">
        Bu eşikte tükenmek üzere ürün yok.
      </p>
    );
  }
  return (
    <div className="mt-2">
      <p className="text-xs text-slate-500 mb-1">
        Eşik: {data.max_days} gün · {data.count} ürün
      </p>
      <table className="w-full bg-white border border-slate-200 rounded text-xs">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="text-left px-3 py-1.5">Ürün</th>
            <th className="text-right px-3 py-1.5">Stok</th>
            <th className="text-right px-3 py-1.5">Günlük Hız</th>
            <th className="text-right px-3 py-1.5">Kalan</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p: any) => (
            <tr key={p.id} className="border-t border-slate-100">
              <td className="px-3 py-1.5">
                <Link
                  href={`/products/${p.id}`}
                  className="text-brand-700 hover:underline"
                >
                  {p.name}
                </Link>
              </td>
              <td className="px-3 py-1.5 text-right">
                {p.stock} {p.unit}
              </td>
              <td className="px-3 py-1.5 text-right text-slate-600">
                {p.daily_velocity}/g
              </td>
              <td className="px-3 py-1.5 text-right">
                <span
                  className={`inline-flex items-center gap-1 font-medium ${
                    p.days_of_stock <= 3
                      ? "text-rose-700"
                      : p.days_of_stock <= 7
                        ? "text-amber-700"
                        : "text-slate-700"
                  }`}
                >
                  <Clock className="h-3 w-3" />
                  {p.days_of_stock} gün
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  SupplierPerformanceRender                                                  */
/* -------------------------------------------------------------------------- */

export function SupplierPerformanceRender({ data }: { data: any }) {
  const suppliers = data?.suppliers ?? [];
  if (suppliers.length === 0) {
    return (
      <p className="text-xs text-slate-500 mt-2">Tedarikçi verisi yok.</p>
    );
  }
  return (
    <table className="w-full bg-white border border-slate-200 rounded text-xs mt-2">
      <thead className="bg-slate-50 text-slate-600">
        <tr>
          <th className="text-left px-3 py-1.5">Tedarikçi</th>
          <th className="text-right px-3 py-1.5">Ort. Lead Time</th>
          <th className="text-right px-3 py-1.5">Bağlı Ürün</th>
          <th className="text-left px-3 py-1.5">Son Alış</th>
        </tr>
      </thead>
      <tbody>
        {suppliers.map((s: any) => (
          <tr key={s.supplier_id} className="border-t border-slate-100">
            <td className="px-3 py-1.5">
              <Link
                href={`/suppliers/${s.supplier_id}`}
                className="text-brand-700 hover:underline"
              >
                {s.supplier_name}
              </Link>
            </td>
            <td className="px-3 py-1.5 text-right">
              {s.avg_lead_time_days != null
                ? `${s.avg_lead_time_days} gün`
                : "—"}
            </td>
            <td className="px-3 py-1.5 text-right">{s.linked_product_count}</td>
            <td className="px-3 py-1.5 text-slate-600">
              {s.last_purchase_at ? formatDateTime(s.last_purchase_at) : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/* -------------------------------------------------------------------------- */
/*  ProductAnalyticsCard                                                       */
/* -------------------------------------------------------------------------- */

export function ProductAnalyticsCard({ data }: { data: any }) {
  const p = data?.product;
  const a = data?.analytics;
  if (!p || !a) return null;

  const margin =
    p.cost && p.cost > 0 && p.price > 0
      ? Math.round(((p.price - p.cost) / p.price) * 1000) / 10
      : null;

  return (
    <div className="mt-2 bg-white border border-slate-200 rounded p-3 max-w-md">
      <header className="flex items-center justify-between mb-2">
        <Link
          href={`/products/${p.id}`}
          className="font-semibold text-brand-700 hover:underline inline-flex items-center gap-1.5"
        >
          <Package className="h-4 w-4" />
          {p.name}
        </Link>
        <span className="text-xs text-slate-500">{p.unit}</span>
      </header>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
        <dt className="text-slate-500">Stok</dt>
        <dd className="text-right font-medium">
          {p.stock} {p.unit}
        </dd>
        <dt className="text-slate-500">Fiyat / Maliyet</dt>
        <dd className="text-right">
          {formatTRY(p.price)} / {p.cost ? formatTRY(p.cost) : "—"}
        </dd>
        <dt className="text-slate-500">Marj</dt>
        <dd className="text-right font-medium">
          {margin != null ? `%${margin}` : "—"}
        </dd>
        <dt className="text-slate-500">30 günlük satış</dt>
        <dd className="text-right">{a.units_sold_30d}</dd>
        <dt className="text-slate-500">30 günlük ciro</dt>
        <dd className="text-right">{formatTRY(a.revenue_30d)}</dd>
        <dt className="text-slate-500">Günlük hız</dt>
        <dd className="text-right">{a.daily_velocity}/g</dd>
        <dt className="text-slate-500">Kalan stok</dt>
        <dd className="text-right font-medium">
          {a.days_of_stock != null ? `${a.days_of_stock} gün` : "—"}
        </dd>
      </dl>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  CategoryStockRender                                                        */
/* -------------------------------------------------------------------------- */

export function CategoryStockRender({ data }: { data: any }) {
  const rows = data?.categories ?? [];
  if (rows.length === 0) {
    return <p className="text-xs text-slate-500 mt-2">Kategori verisi yok.</p>;
  }
  return (
    <table className="w-full bg-white border border-slate-200 rounded text-xs mt-2">
      <thead className="bg-slate-50 text-slate-600">
        <tr>
          <th className="text-left px-3 py-1.5">Kategori</th>
          <th className="text-right px-3 py-1.5">Ürün</th>
          <th className="text-right px-3 py-1.5">Toplam Stok</th>
          <th className="text-right px-3 py-1.5">Düşük Stok</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r: any) => (
          <tr key={r.category} className="border-t border-slate-100">
            <td className="px-3 py-1.5 font-medium">{r.category}</td>
            <td className="px-3 py-1.5 text-right">{r.product_count}</td>
            <td className="px-3 py-1.5 text-right">{r.total_stock}</td>
            <td className="px-3 py-1.5 text-right">
              {r.low_stock_count > 0 ? (
                <span className="inline-flex items-center gap-1 text-rose-700">
                  <AlertTriangle className="h-3 w-3" />
                  {r.low_stock_count}
                </span>
              ) : (
                <span className="text-slate-400">0</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

