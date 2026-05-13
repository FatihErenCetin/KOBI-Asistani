import { formatDate, statusColor, statusLabel } from "@/lib/format";

interface Row {
  order_id: number;
  tracking_no: string;
  customer_name: string;
  status: string;
  current_location: string | null;
  eta: string | null;
}

export function TodaysShipments({ rows }: { rows: Row[] }) {
  return (
    <section className="surface-card overflow-hidden">
      <header className="border-b border-slate-100 px-5 py-4">
        <h2 className="section-title">Bugün Teslim Edilecekler</h2>
      </header>
      {rows.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm font-medium text-slate-400">Bugün için kargo yok.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {rows.map((s) => (
            <li key={s.tracking_no} className="px-5 py-4 text-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold text-slate-950">#{s.order_id} · {s.customer_name}</p>
                  <p className="mt-1 text-xs font-medium text-slate-500">{s.current_location ?? "-"} · ETA {formatDate(s.eta)}</p>
                </div>
                <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${statusColor(s.status)}`}>{statusLabel(s.status)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
