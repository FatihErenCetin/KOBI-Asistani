"use client";

function daysText(value: number | null | undefined) {
  if (value === null || value === undefined) return "Satış hızı yok";
  if (value < 1) return "1 günden az";
  return `${value} gün`;
}

export function StockOverviewRender({ data }: { data: any }) {
  const products = data?.products ?? [];
  if (!Array.isArray(products) || products.length === 0) return null;

  return (
    <ul className="overflow-hidden rounded-2xl border border-slate-200 bg-white text-sm">
      {products.map((p: any) => {
        const ratio = Math.min(100, Math.round((Number(p.stock ?? 0) / Math.max(1, Number(p.low_stock_threshold ?? 1))) * 100));
        return (
          <li key={p.id} className="border-b border-slate-100 px-4 py-3 last:border-0">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="font-bold text-slate-950">{p.name}</span>
                <div className="mt-1 flex flex-wrap gap-2 text-[11px] font-semibold text-slate-500">
                  <span>Eşik: {p.low_stock_threshold} {p.unit}</span>
                  <span>14 gün satış: {p.sold_last_14_days ?? 0} {p.unit}</span>
                  <span>Tahmini kalan: {daysText(p.estimated_days_left)}</span>
                </div>
              </div>
              <span className={p.is_low ? "font-extrabold text-rose-700" : "font-extrabold text-brand-700"}>
                {p.stock} {p.unit}
              </span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div className={p.is_low ? "h-full rounded-full bg-rose-500" : "h-full rounded-full bg-brand-500"} style={{ width: `${Math.max(8, ratio)}%` }} />
            </div>
            {p.is_low && (
              <p className="mt-2 rounded-xl bg-amber-50 px-3 py-2 text-xs font-bold text-amber-800">
                Öneri: yaklaşık {p.suggested_reorder_qty ?? p.low_stock_threshold} {p.unit} tedarik planla.
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
