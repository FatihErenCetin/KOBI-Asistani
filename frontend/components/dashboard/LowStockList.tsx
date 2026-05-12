interface Row {
  id: number;
  name: string;
  stock: number;
  low_stock_threshold: number;
  unit: string;
}

export function LowStockList({ rows }: { rows: Row[] }) {
  return (
    <section className="bg-white border border-slate-200 rounded-lg p-5">
      <h2 className="font-semibold mb-3">Düşük Stok</h2>
      {rows.length === 0 && <p className="text-sm text-slate-500">Tüm stoklar yeterli.</p>}
      <ul className="space-y-2">
        {rows.map((p) => (
          <li key={p.id} className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-0">
            <span>{p.name}</span>
            <span className="text-sm">
              <span className="font-semibold text-rose-700">{p.stock} {p.unit}</span>
              <span className="text-slate-400"> / eşik {p.low_stock_threshold}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
