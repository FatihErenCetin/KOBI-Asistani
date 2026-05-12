import { statusColor, statusLabel } from "@/lib/format";

export function OrderStatusBadge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor(status)}`}>
      {statusLabel(status)}
    </span>
  );
}
