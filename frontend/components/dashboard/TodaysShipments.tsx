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
    <section className="bg-white border border-slate-200 rounded-lg p-5">
      <h2 className="font-semibold mb-3">Bugün Teslim Edilecekler</h2>
      {rows.length === 0 && <p className="text-sm text-slate-500">Bugün için kargo yok.</p>}
      <ul className="space-y-3">
        {rows.map((s) => (
          <li key={s.tracking_no} className="text-sm flex flex-col gap-1">
            <div className="flex justify-between">
              <span className="font-medium">#{s.order_id} • {s.customer_name}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${statusColor(s.status)}`}>
                {statusLabel(s.status)}
              </span>
            </div>
            <div className="text-slate-500">
              {s.current_location ?? "—"} • ETA {formatDate(s.eta)}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
