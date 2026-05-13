"use client";

import { Plus, Star, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

interface SupplierLink {
  id: number;
  supplier_id: number;
  supplier_name: string;
  supplier_sku: string | null;
  last_unit_cost: number | null;
  last_purchase_at: string | null;
  lead_time_days: number | null;
  is_preferred: boolean;
  notes: string | null;
}

interface SupplierOption {
  id: number;
  name: string;
}

interface AddForm {
  supplier_id: string;
  supplier_sku: string;
  last_unit_cost: string;
  lead_time_days: string;
  is_preferred: boolean;
}

const EMPTY_FORM: AddForm = {
  supplier_id: "",
  supplier_sku: "",
  last_unit_cost: "",
  lead_time_days: "",
  is_preferred: false,
};

export function SupplierLinksPanel({ productId }: { productId: number }) {
  const [links, setLinks] = useState<SupplierLink[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierOption[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState<AddForm>(EMPTY_FORM);

  async function reload() {
    const rows = await api.productSupplierLinks(productId);
    setLinks(rows);
  }

  useEffect(() => {
    reload();
  }, [productId]);

  useEffect(() => {
    if (addOpen) {
      api.listSuppliers().then(setSuppliers);
      setForm(EMPTY_FORM);
    }
  }, [addOpen]);

  async function submit() {
    if (!form.supplier_id) return;
    await api.addProductSupplierLink(productId, {
      supplier_id: Number(form.supplier_id),
      supplier_sku: form.supplier_sku || null,
      last_unit_cost: form.last_unit_cost ? Number(form.last_unit_cost) : null,
      lead_time_days: form.lead_time_days ? Number(form.lead_time_days) : null,
      is_preferred: form.is_preferred,
    });
    setAddOpen(false);
    reload();
  }

  async function remove(supplierId: number) {
    if (!confirm("Tedarikçi bağlantısı kaldırılsın mı?")) return;
    await api.removeProductSupplierLink(productId, supplierId);
    reload();
  }

  return (
    <section className="bg-white border border-slate-200 rounded-lg p-5">
      <header className="flex items-center justify-between mb-3">
        <h2 className="font-semibold">Tedarikçiler</h2>
        <button
          onClick={() => setAddOpen(true)}
          className="text-sm inline-flex items-center gap-1 text-brand-700 hover:underline"
        >
          <Plus className="h-3.5 w-3.5" /> Bağla
        </button>
      </header>

      {links.length === 0 ? (
        <p className="text-sm text-slate-500">Bağlı tedarikçi yok.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {links.map((l) => (
            <li
              key={l.id}
              className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-0"
            >
              <div>
                <Link
                  href={`/suppliers/${l.supplier_id}`}
                  className="font-medium text-brand-700 hover:underline"
                >
                  {l.supplier_name}
                </Link>
                {l.is_preferred && (
                  <Star className="h-3 w-3 inline ml-1.5 text-amber-500 fill-amber-500" />
                )}
                <p className="text-xs text-slate-500">
                  SKU: {l.supplier_sku ?? "—"} · Son alış:{" "}
                  {l.last_unit_cost != null
                    ? formatTRY(l.last_unit_cost)
                    : "—"}{" "}
                  {l.last_purchase_at && `(${formatDateTime(l.last_purchase_at)})`}
                  {l.lead_time_days != null && ` · ${l.lead_time_days}g`}
                </p>
              </div>
              <button
                onClick={() => remove(l.supplier_id)}
                className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                aria-label="Bağı kaldır"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        title="Tedarikçi Bağla"
        size="sm"
      >
        <label className="block text-xs text-slate-600 mb-1">Tedarikçi</label>
        <select
          value={form.supplier_id}
          onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
          className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
        >
          <option value="">— Seç —</option>
          {suppliers.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>

        <label className="block text-xs text-slate-600 mb-1">Tedarikçi SKU</label>
        <input
          value={form.supplier_sku}
          onChange={(e) => setForm({ ...form, supplier_sku: e.target.value })}
          className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
        />

        <label className="block text-xs text-slate-600 mb-1">
          Son birim maliyet (TL)
        </label>
        <input
          type="number"
          value={form.last_unit_cost}
          onChange={(e) =>
            setForm({ ...form, last_unit_cost: e.target.value })
          }
          className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
        />

        <label className="block text-xs text-slate-600 mb-1">
          Tedarik süresi (gün)
        </label>
        <input
          type="number"
          value={form.lead_time_days}
          onChange={(e) =>
            setForm({ ...form, lead_time_days: e.target.value })
          }
          className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3"
        />

        <label className="inline-flex items-center text-sm">
          <input
            type="checkbox"
            checked={form.is_preferred}
            onChange={(e) =>
              setForm({ ...form, is_preferred: e.target.checked })
            }
            className="mr-2"
          />
          Birincil tedarikçi yap
        </label>

        <footer className="mt-4 flex justify-end gap-2">
          <button
            onClick={() => setAddOpen(false)}
            className="px-3 py-1.5 text-sm rounded border border-slate-300"
          >
            Vazgeç
          </button>
          <button
            onClick={submit}
            disabled={!form.supplier_id}
            className="px-3 py-1.5 text-sm rounded bg-brand-600 text-white disabled:opacity-50"
          >
            Bağla
          </button>
        </footer>
      </Modal>
    </section>
  );
}
