"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";

const REASONS = [
  { value: "purchase", label: "Alım (giriş)" },
  { value: "adjustment", label: "Sayım / düzeltme" },
  { value: "return", label: "İade" },
  { value: "waste", label: "Fire / hasar" },
];

interface ProductLike {
  id: number;
  name: string;
  unit: string;
  stock: number;
}

export function StockAdjustModal({
  open,
  product,
  onClose,
  onSaved,
}: {
  open: boolean;
  product: ProductLike | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [delta, setDelta] = useState(0);
  const [reason, setReason] = useState("purchase");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | null>(null);

  useEffect(() => {
    if (open) {
      setDelta(0);
      setReason("purchase");
      setNote("");
      setError(null);
      api
        .listWarehouses()
        .then((ws: any[]) => {
          setWarehouses(ws);
          const def = ws.find((w) => w.is_default) ?? ws[0];
          setWarehouseId(def?.id ?? null);
        })
        .catch(() => setWarehouses([]));
    }
  }, [open]);

  if (!product) return null;

  async function submit() {
    if (!product) return;
    setError(null);
    setBusy(true);
    try {
      const payload: any = {
        delta: Number(delta),
        reason,
        note: note || undefined,
      };
      if (warehouseId) payload.warehouse_id = warehouseId;
      await api.adjustStock(product.id, payload);
      onSaved();
      onClose();
    } catch (e: any) {
      setError(e?.message ?? "Kayıt başarısız");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Stok Hareketi: ${product.name}`}
      size="sm"
    >
      <p className="text-xs text-slate-500 mb-3">
        Mevcut stok:{" "}
        <span className="font-medium">
          {product.stock} {product.unit}
        </span>
      </p>

      {warehouses.length > 1 && (
        <>
          <label className="block text-xs text-slate-600 mb-1">Depo</label>
          <select
            value={warehouseId ?? ""}
            onChange={(e) => setWarehouseId(Number(e.target.value))}
            className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
          >
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
                {w.is_default && " (ana)"}
              </option>
            ))}
          </select>
        </>
      )}

      <label className="block text-xs text-slate-600 mb-1">Sebep</label>
      <select
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
      >
        {REASONS.map((r) => (
          <option key={r.value} value={r.value}>
            {r.label}
          </option>
        ))}
      </select>

      <label className="block text-xs text-slate-600 mb-1">
        Miktar (+ giriş, − çıkış)
      </label>
      <input
        type="number"
        value={delta}
        onChange={(e) => setDelta(Number(e.target.value))}
        className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
      />

      <label className="block text-xs text-slate-600 mb-1">Not</label>
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="ör: tedarikçiden gelen 5 kg"
        className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-4"
      />

      {error && (
        <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2 mb-3">
          {error}
        </p>
      )}

      <footer className="flex justify-end gap-2">
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm rounded border border-slate-300"
        >
          Vazgeç
        </button>
        <button
          onClick={submit}
          disabled={busy || delta === 0}
          className="px-3 py-1.5 text-sm rounded bg-brand-600 text-white disabled:opacity-50 inline-flex items-center gap-1.5"
        >
          {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Kaydet
        </button>
      </footer>
    </Modal>
  );
}
