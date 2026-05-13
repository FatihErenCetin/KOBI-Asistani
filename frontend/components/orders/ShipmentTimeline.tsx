import type { ComponentType, ReactNode } from "react";
import {
  Package,
  PackageCheck,
  Truck,
  MapPin,
  CheckCircle2,
  Clock,
  PackageOpen,
} from "lucide-react";
import { formatDate, statusLabel } from "@/lib/format";

type ShipmentStatus =
  | "label_created"
  | "picked_up"
  | "in_transit"
  | "out_for_delivery"
  | "delivered";

const STAGES: ShipmentStatus[] = [
  "label_created",
  "picked_up",
  "in_transit",
  "out_for_delivery",
  "delivered",
];

const STAGE_ICONS: Record<ShipmentStatus, ComponentType<{ className?: string }>> = {
  label_created: Package,
  picked_up: PackageCheck,
  in_transit: Truck,
  out_for_delivery: MapPin,
  delivered: CheckCircle2,
};

interface Shipment {
  tracking_no: string;
  carrier: string;
  status: string;
  current_location: string | null;
  estimated_delivery: string | null;
}

export function ShipmentTimeline({ shipment }: { shipment: Shipment | null }) {
  if (!shipment) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/60 p-6 text-center">
        <div className="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-full bg-white ring-1 ring-slate-200">
          <PackageOpen className="h-5 w-5 text-slate-400" aria-hidden="true" />
        </div>
        <p className="mt-3 text-sm font-medium text-slate-700">
          Bu sipariş henüz kargoya verilmedi
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Sipariş durumunu güncellediğinizde kargo bilgisi burada görünür.
        </p>
      </div>
    );
  }

  const currentIdx = Math.max(0, STAGES.indexOf(shipment.status as ShipmentStatus));
  const totalSegments = STAGES.length - 1;
  const progressPct = (currentIdx / totalSegments) * 100;
  const isDelivered = shipment.status === "delivered";

  return (
    <section
      aria-label="Kargo durumu"
      className="rounded-xl border border-slate-200 bg-white p-5"
    >
      {/* Üst satır: carrier + tracking */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-brand-50 text-brand-700">
            <Truck className="h-4 w-4" aria-hidden="true" />
          </span>
          <div className="leading-tight">
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              Kargo
            </p>
            <p className="text-sm font-medium text-slate-800">
              {shipment.carrier}
            </p>
          </div>
        </div>
        <p className="font-mono text-xs text-slate-500 tabular-nums">
          {shipment.tracking_no}
        </p>
      </div>

      {/* Yatay step indicator */}
      <ol
        className="mt-6 grid grid-cols-5 gap-1"
        aria-label="Kargo aşamaları"
      >
        {STAGES.map((stage, idx) => {
          const reached = idx <= currentIdx;
          const isActive = idx === currentIdx && !isDelivered;
          const isDone = idx < currentIdx || isDelivered;
          const Icon = STAGE_ICONS[stage];

          return (
            <li
              key={stage}
              aria-current={isActive ? "step" : undefined}
              className="relative flex flex-col items-center"
            >
              {/* Connector line (sol taraf) */}
              {idx > 0 && (
                <span
                  aria-hidden="true"
                  className={`absolute top-5 right-1/2 h-0.5 w-full ${
                    reached ? "bg-brand-500" : "bg-slate-200"
                  }`}
                />
              )}
              {/* Connector line (sağ taraf) */}
              {idx < STAGES.length - 1 && (
                <span
                  aria-hidden="true"
                  className={`absolute top-5 left-1/2 h-0.5 w-full ${
                    idx < currentIdx ? "bg-brand-500" : "bg-slate-200"
                  }`}
                />
              )}

              {/* Dot / circle */}
              <div className="relative z-10">
                {isActive && (
                  <span
                    aria-hidden="true"
                    className="absolute inset-0 rounded-full bg-brand-500/30 motion-safe:animate-ping"
                  />
                )}
                <span
                  className={`relative inline-flex items-center justify-center rounded-full ring-4 ring-white ${
                    isActive
                      ? "h-10 w-10 bg-brand-500 text-white shadow-sm shadow-brand-500/30"
                      : isDone
                      ? "h-8 w-8 bg-brand-500 text-white"
                      : "h-8 w-8 border border-slate-200 bg-white text-slate-400"
                  }`}
                >
                  <Icon
                    className={isActive ? "h-5 w-5" : "h-4 w-4"}
                    aria-hidden="true"
                  />
                </span>
              </div>

              {/* Label */}
              <span
                className={`mt-2 text-center text-[11px] leading-tight sm:text-xs ${
                  isActive
                    ? "font-semibold text-brand-700"
                    : isDone
                    ? "font-medium text-slate-700"
                    : "text-slate-400"
                }`}
              >
                {statusLabel(stage)}
              </span>
            </li>
          );
        })}
      </ol>

      {/* Progress meta */}
      <p className="mt-4 text-center text-xs text-slate-500 tabular-nums">
        {currentIdx + 1} / {STAGES.length} aşama
        <span className="mx-1.5 text-slate-300">•</span>
        %{Math.round(progressPct)} tamamlandı
      </p>

      {/* Aktif adım altında: konum + ETA, vurgulu kart */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
          <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Mevcut konum</span>
          </div>
          <p className="mt-1.5 text-base font-semibold text-slate-900">
            {shipment.current_location ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
          <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
            <Clock className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{isDelivered ? "Teslim edildi" : "Tahmini teslim"}</span>
          </div>
          <p className="mt-1.5 text-base font-semibold text-slate-900 tabular-nums">
            {formatDate(shipment.estimated_delivery)}
          </p>
        </div>
      </div>
    </section>
  );
}