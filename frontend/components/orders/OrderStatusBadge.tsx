import { statusColor, statusLabel } from "@/lib/format";

export function OrderStatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${statusColor(status)}`}>
      {statusLabel(status)}
    </span>
  );
}
