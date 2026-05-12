export function formatTRY(amount: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(input: string | Date | null | undefined): string {
  if (!input) return "—";
  const d = typeof input === "string" ? new Date(input) : input;
  return new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium" }).format(d);
}

export function formatDateTime(input: string | Date | null | undefined): string {
  if (!input) return "—";
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
    pending: "bg-amber-100 text-amber-800",
    prepared: "bg-blue-100 text-blue-800",
    shipped: "bg-indigo-100 text-indigo-800",
    delivered: "bg-emerald-100 text-emerald-800",
    cancelled: "bg-rose-100 text-rose-800",
  };
  return map[status] ?? "bg-slate-100 text-slate-800";
}
