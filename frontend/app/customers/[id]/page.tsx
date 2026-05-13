import type { ComponentType, ReactNode } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ChevronRight,
  Phone,
  ShoppingBag,
  TrendingUp,
  Package,
  Calendar,
  Sparkles,
} from "lucide-react";

import { api } from "@/lib/api";
import {
  formatDateTime,
  formatTRY,
  statusColor,
  statusLabel,
} from "@/lib/format";

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                   */
/* -------------------------------------------------------------------------- */

function getInitials(name: string): string {
  if (!name || name === "?") return "?";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const day = Math.floor(diff / 86_400_000);
  if (day === 0) return "Bugün";
  if (day === 1) return "Dün";
  if (day < 7) return `${day} gün önce`;
  if (day < 30) return `${Math.floor(day / 7)} hafta önce`;
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatDateShort(iso: string): string {
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function topProducts(
  orders: any[],
  limit = 5
): { name: string; quantity: number; revenue: number }[] {
  const map = new Map<
    string,
    { name: string; quantity: number; revenue: number }
  >();
  for (const o of orders) {
    for (const item of o.items ?? []) {
      const cur = map.get(item.product_name) ?? {
        name: item.product_name,
        quantity: 0,
        revenue: 0,
      };
      cur.quantity += item.quantity;
      cur.revenue += item.quantity * item.unit_price;
      map.set(item.product_name, cur);
    }
  }
  return [...map.values()]
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit);
}

/* -------------------------------------------------------------------------- */
/*  Inline UI bits                                                            */
/* -------------------------------------------------------------------------- */

function BackNav({ id }: { id: string }) {
  return (
    <nav aria-label="Sayfa konumu">
      <Link
        href="/customers"
        className="group inline-flex h-11 items-center gap-2 rounded-lg -ml-2 px-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <ArrowLeft
          className="h-4 w-4 transition group-hover:-translate-x-0.5"
          aria-hidden="true"
        />
        <span>Müşteriler</span>
        <ChevronRight className="h-4 w-4 text-slate-300" aria-hidden="true" />
        <span className="font-mono text-slate-500">#{id}</span>
      </Link>
    </nav>
  );
}

function InitialsAvatar({ name }: { name: string }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xl font-semibold text-brand-700 ring-1 ring-brand-200"
    >
      {getInitials(name)}
    </span>
  );
}

function KpiCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "slate",
  emphasis = false,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "slate" | "brand" | "indigo" | "amber";
  emphasis?: boolean;
}) {
  const tones: Record<string, string> = {
    slate: "bg-slate-100 text-slate-600",
    brand: "bg-brand-50 text-brand-700",
    indigo: "bg-indigo-50 text-indigo-700",
    amber: "bg-amber-50 text-amber-700",
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300">
      <div className="flex items-center justify-between">
        <dt className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
          {label}
        </dt>
        <span
          className={`inline-flex h-8 w-8 items-center justify-center rounded-lg ${tones[tone]}`}
        >
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
      </div>
      <dd
        className={`mt-3 ${
          emphasis
            ? "text-3xl font-bold text-slate-900"
            : "text-2xl font-semibold text-slate-900"
        } tabular-nums`}
      >
        {value}
      </dd>
      {hint && (
        <p className="mt-1 text-xs text-slate-500 tabular-nums">{hint}</p>
      )}
    </div>
  );
}

