interface Row {
  id: number;
  name: string;
  stock: number;
  low_stock_threshold: number;
  unit: string;
}

export function LowStockList({ rows }: { rows: Row[] }) {
  return (
    <section className="surface-card overflow-hidden">
      <header className="border-b border-slate-100 px-5 py-4">
        <h2 className="section-title">Düşük Stok</h2>
        <p className="section-subtitle mt-1">Eşik altına düşen ürünler</p>
      </header>
      {rows.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm font-medium text-slate-400">Tüm stoklar yeterli.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {rows.map((p) => {
            const pct = Math.min(100, Math.round((p.stock / Math.max(1, p.low_stock_threshold)) * 100));
            return (
              <li key={p.id} className="px-5 py-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-bold text-slate-950">{p.name}</span>
                  <span className="font-extrabold text-rose-700">{p.stock} {p.unit}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-rose-100">
                  <div className="h-full rounded-full bg-rose-500" style={{ width: `${Math.max(8, pct)}%` }} />
                </div>
                <p className="mt-1 text-xs font-medium text-slate-400">Eşik: {p.low_stock_threshold}</p>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
