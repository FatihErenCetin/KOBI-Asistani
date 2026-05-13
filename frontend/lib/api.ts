const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN = process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? "";

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${TOKEN}`,
      ...(init.headers ?? {}),
    },
  });
  if (!r.ok) {
    const body = await r.text().catch(() => "");
    throw new Error(`API ${r.status}: ${body}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  dashboardToday: () => request<any>("/dashboard/today"),
  listOrders: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(params as any).toString();
    return request<any[]>(`/orders${qs ? `?${qs}` : ""}`);
  },
  getOrder: (id: number) => request<any>(`/orders/${id}`),
  patchOrderStatus: (id: number, status: string) =>
    request<any>(`/orders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  listProducts: (params: { search?: string; low_stock_only?: boolean } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).reduce<Record<string, string>>((acc, [k, v]) => {
        if (v !== undefined && v !== null) acc[k] = String(v);
        return acc;
      }, {}),
    ).toString();
    return request<any[]>(`/products${qs ? `?${qs}` : ""}`);
  },
  listCustomers: (search?: string) =>
    request<any[]>(`/customers${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  customerOrders: (id: number) => request<any[]>(`/customers/${id}/orders`),

  carrierPerformance: (sinceDays = 30) =>
    request<any>(`/carriers/performance?since_days=${sinceDays}`),
  carrierRisks: () => request<any>("/carriers/risks"),
  panelChat: (message: string, history?: any[]) =>
    request<{ text: string; data: any | null }>("/panel/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),
  sendSupplierMail: (payload: { subject: string; body: string }) =>
    request<{ ok: boolean; to: string; subject: string; message_id?: string }>("/panel/supplier-mail", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
