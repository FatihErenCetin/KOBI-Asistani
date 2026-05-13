import { AlertTriangle, BarChart3, ShieldCheck, Truck } from "lucide-react";

import { api } from "@/lib/api";

async function getCarrierData() {
  try {
    return await api.carrierPerformance(30);
  } catch {
    return null;
  }
}

function RiskBadge({ score }: { score: number }) {
  if (score > 30) return <span className="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-700">Yüksek</span>;
  if (score > 10) return <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-700">Orta</span>;
  return <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-700">Düşük</span>;
}

export default async function CarrierPage() {
  const data = await getCarrierData();
  const carriers: any[] = data?.carriers ?? [];

  return (
    <div className="page-wrap">
      <header className="surface-card overflow-hidden px-7 py-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-sky-50 px-3 py-1.5 text-xs font-bold text-sky-700">
              <Truck className="h-3.5 w-3.5" aria-hidden="true" />
              Kargo performansı
            </div>
            <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-950">Kargo Firma Analizi</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Son 30 günlük teslimat başarısı, gecikme oranı ve şikayet riski.
            </p>
          </div>
          {data?.recommendation && (
            <div className="max-w-lg rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold leading-6 text-amber-900">
              {data.recommendation}
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="surface-card p-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Toplam kargo</p>
            <Truck className="h-5 w-5 text-slate-300" />
          </div>
          <p className="mt-3 text-3xl font-extrabold text-slate-950 tabular-nums">{data?.total_shipments ?? "-"}</p>
        </div>
        <div className="surface-card p-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Toplam geciken</p>
            <AlertTriangle className="h-5 w-5 text-rose-400" />
          </div>
          <p className="mt-3 text-3xl font-extrabold text-rose-600 tabular-nums">{data?.total_delayed ?? "-"}</p>
        </div>
        <div className="surface-card p-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Gecikme oranı</p>
            <BarChart3 className="h-5 w-5 text-slate-300" />
          </div>
          <p className={`mt-3 text-3xl font-extrabold tabular-nums ${(data?.overall_delay_rate_pct ?? 0) > 20 ? "text-rose-600" : "text-brand-700"}`}>
            {data ? `%${data.overall_delay_rate_pct}` : "-"}
          </p>
        </div>
      </div>

      <section className="table-shell">
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
          <div>
            <h2 className="section-title">Firma Performansı</h2>
            <p className="section-subtitle mt-1">Teslimat oranı, gecikme ve ortalama teslim süresi</p>
          </div>
          <ShieldCheck className="h-5 w-5 text-brand-500" aria-hidden="true" />
        </div>

        {carriers.length === 0 ? (
          <div className="px-6 py-16 text-center text-sm font-medium text-slate-400">
            {data === null ? "Veri yüklenemedi. Backend veya token ayarını kontrol edin." : "Kargo verisi bulunamadı."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-row">
                  <th className="table-cell text-left">Firma</th>
                  <th className="table-cell text-right">Toplam</th>
                  <th className="table-cell text-right">Teslim</th>
                  <th className="table-cell text-right">Gecikme</th>
                  <th className="table-cell text-right">Ortalama</th>
                  <th className="table-cell text-center">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {carriers.map((c: any) => (
                  <tr key={c.carrier} className="transition hover:bg-slate-50/90">
                    <td className="table-cell font-extrabold text-slate-950">{c.carrier}</td>
                    <td className="table-cell text-right font-semibold text-slate-700 tabular-nums">{c.total_shipments}</td>
                    <td className="table-cell text-right font-extrabold text-brand-700 tabular-nums">%{c.delivery_rate_pct}</td>
                    <td className={`table-cell text-right font-extrabold tabular-nums ${c.delay_rate_pct > 20 ? "text-rose-600" : "text-slate-700"}`}>%{c.delay_rate_pct}</td>
                    <td className="table-cell text-right font-semibold text-slate-600 tabular-nums">{c.avg_delivery_days ?? "-"} gün</td>
                    <td className="table-cell text-center"><RiskBadge score={c.risk_score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {carriers.some((c: any) => c.top_complaint_risks?.length > 0) && (
        <section className="table-shell border-rose-100">
          <div className="border-b border-rose-100 bg-rose-50/70 px-6 py-5">
            <h2 className="font-bold text-rose-950">Şikayet Riski Yüksek Siparişler</h2>
            <p className="mt-1 text-sm font-medium text-rose-600">Teslim tarihi geçmiş ve müşteri memnuniyeti riski oluşmuş kayıtlar</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-row">
                  <th className="table-cell text-left">Sipariş</th>
                  <th className="table-cell text-left">Müşteri</th>
                  <th className="table-cell text-left">Firma</th>
                  <th className="table-cell text-left">Son Konum</th>
                  <th className="table-cell text-right">Gecikme</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {carriers.flatMap((c: any) =>
                  (c.top_complaint_risks ?? []).map((r: any) => (
                    <tr key={`${r.order_id}-${r.tracking}`} className="transition hover:bg-rose-50/60">
                      <td className="table-cell font-mono font-bold text-brand-700">#{r.order_id}</td>
                      <td className="table-cell font-semibold text-slate-950">{r.customer}</td>
                      <td className="table-cell text-slate-600">{c.carrier}</td>
                      <td className="table-cell text-slate-500">{r.location ?? "-"}</td>
                      <td className="table-cell text-right font-extrabold text-rose-700">{r.days_late} gün</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
