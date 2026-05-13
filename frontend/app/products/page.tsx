"use client";

import { Boxes, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { ProductFormModal } from "@/components/products/ProductFormModal";
import { ProductRow } from "@/components/products/ProductRow";
import { StockAdjustModal } from "@/components/products/StockAdjustModal";
import { api } from "@/lib/api";

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lowOnly, setLowOnly] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [editing, setEditing] = useState<any | null>(null);
  const [adjusting, setAdjusting] = useState<any | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await api.listProducts({ low_stock_only: lowOnly });
      setProducts(rows);
    } finally {
      setLoading(false);
    }
  }, [lowOnly]);

  useEffect(() => {
    reload();
  }, [reload]);

  async function handleDelete(p: any) {
    if (
      !confirm(`"${p.name}" silinsin mi? (Soft delete — geri alınabilir.)`)
    ) {
      return;
    }
    await api.deleteProduct(p.id);
    reload();
  }

  return (
    <div className="max-w-7xl space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Ürünler & Stok</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Maliyet, kâr marjı ve 7 günlük satış hızı bir bakışta.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setLowOnly(false)}
            className={`px-3 py-1 text-sm rounded border ${
              !lowOnly
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white border-slate-300"
            }`}
          >
            Tümü
          </button>
          <button
            onClick={() => setLowOnly(true)}
            className={`px-3 py-1 text-sm rounded border ${
              lowOnly
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white border-slate-300"
            }`}
          >
            Düşük Stok
          </button>
          <button
            onClick={() => {
              setEditing(null);
              setFormMode("create");
            }}
            className="ml-2 inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Yeni Ürün
          </button>
        </div>
      </header>

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ürün</th>
            <th className="text-left px-4 py-2">Birim</th>
            <th className="text-right px-4 py-2">Stok</th>
            <th className="text-right px-4 py-2">Eşik</th>
            <th className="text-right px-4 py-2">Fiyat</th>
            <th className="text-right px-4 py-2">Maliyet</th>
            <th className="text-right px-4 py-2">Marj</th>
            <th className="text-left px-4 py-2">7g</th>
            <th className="text-right px-4 py-2">İşlem</th>
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td
                colSpan={9}
                className="text-center text-slate-500 py-8"
              >
                Yükleniyor…
              </td>
            </tr>
          )}
          {!loading && products.length === 0 && (
            <tr>
              <td colSpan={9} className="text-center text-slate-500 py-8">
                <Boxes className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                Hiç ürün yok.
              </td>
            </tr>
          )}
          {!loading &&
            products.map((p) => (
              <ProductRow
                key={p.id}
                product={p}
                onEdit={(prod) => {
                  setEditing(prod);
                  setFormMode("edit");
                }}
                onAdjust={(prod) => setAdjusting(prod)}
                onDelete={handleDelete}
              />
            ))}
        </tbody>
      </table>

      {formMode && (
        <ProductFormModal
          open
          mode={formMode}
          product={formMode === "edit" ? editing : undefined}
          onClose={() => setFormMode(null)}
          onSaved={reload}
        />
      )}
      <StockAdjustModal
        open={adjusting !== null}
        product={adjusting}
        onClose={() => setAdjusting(null)}
        onSaved={reload}
      />
    </div>
  );
}
