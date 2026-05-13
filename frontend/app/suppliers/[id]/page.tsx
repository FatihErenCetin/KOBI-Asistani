"use client";

import { ArrowLeft, Pencil } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { SupplierFormModal } from "@/components/suppliers/SupplierFormModal";
import { api } from "@/lib/api";

export default function SupplierDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = Number(params.id);
  const [s, setS] = useState<any | null>(null);
  const [edit, setEdit] = useState(false);

  async function reload() {
    setS(await api.getSupplier(id));
  }

  useEffect(() => {
    reload();
  }, [id]);

  if (!s) return <div className="p-8 text-slate-500">Yükleniyor…</div>;

  return (
    <div className="max-w-4xl space-y-6">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/suppliers"
            className="p-1.5 rounded hover:bg-slate-100"
            aria-label="Geri"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{s.name}</h1>
            <p className="text-sm text-slate-500">{s.contact_name ?? "—"}</p>
          </div>
        </div>
        <button
          onClick={() => setEdit(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
        >
          <Pencil className="h-4 w-4" /> Düzenle
        </button>
      </header>

      <section className="bg-white border border-slate-200 rounded-lg p-5 grid grid-cols-2 gap-y-2 text-sm">
        <Field label="Telefon" value={s.phone} />
        <Field label="E-posta" value={s.email} />
        <Field label="Adres" value={s.address} colSpan={2} />
        <Field label="Not" value={s.notes} colSpan={2} />
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <h2 className="font-semibold mb-3">
          Bağlı Ürünler ({s.linked_product_count})
        </h2>
        <p className="text-sm text-slate-500">
          Tedarikçi bağlı ürünleri ilgili ürün detay sayfasından yönetilir.
        </p>
      </section>

      {edit && (
        <SupplierFormModal
          open
          mode="edit"
          supplier={s}
          onClose={() => setEdit(false)}
          onSaved={reload}
        />
      )}
    </div>
  );
}

function Field({
  label,
  value,
  colSpan = 1,
}: {
  label: string;
  value: any;
  colSpan?: 1 | 2;
}) {
  return (
    <div className={colSpan === 2 ? "col-span-2" : ""}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium text-slate-700">{value ?? "—"}</p>
    </div>
  );
}