function EmptyState({ id }: { id: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-200 bg-white p-12 text-center shadow-sm">
      <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
        <ShoppingBag className="h-6 w-6 text-slate-400" aria-hidden="true" />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-slate-900">
        Bu müşterinin henüz siparişi yok
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Müşteri #{id} için kayıtlı bir sipariş bulunamadı. İlk sipariş geldiğinde
        bu sayfa otomatik olarak dolacaktır.
      </p>
      <Link
        href="/customers"
        className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        <span>Müşteriler listesine dön</span>
      </Link>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Page                                                                      */
/* -------------------------------------------------------------------------- */

export default async function CustomerDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const orders = await api.customerOrders(Number(params.id));

  // Empty state — no orders, no customer record reachable
  if (!orders || orders.length === 0) {
    return (
      <div className="max-w-5xl space-y-6">
        <BackNav id={params.id} />
        <EmptyState id={params.id} />
      </div>
    );
  }

  const customer = orders[0].customer;
  const total = orders.reduce((acc: number, o: any) => acc + o.total, 0);
  const avgBasket = total / orders.length;

  // Sorted by date — newest first for "son sipariş", oldest first for "ilk sipariş"
  const byDateDesc = [...orders].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  const byDateAsc = [...orders].sort(
    (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
  const lastOrder = byDateDesc[0];
  const firstOrder = byDateAsc[0];

  // Highest-value order id (for "En Yüksek" badge)
  const highestOrderId = orders.reduce(
    (best: any, o: any) => (o.total > (best?.total ?? -1) ? o : best),
    null as any
  )?.id;

  const products = topProducts(orders, 5);
  const productMaxRevenue = products[0]?.revenue ?? 0;

  return (
    <div className="max-w-5xl space-y-6">
      <BackNav id={params.id} />

      {/* Profil kartı */}
      <section
        aria-labelledby="profile-heading"
        className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 id="profile-heading" className="sr-only">
          Müşteri profili
        </h2>
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <InitialsAvatar name={customer.name} />
            <div className="min-w-0">
              <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                Müşteri
              </p>
              <h1 className="mt-0.5 text-2xl font-bold tracking-tight text-slate-900">
                {customer.name}
              </h1>
              <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-slate-600">
                <span className="font-mono text-slate-500">#{customer.id}</span>
                <span aria-hidden="true" className="text-slate-300">
                  ·
                </span>
                <span className="inline-flex items-center gap-1">
                  <Calendar
                    className="h-3.5 w-3.5 text-slate-400"
                    aria-hidden="true"
                  />
                  İlk sipariş: {formatDateShort(firstOrder.created_at)}
                </span>
              </p>
            </div>
          </div>

          {/* İletişim grubu — telefon + CTA */}
          <div className="flex flex-col items-stretch gap-2 sm:items-end">
            <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500 sm:text-right">
              İletişim
            </p>
            <div className="flex flex-wrap items-center gap-2 sm:justify-end">
              {customer.phone ? (
                <>
                  <a
                    href={`tel:${customer.phone}`}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 tabular-nums transition hover:bg-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                  >
                    <Phone className="h-4 w-4 text-slate-500" aria-hidden="true" />
                    <span>{customer.phone}</span>
                  </a>
                  <a
                    href={`tel:${customer.phone}`}
                    aria-label={`${customer.name} adlı müşteriyi ara`}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
                  >
                    <Phone className="h-4 w-4" aria-hidden="true" />
                    <span>Ara</span>
                  </a>
                </>
              ) : (
                <>
                  <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-400">
                    <Phone className="h-4 w-4" aria-hidden="true" />
                    Telefon kayıtlı değil
                  </span>
                  <button
                    type="button"
                    disabled
                    aria-disabled="true"
                    aria-label="Telefon kayıtlı olmadığı için aranamaz"
                    className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-lg bg-slate-200 px-4 py-2 text-sm font-medium text-slate-400"
                  >
                    <Phone className="h-4 w-4" aria-hidden="true" />
                    <span>Ara</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* KPI kartları */}
      <section aria-labelledby="kpi-heading">
        <h2 id="kpi-heading" className="sr-only">
          Özet metrikler
        </h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            icon={ShoppingBag}
            label="Toplam sipariş"
            value={orders.length}
            hint={`Son ${orders.length} kayıt`}
            tone="slate"
          />
          <KpiCard
            icon={TrendingUp}
            label="Toplam harcama"
            value={formatTRY(total)}
            tone="brand"
            emphasis
          />
          <KpiCard
            icon={Package}
            label="Ortalama sepet"
            value={formatTRY(avgBasket)}
            hint={`${orders.length} sipariş üzerinden`}
            tone="indigo"
          />
          <KpiCard
            icon={Calendar}
            label="Son sipariş"
            value={relativeTime(lastOrder.created_at)}
            hint={formatDateShort(lastOrder.created_at)}
            tone="amber"
          />
        </dl>
      </section>

      {/* Alt iki kolon: En sık ürünler + Sipariş geçmişi */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* En sık aldığı ürünler */}
        <section
          aria-labelledby="top-products-heading"
          className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm lg:col-span-2"
        >
          <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <div className="flex items-center gap-2">
              <Sparkles
                className="h-4 w-4 text-brand-600"
                aria-hidden="true"
              />
              <h2
                id="top-products-heading"
                className="text-sm font-semibold text-slate-800"
              >
                En Sık Aldığı Ürünler
              </h2>
            </div>
            <span className="text-xs text-slate-500 tabular-nums">
              {products.length}
            </span>
          </header>

          {products.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-500">
              Ürün geçmişi bulunamadı.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {products.map((p, i) => {
                const pct =
                  productMaxRevenue > 0
                    ? Math.max(6, Math.round((p.revenue / productMaxRevenue) * 100))
                    : 0;
                return (
                  <li
                    key={p.name}
                    className="group px-5 py-3 transition hover:bg-slate-50"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex h-5 w-5 items-center justify-center rounded-md bg-slate-100 text-[11px] font-semibold text-slate-600 tabular-nums">
                            {i + 1}
                          </span>
                          <p className="truncate text-sm font-medium text-slate-900">
                            {p.name}
                          </p>
                        </div>
                        <p className="mt-1 pl-7 text-xs text-slate-500 tabular-nums">
                          {p.quantity} adet · {formatTRY(p.revenue)}
                        </p>
                      </div>
                    </div>
                    {/* mini revenue bar */}
                    <div
                      className="ml-7 mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-100"
                      role="presentation"
                    >
                      <div
                        className="h-full rounded-full bg-brand-500/80 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        {/* Sipariş geçmişi */}
        <section
          aria-labelledby="orders-heading"
          className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm lg:col-span-3"
        >
          <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <div className="flex items-center gap-2">
              <ShoppingBag
                className="h-4 w-4 text-slate-400"
                aria-hidden="true"
              />
              <h2
                id="orders-heading"
                className="text-sm font-semibold text-slate-800"
              >
                Sipariş Geçmişi
              </h2>
            </div>
            <span className="text-xs text-slate-500 tabular-nums">
              {orders.length} kayıt
            </span>
          </header>

          {orders.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-500">
              Bu müşterinin henüz siparişi yok.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                    <th scope="col" className="px-4 py-2 text-left">
                      #
                    </th>
                    <th scope="col" className="px-4 py-2 text-left">
                      Tarih
                    </th>
                    <th scope="col" className="px-4 py-2 text-left">
                      Durum
                    </th>
                    <th scope="col" className="px-4 py-2 text-right">
                      Tutar
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {byDateDesc.map((o: any) => {
                    const isHighest = o.id === highestOrderId;
                    return (
                      <tr
                        key={o.id}
                        className="border-t border-slate-100 odd:bg-slate-50/60 transition hover:bg-brand-50/40"
                      >
                        <td className="px-4 py-2.5">
                          <Link
                            href={`/orders/${o.id}`}
                            className="font-mono text-sm font-medium text-brand-700 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                          >
                            #{o.id}
                          </Link>
                        </td>
                        <td className="px-4 py-2.5 text-slate-600 tabular-nums">
                          {formatDateTime(o.created_at)}
                        </td>
                        <td className="px-4 py-2.5">
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColor(
                              o.status
                            )}`}
                          >
                            {statusLabel(o.status)}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {isHighest && orders.length > 1 && (
                              <span className="inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-700 ring-1 ring-inset ring-brand-200">
                                En Yüksek
                              </span>
                            )}
                            <span
                              className={`tabular-nums ${
                                isHighest
                                  ? "font-semibold text-slate-900"
                                  : "text-slate-700"
                              }`}
                            >
                              {formatTRY(o.total)}
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-slate-200 bg-white">
                    <td
                      colSpan={3}
                      className="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0.08em] text-slate-500"
                    >
                      Toplam
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-bold text-slate-900 tabular-nums">
                      {formatTRY(total)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
