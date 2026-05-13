"use client";

import { AlertTriangle, Calendar, Database, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface ExpiringLot {
  lot_id: number;
  product_id: number;
  product_name: string;
  lot_number: string;
  expiry_date: string;
  days_left: number;
  quantity: number;
}

export default function ExpiringPage() {
  const [rows, setRows] = useState<ExpiringLot[]>([]);
  const [days, setDays] = useState(14);
  const [enriching, setEnriching] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState<string | null>(null);

  async function reload() {
    setRows(await api.expiringLots(days));
  }

  useEffect(() => {
    reload();
  }, [days]);

  async function loadDemoData() {
    if (
      !confirm(
        "Demo verilerini yükle?\n\n" +
          "Eksik depolar, çoklu depo dağılımı ve SKT'li lotlar idempotent olarak eklenir. " +
          "Mevcut veriler korunur, bu işlem güvenle birden fazla kez çalıştırılabilir.",
      )
    )
      return;
    setEnriching(true);
    setEnrichMsg(null);
    try {
      const r = await api.enrichDemoData();
      const parts: string[] = [];
      if (r.warehouses_created)
        parts.push(`${r.warehouses_created} yeni depo`);
      if (r.products_split)
        parts.push(`${r.products_split} ürün çoklu depoya dağıtıldı`);
      if (r.lots_created) parts.push(`${r.lots_created} lot oluşturuldu`);
      setEnrichMsg(
        parts.length === 0
          ? "✓ Tüm demo verileri zaten yüklü."
          : `✓ ${parts.join(", ")}.`,
      );
      reload();
    } catch (e: any) {
      setEnrichMsg(`Hata: ${e?.message ?? "yükleme başarısız"}`);
    } finally {
      setEnriching(false);
    }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <Calendar className="h-6 w-6 text-amber-500" />
            Yaklaşan Son Kullanma
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Önümüzdeki günlerde son kullanma tarihi gelecek lot'lar.
          </p>
        </div>
        <div className="flex gap-2 items-center flex-wrap">
          {[7, 14, 30, 60].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded border ${
                days === d
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white border-slate-300"
              }`}
            >
              {d} gün
            </button>
          ))}
          <button
            onClick={loadDemoData}
            disabled={enriching}
            className="ml-1 inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded border border-violet-300 text-violet-700 hover:bg-violet-50 disabled:opacity-50"
            title="Eksik demo verisini yükle (depolar, lot'lar, dağılım)"
          >
            {enriching ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Database className="h-3.5 w-3.5" />
            )}
            Demo Veriyi Yükle
          </button>
        </div>
      </header>

      {enrichMsg && (
        <p className="text-sm bg-violet-50 border border-violet-200 text-violet-800 rounded px-3 py-2">
          {enrichMsg}
        </p>
      )}

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ürün</th>
            <th className="text-left px-4 py-2">Lot No</th>
            <th className="text-right px-4 py-2">Miktar</th>
            <th className="text-left px-4 py-2">SKT</th>
            <th className="text-right px-4 py-2">Kalan Gün</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="text-center py-10">
                <div className="flex flex-col items-center gap-3 text-slate-500">
                  <Calendar className="h-10 w-10 text-slate-300" />
                  <p>Bu aralıkta süresi yaklaşan lot yok.</p>
                  <p className="text-xs">
                    Henüz hiç ürün lot kaydı oluşturmadıysanız, üst kısımdaki{" "}
                    <strong>"Demo Veriyi Yükle"</strong> butonuyla örnek
                    SKT'li lotlar oluşturabilirsiniz.
                  </p>
                </div>
              </td>
            </tr>
          )}
          {rows.map((r) => (
            <tr
              key={r.lot_id}
              className={`border-t border-slate-100 ${
                r.days_left <= 3 ? "bg-rose-50" : r.days_left <= 7 ? "bg-amber-50" : ""
              }`}
            >
              <td className="px-4 py-2">
                <Link
                  href={`/products/${r.product_id}`}
                  className="text-brand-700 hover:underline font-medium"
                >
                  {r.product_name}
                </Link>
              </td>
              <td className="px-4 py-2 text-slate-600">{r.lot_number}</td>
              <td className="px-4 py-2 text-right">{r.quantity}</td>
              <td className="px-4 py-2 text-slate-600">{r.expiry_date}</td>
              <td className="px-4 py-2 text-right">
                <span
                  className={`inline-flex items-center gap-1 font-medium ${
                    r.days_left <= 3
                      ? "text-rose-700"
                      : r.days_left <= 7
                        ? "text-amber-700"
                        : "text-slate-700"
                  }`}
                >
                  {r.days_left <= 7 && <AlertTriangle className="h-3 w-3" />}
                  {r.days_left} gün
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
