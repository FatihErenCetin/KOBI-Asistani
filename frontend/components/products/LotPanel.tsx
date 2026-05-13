"use client";

import { AlertTriangle, Loader2, Plus, Tag } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

interface Lot {
  id: number;
  lot_number: string;
  warehouse_name: string | null;
  quantity: number;
  expiry_date: string | null;
  supplier_name: string | null;
  received_at: string;
}

export function LotPanel({
  productId,
  productUnit,
}: {
  productId: number;
  productUnit: string;
}) {
  const [lots, setLots] = useState<Lot[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [form, setForm] = useState({
    warehouse_id: "",
    lot_number: "",
    quantity: "",
    expiry_date: "",
    supplier_id: "",
    note: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    setLots(await api.productLots(productId));
  }

  useEffect(() => {
    reload();
  }, [productId]);

  useEffect(() => {
    if (addOpen) {
      api.listWarehouses().then((ws: any[]) => {
        setWarehouses(ws);
        const def = ws.find((w) => w.is_default) ?? ws[0];
        if (def) setForm((f) => ({ ...f, warehouse_id: String(def.id) }));
      });
      api.listSuppliers().then(setSuppliers);
    }
  }, [addOpen]);

  async function submit() {
    setError(null);
    if (!form.warehouse_id || !form.lot_number.trim() || !form.quantity) {
      setError("Depo, lot numarası ve miktar zorunlu.");
      return;
    }
    setBusy(true);
    try {
      await api.createProductLot(productId, {
        warehouse_id: Number(form.warehouse_id),
        lot_number: form.lot_number,
        quantity: Number(form.quantity),
        expiry_date: form.expiry_date || null,
        supplier_id: form.supplier_id ? Number(form.supplier_id) : null,
        note: form.note || null,
      });
      setAddOpen(false);
      setForm({
        warehouse_id: form.warehouse_id,
        lot_number: "",
        quantity: "",
        expiry_date: "",
        supplier_id: "",
        note: "",
      });
      reload();
    } catch (e: any) {
      setError(e?.message ?? "Hata");
    } finally {
      setBusy(false);
    }
  }

  function expiryClass(date: string | null): string {
    if (!date) return "text-slate-500";
    const days = Math.floor(
      (new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24),
    );
    if (days < 0) return "text-rose-700 font-medium";
    if (days <= 7) return "text-rose-700";
    if (days <= 30) return "text-amber-700";
    return "text-slate-700";
  }

  return (
    <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <header className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
        <h2 className="font-semibold inline-flex items-center gap-1.5">
          <Tag className="h-4 w-4 text-brand-600" />
          Lot/Batch Listesi
        </h2>
        <button
          onClick={() => setAddOpen(true)}
          className="text-sm inline-flex items-center gap-1 text-brand-700 hover:underline"
        >
          <Plus className="h-3.5 w-3.5" /> Lot Ekle
        </button>
      </header>

      {lots.length === 0 ? (
        <p className="text-sm text-slate-500 p-5">
          Henüz lot kaydı yok. Lot olmadan da stok sistemi çalışır; lot
          ekleyerek son kullanma tarihi takibi yapabilirsiniz.
        </p>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-600">
            <tr>
              <th className="text-left px-4 py-2">Lot No</th>
              <th className="text-left px-4 py-2">Depo</th>
              <th className="text-right px-4 py-2">Miktar</th>
              <th className="text-left px-4 py-2">SKT</th>
              <th className="text-left px-4 py-2">Tedarikçi</th>
              <th className="text-left px-4 py-2">Alış</th>
            </tr>
          </thead>
          <tbody>
            {lots.map((l) => (
              <tr key={l.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-medium">{l.lot_number}</td>
                <td className="px-4 py-2 text-slate-600">
                  {l.warehouse_name ?? "—"}
                </td>
                <td className="px-4 py-2 text-right">
                  {l.quantity} {productUnit}
                </td>
                <td className={`px-4 py-2 text-xs ${expiryClass(l.expiry_date)}`}>
                  {l.expiry_date ? (
                    <span className="inline-flex items-center gap-1">
                      {expiryClass(l.expiry_date).includes("rose") && (
                        <AlertTriangle className="h-3 w-3" />
                      )}
                      {l.expiry_date}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-2 text-slate-600 text-xs">
                  {l.supplier_name ?? "—"}
                </td>
                <td className="px-4 py-2 text-xs text-slate-500">
                  {formatDateTime(l.received_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Yeni Lot Ekle"
        size="md"
      >
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <label className="block text-xs text-slate-600 mb-1">Depo *</label>
            <select
              value={form.warehouse_id}
              onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            >
              <option value="">— Seç —</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">
              Lot Numarası *
            </label>
            <input
              value={form.lot_number}
              onChange={(e) => setForm({ ...form, lot_number: e.target.value })}
              placeholder="ör: B-2024-001"
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">Miktar *</label>
            <input
              type="number"
              step="0.01"
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">
              Son Kullanma Tarihi
            </label>
            <input
              type="date"
              value={form.expiry_date}
              onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">
              Tedarikçi
            </label>
            <select
              value={form.supplier_id}
              onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            >
              <option value="">—</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">Not</label>
            <input
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
        </div>
        {error && (
          <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2 mt-3">
            {error}
          </p>
        )}
        <footer className="mt-4 flex justify-end gap-2">
          <button
            onClick={() => setAddOpen(false)}
            className="px-3 py-1.5 text-sm rounded border border-slate-300"
          >
            Vazgeç
          </button>
          <button
            onClick={submit}
            disabled={busy}
            className="px-3 py-1.5 text-sm rounded bg-brand-600 text-white disabled:opacity-50 inline-flex items-center gap-1.5"
          >
            {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Ekle
          </button>
        </footer>
      </Modal>
    </section>
  );
}
