import type { ReactNode } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowUpRight,
  Lightbulb,
  MessageSquareText,
  Clock3,
  Package,
  ShoppingBag,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Truck,
} from "lucide-react";

import { api } from "@/lib/api";
import { formatDateTime, formatTRY, statusColor, statusLabel } from "@/lib/format";

type StatAccent = "emerald" | "amber" | "rose" | "blue";

const statAccent: Record<StatAccent, string> = {
  emerald: "border-brand-200/80 bg-brand-50/80 text-brand-700",
  amber: "border-amber-200/80 bg-amber-50/80 text-amber-700",
  rose: "border-rose-200/80 bg-rose-50/80 text-rose-700",
  blue: "border-sky-200/80 bg-sky-50/80 text-sky-700",
};

function StatCard({
  title,
  value,
  sub,
  trend,
  icon: Icon,
  accent = "emerald",
  href,
}: {
  title: string;
  value: string | number;
  sub?: string;
  trend?: number;
  icon: any;
  accent?: StatAccent;
  href?: string;
}) {
  const content = (
    <div className="group relative overflow-hidden rounded-3xl border border-white/80 bg-white/90 p-5 shadow-card transition duration-300 hover:-translate-y-0.5 hover:shadow-soft">
      <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-brand-500/10 blur-2xl transition group-hover:bg-brand-500/20" />
      <div className="relative flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">{title}</p>
          <p className="mt-3 text-3xl font-extrabold tracking-tight text-slate-950 tabular-nums">{value}</p>
          {sub && <p className="mt-1 text-sm font-medium text-slate-500">{sub}</p>}
        </div>
        <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border ${statAccent[accent]}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
      {trend !== undefined && (
        <div className={`relative mt-5 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${trend >= 0 ? "bg-brand-50 text-brand-700" : "bg-rose-50 text-rose-700"}`}>
          {trend >= 0 ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
          {trend >= 0 ? "+" : ""}{trend.toFixed(1)}% dünle karşılaştırma
        </div>
      )}
      {href && <ArrowUpRight className="absolute right-5 top-5 h-4 w-4 text-slate-300 transition group-hover:text-brand-500" />}
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

function SectionCard({
  title,
  description,
  action,
  children,
  className = "",
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`surface-card overflow-hidden ${className}`}>
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
        <div>
          <h2 className="section-title">{title}</h2>
          {description && <p className="section-subtitle mt-1">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}


function AiRecommendations({
  summary,
  lowStockItems,
  riskCount,
}: {
  summary: any;
  lowStockItems: any[];
  riskCount: number;
}) {
  const firstLow = lowStockItems[0];
  const items = [
    firstLow
      ? {
          title: `${firstLow.name} kritik stokta`,
          description: `${firstLow.stock} ${firstLow.unit} kaldı. Tedarik planı oluşturulmalı.`,
          tone: "rose",
          href: "/chat",
        }
      : {
          title: "Stok seviyesi güvenli",
          description: "Kritik stokta ürün görünmüyor.",
          tone: "emerald",
          href: "/products",
        },
    summary.pending_to_prepare > 0
      ? {
          title: `${summary.pending_to_prepare} sipariş hazırlanacak`,
          description: summary.urgent_today > 0 ? `${summary.urgent_today} sipariş bugün öncelikli.` : "Paketleme sırası kontrol edilmeli.",
          tone: summary.urgent_today > 0 ? "amber" : "blue",
          href: "/orders?status=pending",
        }
      : {
          title: "Bekleyen sipariş yok",
          description: "Hazırlama kuyruğu şu an temiz.",
          tone: "emerald",
          href: "/orders",
        },
    riskCount > 0
      ? {
          title: `${riskCount} kargo riski var`,
          description: "Müşteri memnuniyeti için bilgilendirme mesajı hazırlanabilir.",
          tone: "rose",
          href: "/carriers",
        }
      : {
          title: "Kargo riski düşük",
          description: "Son 30 günlük riskli gönderi görünmüyor.",
          tone: "emerald",
          href: "/carriers",
        },
  ];

  const toneMap: Record<string, string> = {
    rose: "border-rose-100 bg-rose-50 text-rose-700",
    amber: "border-amber-100 bg-amber-50 text-amber-700",
    emerald: "border-emerald-100 bg-emerald-50 text-emerald-700",
    blue: "border-sky-100 bg-sky-50 text-sky-700",
  };

  return (
    <section className="surface-card overflow-hidden">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-100 px-6 py-5 lg:flex-row lg:items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-700">
            <Lightbulb className="h-3.5 w-3.5" aria-hidden="true" />
            AI önerileri
          </div>
          <h2 className="mt-3 section-title">Bugün öncelik verilecek aksiyonlar</h2>
          <p className="section-subtitle mt-1">Sipariş, stok ve kargo verisine göre otomatik çıkarıldı.</p>
        </div>
        <Link href="/chat" className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-extrabold text-white transition hover:bg-brand-700">
          <MessageSquareText className="h-4 w-4" aria-hidden="true" />
          Asistana sor
        </Link>
      </div>
      <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-3">
        {items.map((item) => (
          <Link key={item.title} href={item.href} className={`rounded-3xl border p-4 transition hover:-translate-y-0.5 hover:shadow-soft ${toneMap[item.tone]}`}>
            <p className="text-sm font-extrabold">{item.title}</p>
            <p className="mt-2 text-xs font-semibold leading-5 opacity-80">{item.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

function EmptyRow({ colSpan, text }: { colSpan: number; text: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-6 py-10 text-center text-sm font-medium text-slate-400">
        {text}
      </td>
    </tr>
  );
}

export default async function DashboardPage() {
  const data = await api.dashboardToday();
  const riskData = await api.carrierRisks().catch(() => ({ count: 0, orders: [] }));
  const { summary, pending_orders, low_stock_items, recent_orders, todays_shipments } = data;
  const operationScore = Math.max(0, 100 - summary.low_stock_count * 8 - summary.pending_to_prepare * 2);

  return (
    <div className="page-wrap">
      <header className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-slate-950 px-7 py-7 text-white shadow-card">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,.40),transparent_28rem)]" />
        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-bold text-brand-100">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              AI destekli operasyon paneli
            </div>
            <h1 className="mt-5 max-w-2xl text-3xl font-extrabold tracking-tight sm:text-4xl">
              Bugünün sipariş, stok ve kargo akışı tek ekranda.
            </h1>
            <p className="mt-3 text-sm font-medium text-slate-300">
              {new Date().toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/10 p-4 backdrop-blur">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Operasyon skoru</p>
            <div className="mt-2 flex items-end gap-2">
              <span className="text-4xl font-extrabold tabular-nums">{operationScore}</span>
              <span className="pb-1 text-sm font-semibold text-slate-300">/ 100</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">Düşük stok ve bekleyen sipariş yoğunluğuna göre</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Son 24 Saat"
          value={`${summary.orders_last_24h} sipariş`}
          sub={formatTRY(summary.revenue_last_24h)}
          trend={summary.orders_vs_yesterday_pct}
          icon={ShoppingBag}
          accent="emerald"
          href="/orders"
        />
        <StatCard
          title="Hazırlanacak"
          value={summary.pending_to_prepare}
          sub={summary.urgent_today > 0 ? `${summary.urgent_today} acil bugün` : "Acil sipariş yok"}
          icon={Package}
          accent={summary.urgent_today > 0 ? "amber" : "blue"}
          href="/orders?status=pending"
        />
        <StatCard
          title="Bugün Teslim"
          value={summary.shipments_today}
          sub="kargo hareketi"
          icon={Truck}
          accent="blue"
          href="/carriers"
        />
        <StatCard
          title="Düşük Stok"
          value={summary.low_stock_count}
          sub="eşik altı ürün"
          icon={AlertTriangle}
          accent={summary.low_stock_count > 0 ? "rose" : "emerald"}
          href="/products?low=1"
        />
      </div>

      <AiRecommendations summary={summary} lowStockItems={low_stock_items} riskCount={riskData?.count ?? 0} />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <SectionCard
          title="Bekleyen Siparişler"
          description="Hazırlama ve kargo öncesi takip edilmesi gerekenler"
          className="xl:col-span-2"
          action={<Link href="/orders?status=pending" className="filter-pill">Tümünü gör</Link>}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head-row">
                  <th className="table-cell text-left">Sipariş</th>
                  <th className="table-cell text-left">Müşteri</th>
                  <th className="table-cell text-left">Durum</th>
                  <th className="table-cell text-right">Tutar</th>
                  <th className="table-cell text-left">Tarih</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pending_orders.slice(0, 6).map((o: any) => (
                  <tr key={o.id} className="transition hover:bg-slate-50/80">
                    <td className="table-cell">
                      <Link href={`/orders/${o.id}`} className="font-mono font-bold text-brand-700 hover:underline">#{o.id}</Link>
                    </td>
                    <td className="table-cell font-semibold text-slate-900">{o.customer_name}</td>
                    <td className="table-cell">
                      <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${statusColor(o.status)}`}>{statusLabel(o.status)}</span>
                    </td>
                    <td className="table-cell text-right font-bold text-slate-950 tabular-nums">{formatTRY(o.total)}</td>
                    <td className="table-cell text-xs font-medium text-slate-500">{formatDateTime(o.created_at)}</td>
                  </tr>
                ))}
                {pending_orders.length === 0 && <EmptyRow colSpan={5} text="Bekleyen sipariş yok" />}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <div className="space-y-6">
          <SectionCard
            title="Düşük Stok"
            description="Öncelikli yenilenmesi gereken ürünler"
            action={<Link href="/products?low=1" className="text-sm font-bold text-rose-600 hover:text-rose-700">Listele</Link>}
          >
            {low_stock_items.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm font-medium text-slate-400">Stoklar yeterli</div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {low_stock_items.slice(0, 6).map((p: any) => {
                  const pct = Math.min(100, Math.round((p.stock / Math.max(1, p.low_stock_threshold)) * 100));
                  return (
                    <li key={p.id} className="px-6 py-4">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold text-slate-900">{p.name}</span>
                        <span className="font-bold text-rose-600">{p.stock} {p.unit}</span>
                      </div>
                      <div className="mt-2 h-2 overflow-hidden rounded-full bg-rose-100">
                        <div className="h-full rounded-full bg-rose-500" style={{ width: `${pct}%` }} />
                      </div>
                      <p className="mt-1 text-xs font-medium text-slate-400">Eşik: {p.low_stock_threshold}</p>
                    </li>
                  );
                })}
              </ul>
            )}
          </SectionCard>

          <SectionCard title="Bugün Teslim" description="Gün içinde takip edilecek gönderiler">
            {todays_shipments.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm font-medium text-slate-400">Bugün kargo yok</div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {todays_shipments.slice(0, 5).map((s: any) => (
                  <li key={s.tracking_no} className="px-6 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">{s.customer_name}</p>
                        <p className="mt-1 text-xs font-medium text-slate-500">{s.current_location ?? "Konum bilgisi yok"}</p>
                      </div>
                      <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${statusColor(s.status)}`}>{statusLabel(s.status)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      </div>

      <SectionCard
        title="Son 24 Saatte Gelen Siparişler"
        description="Yeni sipariş hareketlerini hızlıca kontrol edin"
        action={<Clock3 className="h-5 w-5 text-slate-300" aria-hidden="true" />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head-row">
                <th className="table-cell text-left">Sipariş</th>
                <th className="table-cell text-left">Müşteri</th>
                <th className="table-cell text-left">Durum</th>
                <th className="table-cell text-right">Tutar</th>
                <th className="table-cell text-left">Tarih</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent_orders.slice(0, 7).map((o: any) => (
                <tr key={o.id} className="transition hover:bg-slate-50/80">
                  <td className="table-cell">
                    <Link href={`/orders/${o.id}`} className="font-mono font-bold text-brand-700 hover:underline">#{o.id}</Link>
                  </td>
                  <td className="table-cell font-semibold text-slate-900">{o.customer_name}</td>
                  <td className="table-cell"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${statusColor(o.status)}`}>{statusLabel(o.status)}</span></td>
                  <td className="table-cell text-right font-bold text-slate-950 tabular-nums">{formatTRY(o.total)}</td>
                  <td className="table-cell text-xs font-medium text-slate-500">{formatDateTime(o.created_at)}</td>
                </tr>
              ))}
              {recent_orders.length === 0 && <EmptyRow colSpan={5} text="Son 24 saatte sipariş yok" />}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
