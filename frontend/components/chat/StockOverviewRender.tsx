"use client";

export function StockOverviewRender({ data }: { data: any }) {
  const products = data?.products ?? [];
  if (!Array.isArray(products) || products.length === 0) return null;
  return (
    <ul className="bg-white border border-slate-200 rounded mt-2 divide-y divide-slate-100 text-sm">
      {products.map((p: any) => (
        <li key={p.id} className="flex justify-between px-3 py-2">
          <span>{p.name}</span>
          <span>
            <span className={p.is_low ? "text-rose-700 font-semibold" : ""}>
              {p.stock} {p.unit}
            </span>
            {p.is_low && <span className="ml-2 text-xs text-rose-500">⚠️ düşük</span>}
          </span>
        </li>
      ))}
    </ul>
  );
}
