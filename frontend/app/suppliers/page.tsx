"use client";

import { Plus, Trash2, Users } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { SupplierFormModal } from "@/components/suppliers/SupplierFormModal";
import { api } from "@/lib/api";

interface Supplier {
  id: number;
  name: string;
  contact_name: string | null;
  phone: string | null;
  linked_product_count: number;
}

export default function SuppliersPage() {
  const [rows, setRows] = useState<Supplier[]>([]);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);

  async function reload() {
    setRows(await api.listSuppliers(search || undefined));
  }

  useEffect(() => {
    reload();
  }, [search]);

  async function remove(s: Supplier) {
    if (!confirm(`"${s.name}" silinsin mi?`)) return;
    await api.deleteSupplier(s.id);
    reload();
  }

  return (
    <div className="max-w-5xl space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tedarikçiler</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            İletişim, tedarik süresi ve bağlı ürünler.
          </p>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> Yeni Tedarikçi
        </button>
      </header>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Ad / iletişim / telefon ara..."
        className="w-full max-w-sm border border-slate-300 rounded px-3 py-1.5 text-sm"
      />

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ad</th>
            <th className="text-left px-4 py-2">İletişim</th>
            <th className="text-left px-4 py-2">Telefon</th>
            <th className="text-right px-4 py-2">Bağlı Ürün</th>
            <th className="text-right px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="text-center text-slate-500 py-8">
                <Users className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                Tedarikçi yok.
              </td>
            </tr>
          )}
          {rows.map((s) => (
            <tr
              key={s.id}
              className="border-t border-slate-100 hover:bg-slate-50"
            >
              <td className="px-4 py-2">
                <Link
                  href={`/suppliers/${s.id}`}
                  className="text-brand-700 hover:underline font-medium"
                >
                  {s.name}
                </Link>
              </td>
              <td className="px-4 py-2 text-slate-600">
                {s.contact_name ?? "—"}
              </td>
              <td className="px-4 py-2 text-slate-600">{s.phone ?? "—"}</td>
              <td className="px-4 py-2 text-right">
                {s.linked_product_count}
              </td>
              <td className="px-4 py-2 text-right">
                <button
                  onClick={() => remove(s)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                  aria-label="Sil"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {open && (
        <SupplierFormModal
          open
          mode="create"
          onClose={() => setOpen(false)}
          onSaved={reload}
        />
      )}
    </div>
  );
}
