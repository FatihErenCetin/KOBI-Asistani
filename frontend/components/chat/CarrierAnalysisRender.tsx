"use client";

import { formatDate } from "@/lib/format";

export function CarrierAnalysisRender({ data }: { data: any }) {
  const carriers = data?.carriers ?? [];
  const risks = data?.orders ?? [];

  if (data?.type === "carrier_risks") {
    if (!Array.isArray(risks) || risks.length === 0) {
      return <p className="rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-slate-500">Riskli kargo kaydı bulunmadı.</p>;
    }

    return (
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
              <th className="px-3 py-2 text-left">Sipariş</th>
              <th className="px-3 py-2 text-left">Müşteri</th>
              <th className="px-3 py-2 text-left">Firma</th>
              <th className="px-3 py-2 text-left">Söz verilen</th>
              <th className="px-3 py-2 text-right">Gecikme</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {risks.map((r: any) => (
              <tr key={`${r.order_id}-${r.tracking}`} className="transition hover:bg-slate-50">
                <td className="px-3 py-2.5 font-mono font-bold text-brand-700">#{r.order_id}</td>
                <td className="px-3 py-2.5 font-semibold text-slate-950">{r.customer}</td>
                <td className="px-3 py-2.5 text-slate-600">{r.carrier}</td>
                <td className="px-3 py-2.5 text-slate-500">{formatDate(r.promised)}</td>
                <td className="px-3 py-2.5 text-right font-extrabold text-rose-700">{r.days_late} gün</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (!Array.isArray(carriers) || carriers.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-slate-50 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">
            <th className="px-3 py-2 text-left">Firma</th>
            <th className="px-3 py-2 text-right">Toplam</th>
            <th className="px-3 py-2 text-right">Teslim</th>
            <th className="px-3 py-2 text-right">Gecikme</th>
            <th className="px-3 py-2 text-right">Ortalama</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {carriers.map((c: any) => (
            <tr key={c.carrier} className="transition hover:bg-slate-50">
              <td className="px-3 py-2.5 font-bold text-slate-950">{c.carrier}</td>
              <td className="px-3 py-2.5 text-right font-semibold text-slate-700">{c.total_shipments}</td>
              <td className="px-3 py-2.5 text-right font-extrabold text-brand-700">%{c.delivery_rate_pct}</td>
              <td className="px-3 py-2.5 text-right font-extrabold text-rose-600">%{c.delay_rate_pct}</td>
              <td className="px-3 py-2.5 text-right font-semibold text-slate-600">{c.avg_delivery_days ?? "-"} gün</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
