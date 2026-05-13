"use client";

import { Clock, Copy, Mail, RefreshCw, ShoppingBag, Star } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import { formatTRY } from "@/lib/format";

interface Suggestion {
  product_id: number;
  product_name: string;
  unit: string;
  current_stock: number;
  min_stock: number;
  max_stock: number | null;
  suggested_order_qty: number;
  supplier_id: number | null;
  supplier_name: string | null;
  lead_time_days: number | null;
  last_unit_cost: number | null;
  estimated_cost: number | null;
  days_of_stock: number | null;
  recommended_order_date: string | null;
  urgency: "critical" | "warning" | "info";
}

export default function ReorderPage() {
  const [rows, setRows] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState<any | null>(null);
  const [draftBusy, setDraftBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function openDraft(r: Suggestion) {
    if (!r.supplier_id) return;
    setDraftBusy(true);
    setCopied(false);
    try {
      const d = await api.reorderDraftMail({
        product_id: r.product_id,
        order_qty: r.suggested_order_qty,
        supplier_id: r.supplier_id,
      });
      setDraft({ ...d, product_name: r.product_name });
    } catch (e: any) {
      alert(e?.message ?? "Hata");
    } finally {
      setDraftBusy(false);
    }
  }

  async function copyDraft() {
    if (!draft) return;
    try {
      await navigator.clipboard.writeText(
        `Konu: ${draft.subject}\n\n${draft.body}`,
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // graceful
    }
  }

  async function reload() {
    setLoading(true);
    try {
      setRows(await api.reorderSuggestions());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  return (
    <div className="max-w-6xl space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <ShoppingBag className="h-6 w-6 text-brand-600" />
            Sipariş Önerileri
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Stoğu min seviyesinin altına düşen ürünler ve birincil tedarikçi.
          </p>
        </div>
        <button
          onClick={reload}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded border border-slate-300 hover:bg-slate-50"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Yenile
        </button>
      </header>

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ürün</th>
            <th className="text-right px-4 py-2">Mevcut</th>
            <th className="text-right px-4 py-2">Min</th>
            <th className="text-right px-4 py-2">Sipariş</th>
            <th className="text-left px-4 py-2">Tedarikçi</th>
            <th className="text-right px-4 py-2">Lead Time</th>
            <th className="text-right px-4 py-2">Tahmini Maliyet</th>
            <th className="text-left px-4 py-2">Tavsiye Tarih</th>
            <th className="text-right px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td colSpan={7} className="text-center text-slate-500 py-8">
                Yükleniyor…
              </td>
            </tr>
          )}
          {!loading && rows.length === 0 && (
            <tr>
              <td colSpan={7} className="text-center text-emerald-600 py-8">
                ✓ Tüm ürünler yeterli stoğa sahip.
              </td>
            </tr>
          )}
          {!loading &&
            rows.map((r) => (
              <tr
                key={r.product_id}
                className={`border-t border-slate-100 ${
                  r.urgency === "critical"
                    ? "bg-rose-50"
                    : r.urgency === "warning"
                      ? "bg-amber-50"
                      : ""
                }`}
              >
                <td className="px-4 py-2">
                  <Link
                    href={`/products/${r.product_id}`}
                    className="text-brand-700 hover:underline font-medium"
                  >
                    {r.product_name}
                  </Link>
                  <span className="text-xs text-slate-500 ml-1">({r.unit})</span>
                </td>
                <td className="px-4 py-2 text-right font-medium">
                  {r.current_stock}
                </td>
                <td className="px-4 py-2 text-right text-slate-500">
                  {r.min_stock}
                </td>
                <td className="px-4 py-2 text-right font-medium text-amber-700">
                  +{r.suggested_order_qty}
                </td>
                <td className="px-4 py-2">
                  {r.supplier_name ? (
                    <Link
                      href={`/suppliers/${r.supplier_id}`}
                      className="text-brand-700 hover:underline inline-flex items-center gap-1"
                    >
                      <Star className="h-3 w-3 text-amber-500 fill-amber-500" />
                      {r.supplier_name}
                    </Link>
                  ) : (
                    <span className="text-slate-400">— bağlı tedarikçi yok</span>
                  )}
                </td>
                <td className="px-4 py-2 text-right text-slate-600">
                  {r.lead_time_days != null ? (
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {r.lead_time_days}g
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-2 text-right">
                  {r.estimated_cost != null ? formatTRY(r.estimated_cost) : "—"}
                </td>
                <td className="px-4 py-2 text-xs">
                  {r.recommended_order_date ? (
                    <span
                      className={`px-1.5 py-0.5 rounded ${
                        r.urgency === "critical"
                          ? "bg-rose-100 text-rose-700 font-medium"
                          : r.urgency === "warning"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {r.urgency === "critical"
                        ? "Acil bugün"
                        : r.recommended_order_date}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-2 text-right">
                  {r.supplier_id && (
                    <button
                      onClick={() => openDraft(r)}
                      disabled={draftBusy}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded border border-slate-300 hover:bg-slate-50"
                    >
                      <Mail className="h-3 w-3" /> Mail Taslağı
                    </button>
                  )}
                </td>
              </tr>
            ))}
        </tbody>
      </table>

      <Modal
        open={draft !== null}
        onClose={() => setDraft(null)}
        title={`Mail Taslağı: ${draft?.product_name ?? ""}`}
        size="lg"
      >
        <div className="space-y-3">
          {draft?.supplier_email && (
            <p className="text-xs text-slate-500">
              Tedarikçi:{" "}
              <span className="font-mono">{draft.supplier_email}</span>
              {draft.supplier_phone && (
                <span> · Telefon: {draft.supplier_phone}</span>
              )}
            </p>
          )}
          <div>
            <label className="block text-xs text-slate-600 mb-1">Konu</label>
            <input
              readOnly
              value={draft?.subject ?? ""}
              className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-slate-50"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">Mesaj</label>
            <textarea
              readOnly
              value={draft?.body ?? ""}
              rows={12}
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm font-mono bg-slate-50"
            />
          </div>
        </div>
        <footer className="mt-4 flex justify-end gap-2">
          <button
            onClick={copyDraft}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
          >
            <Copy className="h-3.5 w-3.5" />
            {copied ? "Kopyalandı ✓" : "Kopyala"}
          </button>
          <button
            onClick={() => setDraft(null)}
            className="px-3 py-1.5 text-sm rounded border border-slate-300"
          >
            Kapat
          </button>
        </footer>
      </Modal>
    </div>
  );
}
