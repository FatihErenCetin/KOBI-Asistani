"use client";

import {
  CheckCircle2,
  Clock,
  History,
  Loader2,
  MapPin,
  Package,
  Phone,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  Star,
  Store,
  Truck,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { PurchaseOrderModal } from "@/components/marketplace/PurchaseOrderModal";
import { RecommendationCard } from "@/components/marketplace/RecommendationCard";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

interface Supplier {
  id: number;
  name: string;
  category: string | null;
  carrier: string | null;
  city: string | null;
  district: string | null;
  description: string | null;
  rating: number | null;
  contact_name: string | null;
  phone: string | null;
  email: string | null;
  last_used_at: string | null;
  linked_product_count: number;
}

interface Recommendation {
  id: number;
  product_id: number | null;
  product_name: string;
  suggested_supplier_id: number | null;
  suggested_supplier_name: string | null;
  suggested_quantity: number;
  estimated_unit_cost: number | null;
  confidence: number;
  reasoning: string;
  nearby_signal_count: number;
  status: string;
}

interface PurchaseOrder {
  id: number;
  supplier_id: number;
  supplier_name: string;
  status: string;
  total_cost: number;
  expected_delivery: string | null;
  received_at: string | null;
  ai_suggested: boolean;
  items: { product_name: string; quantity: number; product_unit: string }[];
  created_at: string;
}

const STATUS_PILL: Record<
  string,
  { label: string; cls: string; icon: any }
> = {
  draft: { label: "Taslak", cls: "bg-slate-100 text-slate-700", icon: Clock },
  sent: { label: "Gönderildi", cls: "bg-blue-100 text-blue-700", icon: Send },
  confirmed: {
    label: "Onaylandı",
    cls: "bg-amber-100 text-amber-700",
    icon: CheckCircle2,
  },
  received: {
    label: "Teslim alındı",
    cls: "bg-emerald-100 text-emerald-700",
    icon: CheckCircle2,
  },
  cancelled: {
    label: "İptal",
    cls: "bg-rose-100 text-rose-700",
    icon: XCircle,
  },
};

export default function MarketplacePage() {
  const [tab, setTab] = useState<"recommendations" | "suppliers" | "orders">(
    "recommendations",
  );
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [recent, setRecent] = useState<Supplier[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [filters, setFilters] = useState<{
    categories: string[];
    carriers: string[];
    cities: string[];
  }>({ categories: [], carriers: [], cities: [] });
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [carrier, setCarrier] = useState("");
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [modal, setModal] = useState<{
    supplier: Supplier;
    initialProductName?: string;
    initialQuantity?: number;
    initialUnitCost?: number | null;
    recommendationId?: number;
  } | null>(null);

  const reloadSuppliers = useCallback(async () => {
    const params: Record<string, string | undefined> = {};
    if (search) params.search = search;
    if (category) params.category = category;
    if (carrier) params.carrier = carrier;
    if (city) params.city = city;
    setSuppliers(await api.marketplaceSuppliers(params));
  }, [search, category, carrier, city]);

  const reloadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [s, r, recs, ords, f] = await Promise.all([
        api.marketplaceSuppliers(),
        api.marketplaceRecent(8),
        api.marketplaceRecommendations(),
        api.marketplacePurchaseOrders(),
        api.marketplaceFilters(),
      ]);
      setSuppliers(s);
      setRecent(r.map((x: any) => x.supplier));
      setRecommendations(recs);
      setOrders(ords);
      setFilters(f);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reloadAll();
  }, [reloadAll]);

  useEffect(() => {
    // Filter değişince sadece supplier listesi yenilenir
    const t = setTimeout(reloadSuppliers, 200);
    return () => clearTimeout(t);
  }, [reloadSuppliers]);

  async function generateRecs() {
    setGenerating(true);
    try {
      const r = await api.generateMarketplaceRecommendations({});
      setRecommendations(r);
    } finally {
      setGenerating(false);
    }
  }

  async function applyRecommendation(rec: Recommendation) {
    if (!rec.suggested_supplier_id) {
      alert("Bu öneri için tedarikçi atanmamış.");
      return;
    }
    const sup = suppliers.find((s) => s.id === rec.suggested_supplier_id);
    if (!sup) {
      alert(
        "Önerilen tedarikçi marketplace'te bulunamadı. Önce tedarikçileri yükleyin.",
      );
      return;
    }
    setModal({
      supplier: sup,
      initialProductName: rec.product_name,
      initialQuantity: rec.suggested_quantity,
      initialUnitCost: rec.estimated_unit_cost,
      recommendationId: rec.id,
    });
  }

  async function markReceived(po: PurchaseOrder) {
    if (!confirm(`#${po.id} teslim alındı olarak işaretlensin mi? Stok artar.`))
      return;
    await api.updatePurchaseOrderStatus(po.id, "received");
    await reloadAll();
  }

  const recCountActive = useMemo(
    () => recommendations.filter((r) => r.status === "active").length,
    [recommendations],
  );

  return (
    <div className="max-w-7xl space-y-5">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <Store className="h-6 w-6 text-amber-600" />
            Tedarikçi Pazarı
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Tüm tedarikçiler, AI önerileri ve satınalma siparişlerin tek
            ekranda.
          </p>
        </div>
        <button
          onClick={generateRecs}
          disabled={generating}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded border border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100 disabled:opacity-50"
        >
          {generating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          AI önerilerini yenile
        </button>
      </header>

      {/* Recent suppliers */}
      {recent.length > 0 && (
        <section>
          <h2 className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-700 mb-2">
            <History className="h-4 w-4 text-slate-500" />
            Son kullanılan tedarikçiler
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {recent.map((s) => (
              <button
                key={s.id}
                onClick={() => setModal({ supplier: s })}
                className="shrink-0 w-56 text-left rounded-lg border border-slate-200 bg-white p-3 hover:border-amber-300 hover:shadow-sm transition"
              >
                <p className="font-medium text-sm text-slate-800 truncate">
                  {s.name}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {s.category ?? "—"}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Son: {s.last_used_at ? formatDateTime(s.last_used_at) : "—"}
                </p>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1">
          <TabBtn
            active={tab === "recommendations"}
            onClick={() => setTab("recommendations")}
            icon={Sparkles}
            label="AI Önerileri"
            badge={recCountActive}
          />
          <TabBtn
            active={tab === "suppliers"}
            onClick={() => setTab("suppliers")}
            icon={Store}
            label="Tedarikçiler"
            badge={suppliers.length}
          />
          <TabBtn
            active={tab === "orders"}
            onClick={() => setTab("orders")}
            icon={Package}
            label="Siparişlerim"
            badge={orders.length}
          />
        </nav>
      </div>

      {loading && (
        <p className="text-sm text-slate-500">Yükleniyor…</p>
      )}

      {/* Recommendations */}
      {tab === "recommendations" && (
        <section className="space-y-4">
          {recommendations.length === 0 ? (
            <div className="bg-amber-50/40 border border-amber-200 rounded-xl p-6 text-center">
              <Sparkles className="h-8 w-8 text-amber-500 mx-auto mb-2" />
              <p className="text-sm text-slate-700">
                Henüz aktif öneri yok. AI analizini başlatmak için yukarıdaki
                &quot;AI önerilerini yenile&quot; butonuna tıkla.
              </p>
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {recommendations
                .filter((r) => r.status === "active")
                .map((r) => (
                  <RecommendationCard
                    key={r.id}
                    rec={r}
                    onChange={reloadAll}
                    onApply={applyRecommendation}
                  />
                ))}
            </div>
          )}
          <p className="text-xs text-slate-500">
            Öneriler komşu KOBİ'lerin son satınalma trendlerinden üretilir.
            Aynı şehirde + aynı kargo şirketini kullanan dükkânlar takip
            edilir.
          </p>
        </section>
      )}

      {/* Suppliers */}
      {tab === "suppliers" && (
        <section className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Tedarikçi ara..."
                className="pl-7 pr-3 py-1.5 text-sm border border-slate-300 rounded w-56"
              />
            </div>
            <FilterSelect
              value={category}
              onChange={setCategory}
              options={filters.categories}
              placeholder="Tüm kategoriler"
            />
            <FilterSelect
              value={carrier}
              onChange={setCarrier}
              options={filters.carriers}
              placeholder="Tüm kargolar"
            />
            <FilterSelect
              value={city}
              onChange={setCity}
              options={filters.cities}
              placeholder="Tüm şehirler"
            />
            {(search || category || carrier || city) && (
              <button
                onClick={() => {
                  setSearch("");
                  setCategory("");
                  setCarrier("");
                  setCity("");
                }}
                className="text-xs text-slate-500 hover:text-slate-800"
              >
                Filtreleri temizle
              </button>
            )}
          </div>

          {suppliers.length === 0 ? (
            <p className="text-sm text-slate-500 italic">
              Filtrelerle eşleşen tedarikçi bulunamadı.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {suppliers.map((s) => (
                <article
                  key={s.id}
                  className="rounded-lg border border-slate-200 bg-white p-4 space-y-2 hover:shadow-sm transition"
                >
                  <header className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <h3 className="font-semibold text-slate-900 truncate">
                        {s.name}
                      </h3>
                      {s.category && (
                        <p className="text-xs text-slate-500">{s.category}</p>
                      )}
                    </div>
                    {s.rating != null && (
                      <span className="shrink-0 inline-flex items-center gap-0.5 text-xs text-amber-700">
                        <Star className="h-3 w-3 fill-amber-500 stroke-amber-500" />
                        {s.rating.toFixed(1)}
                      </span>
                    )}
                  </header>
                  {s.description && (
                    <p className="text-xs text-slate-600 line-clamp-2">
                      {s.description}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2 text-[11px] text-slate-500 pt-1">
                    {s.city && (
                      <span className="inline-flex items-center gap-0.5">
                        <MapPin className="h-3 w-3" />
                        {s.city}
                        {s.district ? ` / ${s.district}` : ""}
                      </span>
                    )}
                    {s.carrier && (
                      <span className="inline-flex items-center gap-0.5">
                        <Truck className="h-3 w-3" />
                        {s.carrier}
                      </span>
                    )}
                    {s.phone && (
                      <span className="inline-flex items-center gap-0.5">
                        <Phone className="h-3 w-3" />
                        {s.phone}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                    <span className="text-[11px] text-slate-500">
                      {s.linked_product_count} bağlı ürün
                    </span>
                    <button
                      onClick={() => setModal({ supplier: s })}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 hover:underline"
                    >
                      Sipariş geç →
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Orders */}
      {tab === "orders" && (
        <section className="space-y-3">
          {orders.length === 0 ? (
            <p className="text-sm text-slate-500 italic">
              Henüz satınalma siparişi yok. "Tedarikçiler" sekmesinden geç.
            </p>
          ) : (
            <ul className="space-y-2">
              {orders.map((po) => {
                const pill = STATUS_PILL[po.status] ?? STATUS_PILL.draft;
                const Icon = pill.icon;
                return (
                  <li
                    key={po.id}
                    className="rounded-lg border border-slate-200 bg-white p-4 flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-xs text-slate-500">
                          #{po.id}
                        </span>
                        <span
                          className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded ${pill.cls}`}
                        >
                          <Icon className="h-3 w-3" />
                          {pill.label}
                        </span>
                        {po.ai_suggested && (
                          <span className="inline-flex items-center gap-1 text-[11px] text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                            <Sparkles className="h-3 w-3" /> AI
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-800">
                        {po.supplier_name}
                      </p>
                      <p className="text-xs text-slate-600 mt-0.5 truncate">
                        {po.items
                          .map(
                            (it) =>
                              `${it.quantity} ${it.product_unit} ${it.product_name}`,
                          )
                          .join(" · ")}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="font-semibold tabular-nums">
                        {formatTRY(po.total_cost)}
                      </p>
                      {po.status !== "received" && po.status !== "cancelled" && (
                        <button
                          onClick={() => markReceived(po)}
                          className="mt-1 text-xs text-emerald-700 hover:underline"
                        >
                          Teslim alındı ↑
                        </button>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      )}

      {modal && (
        <PurchaseOrderModal
          open
          supplier={modal.supplier}
          initialProductName={modal.initialProductName}
          initialQuantity={modal.initialQuantity}
          initialUnitCost={modal.initialUnitCost}
          recommendationId={modal.recommendationId}
          onClose={() => setModal(null)}
          onCreated={() => {
            reloadAll();
          }}
        />
      )}
    </div>
  );
}

function TabBtn({
  active,
  onClick,
  icon: Icon,
  label,
  badge,
}: {
  active: boolean;
  onClick: () => void;
  icon: any;
  label: string;
  badge?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm rounded-t-md border-b-2 transition ${
        active
          ? "border-amber-500 text-amber-700 bg-amber-50/40"
          : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100"
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
      {badge != null && badge > 0 && (
        <span
          className={`ml-1 inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full text-[10px] font-semibold ${
            active ? "bg-amber-500 text-white" : "bg-slate-200 text-slate-700"
          }`}
        >
          {badge}
        </span>
      )}
    </button>
  );
}

function FilterSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-2 py-1.5 text-sm border border-slate-300 rounded"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );
}
