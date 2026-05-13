export function formatTRY(amount: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    minimumFractionDigits: 2,
  }).format(amount ?? 0);
}

export function formatDate(input: string | Date | null | undefined): string {
  if (!input) return "-";
  const d = typeof input === "string" ? new Date(input) : input;
  return new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium" }).format(d);
}

export function formatDateTime(input: string | Date | null | undefined): string {
  if (!input) return "-";
  const d = typeof input === "string" ? new Date(input) : input;
  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "Yeni",
    prepared: "Hazırlandı",
    shipped: "Kargoda",
    delivered: "Teslim Edildi",
    cancelled: "İptal",
    label_created: "Etiket Oluşturuldu",
    picked_up: "Teslim Alındı",
    in_transit: "Yolda",
    out_for_delivery: "Dağıtımda",
  };
  return map[status] ?? status;
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    pending: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    prepared: "bg-sky-100 text-sky-800 ring-1 ring-sky-200",
    shipped: "bg-indigo-100 text-indigo-800 ring-1 ring-indigo-200",
    delivered: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
    cancelled: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
    label_created: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
    picked_up: "bg-sky-100 text-sky-800 ring-1 ring-sky-200",
    in_transit: "bg-indigo-100 text-indigo-800 ring-1 ring-indigo-200",
    out_for_delivery: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
  };
  return map[status] ?? "bg-slate-100 text-slate-800 ring-1 ring-slate-200";
}
