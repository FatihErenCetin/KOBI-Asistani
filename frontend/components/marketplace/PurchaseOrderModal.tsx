"use client";

import { Loader2, Plus, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { formatTRY } from "@/lib/format";

interface Supplier {
  id: number;
  name: string;
  category?: string | null;
  carrier?: string | null;
}

interface Product {
  id: number;
  name: string;
  unit: string;
  cost: number;
}

interface ItemDraft {
  product_id: number | "";
  quantity: number;
  unit_cost: number;
}

interface Props {
  open: boolean;
  supplier: Supplier;
  initialProductName?: string;
  initialQuantity?: number;
  initialUnitCost?: number | null;
  recommendationId?: number;
  onClose: () => void;
  onCreated: (po: any) => void;
}

export function PurchaseOrderModal({
  open,
  supplier,
  initialProductName,
  initialQuantity,
  initialUnitCost,
  recommendationId,
  onClose,
  onCreated,
}: Props) {
  const [products, setProducts] = useState<Product[]>([]);
  const [items, setItems] = useState<ItemDraft[]>([
    { product_id: "", quantity: 1, unit_cost: 0 },
  ]);
  const [notes, setNotes] = useState("");
  const [expectedDelivery, setExpectedDelivery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    api.listProducts({}).then((rows: any[]) =>
      setProducts(
        rows.map((p) => ({
          id: p.id,
          name: p.name,
          unit: p.unit,
          cost: p.cost ?? 0,
        })),
      ),
    );
  }, [open]);

  // İlk ürün önerisi (AI öneriden geliyorsa product_name + qty + cost preset)
  useEffect(() => {
    if (!open || !initialProductName || products.length === 0) return;
    const target = products.find(
      (p) => p.name.toLowerCase() === initialProductName.toLowerCase(),
    );
    if (target) {
      setItems([
        {
          product_id: target.id,
          quantity: initialQuantity ?? 5,
          unit_cost: initialUnitCost ?? target.cost,
        },
      ]);
    }
  }, [open, initialProductName, initialQuantity, initialUnitCost, products]);

  if (!open) return null;

  function updateItem(idx: number, patch: Partial<ItemDraft>) {
    setItems((cur) =>
      cur.map((it, i) => (i === idx ? { ...it, ...patch } : it)),
    );
  }

  function addItem() {
    setItems((cur) => [...cur, { product_id: "", quantity: 1, unit_cost: 0 }]);
  }

  function removeItem(idx: number) {
    setItems((cur) => cur.filter((_, i) => i !== idx));
  }

  const total = items.reduce(
    (sum, it) => sum + Number(it.quantity || 0) * Number(it.unit_cost || 0),
    0,
  );
  const validItems = items.filter(
    (it) => it.product_id !== "" && it.quantity > 0,
  );

  async function submit() {
    if (validItems.length === 0) {
      setError("En az bir geçerli ürün satırı gerekli.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const po = await api.createPurchaseOrder({
        supplier_id: supplier.id,
        items: validItems.map((it) => ({
          product_id: Number(it.product_id),
          quantity: Number(it.quantity),
          unit_cost: Number(it.unit_cost),
        })),
        expected_delivery: expectedDelivery || undefined,
        notes: notes || undefined,
        recommendation_id: recommendationId,
      });
      onCreated(po);
      onClose();
    } catch (e: any) {
      setError(e?.message ?? "Sipariş oluşturulamadı.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white shadow-xl">
        <header className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <div>
            <h2 className="text-base font-semibold">
              {supplier.name} — Satınalma Siparişi
            </h2>
            <p className="text-xs text-slate-500">
              {supplier.category ?? "Tedarikçi"}
              {supplier.carrier ? ` · ${supplier.carrier}` : ""}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="max-h-[60vh] space-y-4 overflow-y-auto px-5 py-4">
          {/* Items */}
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
              Ürünler
            </p>
            <div className="space-y-2">
              {items.map((it, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-[1fr_90px_110px_28px] gap-2 items-center"
                >
                  <select
                    value={it.product_id}
                    onChange={(e) => {
                      const pid = e.target.value === "" ? "" : Number(e.target.value);
                      const p = products.find((p) => p.id === pid);
                      updateItem(idx, {
                        product_id: pid,
                        unit_cost: p ? p.cost : it.unit_cost,
                      });
                    }}
                    className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
                  >
                    <option value="">— Ürün seç —</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.unit})
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    value={it.quantity}
                    onChange={(e) =>
                      updateItem(idx, { quantity: Number(e.target.value) })
                    }
                    placeholder="Adet"
                    className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm text-right tabular-nums"
                  />
                  <input
                    type="number"
                    min={0}
                    step={0.01}
                    value={it.unit_cost}
                    onChange={(e) =>
                      updateItem(idx, { unit_cost: Number(e.target.value) })
                    }
                    placeholder="Birim ₺"
                    className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm text-right tabular-nums"
                  />
                  <button
                    onClick={() => removeItem(idx)}
                    disabled={items.length === 1}
                    className="text-slate-400 hover:text-rose-600 disabled:opacity-30"
                    title="Satırı kaldır"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={addItem}
              className="mt-2 inline-flex items-center gap-1 text-xs text-brand-700 hover:underline"
            >
              <Plus className="h-3 w-3" /> Kalem ekle
            </button>
          </div>

          {/* Notes + delivery */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-600 block mb-1">
                Tahmini teslim
              </label>
              <input
                type="date"
                value={expectedDelivery}
                onChange={(e) => setExpectedDelivery(e.target.value)}
                className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">
                Not (opsiyonel)
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Özel istek..."
                className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
              />
            </div>
          </div>

          {/* Total */}
          <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
            <span className="text-xs uppercase tracking-wider text-slate-500">
              Tahmini toplam
            </span>
            <span className="text-lg font-semibold tabular-nums">
              {formatTRY(total)}
            </span>
          </div>

          {error && (
            <p className="text-xs text-rose-700 bg-rose-50 px-2 py-1.5 rounded">
              {error}
            </p>
          )}
        </div>

        <footer className="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3">
          <button
            onClick={onClose}
            className="text-sm px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-100"
          >
            Vazgeç
          </button>
          <button
            onClick={submit}
            disabled={busy || validItems.length === 0}
            className="inline-flex items-center gap-1.5 text-sm px-4 py-1.5 rounded bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50"
          >
            {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Sipariş Oluştur (Taslak)
          </button>
        </footer>
      </div>
    </div>
  );
}
