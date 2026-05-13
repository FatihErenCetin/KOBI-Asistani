"use client";

import { Loader2, Plus, Star, Trash2, Warehouse as WarehouseIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";

interface Warehouse {
  id: number;
  name: string;
  code: string | null;
  address: string | null;
  is_default: boolean;
  is_active: boolean;
}

export default function WarehousesPage() {
  const [rows, setRows] = useState<Warehouse[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    code: "",
    address: "",
    is_default: false,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    setRows(await api.listWarehouses());
  }

  useEffect(() => {
    reload();
  }, []);

  async function submit() {
    setError(null);
    if (!form.name.trim()) {
      setError("Ad zorunludur.");
      return;
    }
    setBusy(true);
    try {
      await api.createWarehouse({
        name: form.name,
        code: form.code || null,
        address: form.address || null,
        is_default: form.is_default,
      });
      setOpen(false);
      setForm({ name: "", code: "", address: "", is_default: false });
      reload();
    } catch (e: any) {
      setError(e?.message ?? "Hata");
    } finally {
      setBusy(false);
    }
  }

  async function remove(w: Warehouse) {
    if (w.is_default) {
      alert("Ana depo silinemez.");
      return;
    }
    if (!confirm(`"${w.name}" depo silinsin mi?`)) return;
    try {
      await api.deleteWarehouse(w.id);
      reload();
    } catch (e: any) {
      alert(e?.message ?? "Silinemedi");
    }
  }

  async function makeDefault(w: Warehouse) {
    if (w.is_default) return;
    await api.updateWarehouse(w.id, { is_default: true });
    reload();
  }

  return (
    <div className="max-w-4xl space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Depolar</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Çoklu depo yönetimi. Ana depo varsayılan olarak kullanılır.
          </p>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> Yeni Depo
        </button>
      </header>

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ad</th>
            <th className="text-left px-4 py-2">Kod</th>
            <th className="text-left px-4 py-2">Adres</th>
            <th className="text-center px-4 py-2">Ana</th>
            <th className="text-right px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="text-center text-slate-500 py-8">
                <WarehouseIcon className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                Depo yok.
              </td>
            </tr>
          )}
          {rows.map((w) => (
            <tr
              key={w.id}
              className="border-t border-slate-100 hover:bg-slate-50"
            >
              <td className="px-4 py-2 font-medium">{w.name}</td>
              <td className="px-4 py-2 text-slate-600">{w.code ?? "—"}</td>
              <td className="px-4 py-2 text-slate-600">{w.address ?? "—"}</td>
              <td className="px-4 py-2 text-center">
                {w.is_default ? (
                  <Star className="h-4 w-4 inline text-amber-500 fill-amber-500" />
                ) : (
                  <button
                    onClick={() => makeDefault(w)}
                    className="text-xs text-slate-400 hover:text-brand-600"
                    title="Ana depo yap"
                  >
                    yap
                  </button>
                )}
              </td>
              <td className="px-4 py-2 text-right">
                <button
                  onClick={() => remove(w)}
                  disabled={w.is_default}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded disabled:opacity-30 disabled:hover:bg-transparent"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Yeni Depo"
        size="sm"
      >
        <div className="space-y-3 text-sm">
          <div>
            <label className="block text-xs text-slate-600 mb-1">Ad *</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">Kod</label>
            <input
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              placeholder="ör: sube1"
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">Adres</label>
            <input
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <label className="inline-flex items-center text-sm">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) =>
                setForm({ ...form, is_default: e.target.checked })
              }
              className="mr-2"
            />
            Ana depo olarak işaretle
          </label>
          {error && (
            <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
              {error}
            </p>
          )}
        </div>
        <footer className="mt-4 flex justify-end gap-2">
          <button
            onClick={() => setOpen(false)}
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
            Kaydet
          </button>
        </footer>
      </Modal>
    </div>
  );
}
