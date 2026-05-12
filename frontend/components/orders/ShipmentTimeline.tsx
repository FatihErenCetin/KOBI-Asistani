import { formatDate, statusLabel } from "@/lib/format";

const STAGES = [
  "label_created",
  "picked_up",
  "in_transit",
  "out_for_delivery",
  "delivered",
];

interface Shipment {
  tracking_no: string;
  carrier: string;
  status: string;
  current_location: string | null;
  estimated_delivery: string | null;
}

export function ShipmentTimeline({ shipment }: { shipment: Shipment | null }) {
  if (!shipment) {
    return <p className="text-sm text-slate-500">Bu sipariş için kargo bilgisi yok.</p>;
  }
  const currentIdx = STAGES.indexOf(shipment.status);
  return (
    <div>
      <p className="text-xs text-slate-500 mb-2">
        {shipment.carrier} • <span className="font-mono">{shipment.tracking_no}</span>
      </p>
      <ol className="space-y-2">
        {STAGES.map((stage, idx) => {
          const reached = idx <= currentIdx;
          return (
            <li key={stage} className="flex items-center gap-3 text-sm">
              <span
                className={`h-3 w-3 rounded-full ${reached ? "bg-brand-500" : "bg-slate-300"}`}
              />
              <span className={reached ? "" : "text-slate-400"}>{statusLabel(stage)}</span>
            </li>
          );
        })}
      </ol>
      <p className="text-sm mt-3">
        Konum: <span className="font-medium">{shipment.current_location ?? "—"}</span>
      </p>
      <p className="text-sm">ETA: {formatDate(shipment.estimated_delivery)}</p>
    </div>
  );
}
