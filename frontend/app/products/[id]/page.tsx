"use client";

import { ArrowLeft, BarChart3, Boxes, Pencil, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { PriceHistoryTable } from "@/components/products/PriceHistoryTable";
import { ProductFormModal } from "@/components/products/ProductFormModal";
import { StockAdjustModal } from "@/components/products/StockAdjustModal";
import { StockMovementTable } from "@/components/products/StockMovementTable";
import { SupplierLinksPanel } from "@/components/products/SupplierLinksPanel";
import { api } from "@/lib/api";
import { formatTRY } from "@/lib/format";

export default function ProductDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = Number(params.id);
  const [product, setProduct] = useState<any | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [movements, setMovements] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [editOpen, setEditOpen] = useState(false);
  const [adjustOpen, setAdjustOpen] = useState(false);

  async function reload() {
    const [p, ph, mv, wh] = await Promise.all([
      api.getProduct(id),
      api.priceHistory(id),
      api.stockMovements(id),
      api.productWarehouseBreakdown(id),
    ]);
    setProduct(p);
    setHistory(ph);
    setMovements(mv);
    setWarehouses(wh);
  }

  useEffect(() => {
    reload();
  }, [id]);

  if (!product) {
    return <div className="p-8 text-slate-500">Yükleniyor…</div>;
  }

  const a = product.analytics ?? {};
  const margin = product.profit_margin_pct;

  return (
    <div className="max-w-6xl space-y-6">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/products"
            className="p-1.5 rounded hover:bg-slate-100"
            aria-label="Geri"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{product.name}</h1>
            <p className="text-sm text-slate-500">
              {product.category ?? "Kategorisiz"} · {product.unit}
              {product.barcode && ` · ${product.barcode}`}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setAdjustOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-300 rounded hover:bg-slate-50"
          >
            <Boxes className="h-4 w-4" /> Stok Hareketi
          </button>
          <button
            onClick={() => setEditOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
          >
            <Pencil className="h-4 w-4" /> Düzenle
          </button>
        </div>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Stat
          label="Stok"
          value={`${product.stock} ${product.unit}`}
          hint={product.is_low ? "Eşik altı" : undefined}
          hintColor="rose"
        />
        <Stat label="Fiyat" value={formatTRY(product.price)} />
        <Stat
          label="Maliyet"
          value={product.cost ? formatTRY(product.cost) : "—"}
        />
        <Stat
          label="Kâr marjı"
          value={margin != null ? `%${margin}` : "—"}
          hintColor={
            margin != null && margin < 15 ? "rose" : "emerald"
          }
        />
        <Stat
          label="Stok ömrü"
          value={a.days_of_stock != null ? `${a.days_of_stock} gün` : "—"}
          hint={a.daily_velocity ? `${a.daily_velocity}/g` : undefined}
        />
      </section>

      {warehouses.length > 1 && (
        <section className="bg-white border border-slate-200 rounded-lg p-5">
          <h2 className="font-semibold mb-3">Depo Dağılımı</h2>
          <ul className="space-y-1.5 text-sm">
            {warehouses.map((w) => (
              <li
                key={w.warehouse_id}
                className="flex justify-between border-b border-slate-100 pb-1.5 last:border-0"
              >
                <span className="text-slate-700">{w.warehouse_name}</span>
                <span className="font-medium">
                  {w.quantity} {product.unit}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <header className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-brand-600" />
            <h2 className="font-semibold">Son 30 gün</h2>
          </header>
          <ul className="space-y-1 text-sm">
            <li className="flex justify-between">
              <span className="text-slate-600">Satılan</span>
              <span className="font-medium">
                {a.units_sold_30d ?? 0} {product.unit}
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-slate-600">Ciro</span>
              <span className="font-medium">
                {formatTRY(a.revenue_30d ?? 0)}
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-slate-600">Son satış</span>
              <span className="font-medium text-xs">
                {a.last_sale_at
                  ? new Date(a.last_sale_at).toLocaleString("tr-TR")
                  : "—"}
              </span>
            </li>
          </ul>
        </div>
        <SupplierLinksPanel productId={product.id} />
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <header className="flex items-center gap-2 mb-3">
          <BarChart3 className="h-4 w-4 text-brand-600" />
          <h2 className="font-semibold">Fiyat & Maliyet Geçmişi</h2>
        </header>
        <PriceHistoryTable rows={history} />
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="font-semibold mb-3">Stok Hareketleri</h2>
        <StockMovementTable rows={movements} />
      </section>

      {editOpen && (
        <ProductFormModal
          open
          mode="edit"
          product={product}
          onClose={() => setEditOpen(false)}
          onSaved={reload}
        />
      )}
      <StockAdjustModal
        open={adjustOpen}
        product={product}
        onClose={() => setAdjustOpen(false)}
        onSaved={reload}
      />
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  hintColor,
}: {
  label: string;
  value: string;
  hint?: string;
  hintColor?: "rose" | "emerald";
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-xl font-semibold mt-1">{value}</p>
      {hint && (
        <p
          className={`text-xs mt-0.5 ${
            hintColor === "rose" ? "text-rose-600" : "text-emerald-600"
          }`}
        >
          {hint}
        </p>
      )}
    </div>
  );
}
