"use client";

import { ArrowLeft, Pencil, Star } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { SupplierFormModal } from "@/components/suppliers/SupplierFormModal";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

interface LinkedProduct {
  product_id: number;
  product_name: string;
  product_unit: string;
  supplier_sku: string | null;
  last_unit_cost: number | null;
  last_purchase_at: string | null;
  lead_time_days: number | null;
  is_preferred: boolean;
}

export default function SupplierDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = Number(params.id);
  const [s, setS] = useState<any | null>(null);
  const [products, setProducts] = useState<LinkedProduct[]>([]);
  const [edit, setEdit] = useState(false);

  async function reload() {
    const [supplier, linked] = await Promise.all([
      api.getSupplier(id),
      api.supplierProducts(id),
    ]);
    setS(supplier);
    setProducts(linked);
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

      <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <header className="px-5 py-3 border-b border-slate-200">
          <h2 className="font-semibold">
            Bağlı Ürünler ({products.length})
          </h2>
        </header>
        {products.length === 0 ? (
          <p className="text-sm text-slate-500 p-5">
            Bu tedarikçiye bağlı ürün yok. Bağlamak için bir ürünün detay sayfasındaki
            “Tedarikçiler” bölümünü kullanın.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-600">
              <tr>
                <th className="text-left px-4 py-2">Ürün</th>
                <th className="text-left px-4 py-2">SKU</th>
                <th className="text-right px-4 py-2">Son Maliyet</th>
                <th className="text-left px-4 py-2">Son Alış</th>
                <th className="text-right px-4 py-2">Lead Time</th>
                <th className="text-center px-4 py-2">Birincil</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr
                  key={p.product_id}
                  className="border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-4 py-2">
                    <Link
                      href={`/products/${p.product_id}`}
                      className="text-brand-700 hover:underline font-medium"
                    >
                      {p.product_name}
                    </Link>
                    <span className="text-xs text-slate-500 ml-1">
                      ({p.product_unit})
                    </span>
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {p.supplier_sku ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {p.last_unit_cost != null ? formatTRY(p.last_unit_cost) : "—"}
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500">
                    {p.last_purchase_at ? formatDateTime(p.last_purchase_at) : "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {p.lead_time_days != null ? `${p.lead_time_days} gün` : "—"}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {p.is_preferred && (
                      <Star className="h-3.5 w-3.5 inline text-amber-500 fill-amber-500" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
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
