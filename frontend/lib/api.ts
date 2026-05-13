import { clearAuth } from "@/lib/auth";

const BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const FALLBACK_TOKEN = process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? "";
const TOKEN_KEY = "kobi-auth-token";

/**
 * Runtime-resolved bearer token.
 * - Client (browser): prefer user's JWT from localStorage, fallback to ADMIN_TOKEN.
 * - Server (RSC/SSR): always ADMIN_TOKEN (backend accepts both — hybrid auth).
 */
function getAuthToken(): string {
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem(TOKEN_KEY);
      if (stored) return stored;
    } catch {
      /* fall through */
    }
  }
  return FALLBACK_TOKEN;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAuthToken();

  const r = await fetch(`${BASE}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (r.status === 401) {
    if (typeof window !== "undefined") {
      clearAuth();
      // Avoid redirect loop from the login page itself
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    throw new Error("Oturum sona erdi");
  }

  if (!r.ok) {
    const body = await r.text().catch(() => "");
    throw new Error(`API ${r.status}: ${body}`);
  }

  return r.json() as Promise<T>;
}

/* -------------------------------------------------------------------------- */
/*  Public API                                                                 */
/* -------------------------------------------------------------------------- */

function qs(params?: Record<string, string | number | boolean | undefined>): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== "" && v !== null,
  );
  if (entries.length === 0) return "";
  return (
    "?" +
    new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
  );
}

export const api = {
  // Dashboard
  dashboardToday: () => request<any>("/dashboard/today"),

  // Orders
  listOrders: (params?: Record<string, string | number | undefined>) =>
    request<any[]>(`/orders${qs(params)}`),
  getOrder: (id: number) => request<any>(`/orders/${id}`),
  patchOrderStatus: (id: number, status: string) =>
    request<any>(`/orders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  // Products — list, get, create, update, soft-delete
  listProducts: (params?: {
    search?: string;
    low_stock_only?: boolean;
    include_inactive?: boolean;
  }) => request<any[]>(`/products${qs(params)}`),
  getProduct: (id: number) => request<any>(`/products/${id}`),
  createProduct: (data: Record<string, any>) =>
    request<any>("/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (id: number, data: Record<string, any>) =>
    request<any>(`/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteProduct: (id: number) =>
    request<void>(`/products/${id}`, { method: "DELETE" }),

  // Bulk operations
  exportProductsCsvUrl: () => `${BASE}/products/export.csv`,
  importProductsCsv: async (file: File): Promise<any> => {
    const token = getAuthToken();
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch(`${BASE}/products/import.csv`, {
      method: "POST",
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: fd,
    });
    if (!r.ok) {
      const t = await r.text().catch(() => "");
      throw new Error(`API ${r.status}: ${t}`);
    }
    return r.json();
  },
  bulkPriceUpdate: (data: {
    product_ids?: number[];
    category?: string;
    name_pattern?: string;
    operation: "percent_increase" | "percent_decrease" | "set_absolute";
    value: number;
    target?: "price" | "cost";
    reason: string;
  }) =>
    request<{ updated: number }>("/products/bulk-price", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Stock movements
  adjustStock: (
    id: number,
    data: { delta: number; reason: string; note?: string },
  ) =>
    request<any>(`/products/${id}/stock-movements`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  stockMovements: (id: number) =>
    request<any[]>(`/products/${id}/movements`),

  // Price history + analytics + sparkline
  priceHistory: (id: number) => request<any[]>(`/products/${id}/price-history`),
  productAnalytics: (id: number) => request<any>(`/products/${id}/analytics`),
  productSparkline: (id: number, days = 7) =>
    request<any[]>(`/products/${id}/sparkline?days=${days}`),
  productSparklinesBulk: (ids: number[], days = 7) =>
    request<Record<number, { day: string; units: number }[]>>(
      `/products/sparklines?ids=${ids.join(",")}&days=${days}`,
    ),

  // Product-supplier links
  productSupplierLinks: (id: number) =>
    request<any[]>(`/products/${id}/suppliers`),
  addProductSupplierLink: (productId: number, data: Record<string, any>) =>
    request<any>(`/products/${productId}/suppliers`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateProductSupplierLink: (
    productId: number,
    supplierId: number,
    data: Record<string, any>,
  ) =>
    request<any>(`/products/${productId}/suppliers/${supplierId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  removeProductSupplierLink: (productId: number, supplierId: number) =>
    request<void>(`/products/${productId}/suppliers/${supplierId}`, {
      method: "DELETE",
    }),

  // Warehouses
  listWarehouses: (search?: string, include_inactive?: boolean) =>
    request<any[]>(`/warehouses${qs({ search, include_inactive })}`),
  getWarehouse: (id: number) => request<any>(`/warehouses/${id}`),
  createWarehouse: (data: Record<string, any>) =>
    request<any>("/warehouses", { method: "POST", body: JSON.stringify(data) }),
  updateWarehouse: (id: number, data: Record<string, any>) =>
    request<any>(`/warehouses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteWarehouse: (id: number) =>
    request<void>(`/warehouses/${id}`, { method: "DELETE" }),
  productWarehouseBreakdown: (id: number) =>
    request<{ warehouse_id: number; warehouse_name: string; quantity: number }[]>(
      `/products/${id}/warehouses`,
    ),

  // Stock lots
  productLots: (id: number, warehouse_id?: number) => {
    const q = warehouse_id ? `?warehouse_id=${warehouse_id}` : "";
    return request<any[]>(`/products/${id}/lots${q}`);
  },
  createProductLot: (id: number, data: any) =>
    request<any>(`/products/${id}/lots`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  expiringLots: (within_days = 14) =>
    request<any[]>(`/products/expiring?within_days=${within_days}`),

  // Complaints
  listComplaints: () => request<any[]>("/complaints"),
  resolveComplaint: (id: number) =>
    request<any>(`/complaints/${id}/resolve`, { method: "POST" }),
  scanComplaints: () =>
    request<{
      shipment_delay: number;
      slow_shipment: number;
      stale_pending: number;
      repeat_complainer: number;
      dormant_customer: number;
      total: number;
    }>("/complaints/scan", { method: "POST" }),

  // Admin tools
  enrichDemoData: () =>
    request<{
      warehouses_created: number;
      lots_created: number;
      products_split: number;
    }>("/admin/enrich-demo-data", { method: "POST" }),

  // Lot actions (AI advisor)
  analyzeExpiringLots: (within_days = 14) =>
    request<{
      lots_analyzed: number;
      actions_created: number;
      lots_skipped: number;
    }>(`/lot-actions/analyze?within_days=${within_days}`, { method: "POST" }),
  analyzeSingleLot: (lot_id: number, force = false) =>
    request<any[]>(`/lot-actions/lots/${lot_id}/analyze?force=${force}`, {
      method: "POST",
    }),
  lotActions: (lot_id: number) =>
    request<any[]>(`/lot-actions/lots/${lot_id}`),
  applyLotAction: (action_id: number) =>
    request<any>(`/lot-actions/${action_id}/apply`, { method: "POST" }),
  dismissLotAction: (action_id: number) =>
    request<any>(`/lot-actions/${action_id}/dismiss`, { method: "POST" }),

  // Reorder suggestions + draft mail
  reorderSuggestions: () => request<any[]>("/reorder/suggestions"),
  reorderDraftMail: (data: {
    product_id: number;
    order_qty: number;
    supplier_id?: number | null;
  }) =>
    request<{
      subject: string;
      body: string;
      supplier_email: string | null;
      supplier_phone: string | null;
    }>("/reorder/draft-mail", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Suppliers (top-level CRUD)
  listSuppliers: (search?: string, include_inactive?: boolean) =>
    request<any[]>(`/suppliers${qs({ search, include_inactive })}`),
  getSupplier: (id: number) => request<any>(`/suppliers/${id}`),
  supplierProducts: (id: number) =>
    request<any[]>(`/suppliers/${id}/products`),
  createSupplier: (data: Record<string, any>) =>
    request<any>("/suppliers", { method: "POST", body: JSON.stringify(data) }),
  updateSupplier: (id: number, data: Record<string, any>) =>
    request<any>(`/suppliers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteSupplier: (id: number) =>
    request<void>(`/suppliers/${id}`, { method: "DELETE" }),

  // Customers — backend uses `search` query param
  listCustomers: (search?: string) =>
    request<any[]>(`/customers${qs({ search })}`),
  customerOrders: (id: number) => request<any[]>(`/customers/${id}/orders`),

  // Chat — backend route is /panel/chat (router prefix /panel, endpoint /chat)
  panelChat: (message: string, history?: any[]) =>
    request<{ text: string; data: any | null }>("/panel/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),

  // Auth
  me: () => request<any>("/auth/me"),
};
