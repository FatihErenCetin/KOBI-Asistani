import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  CalendarCheck,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  Package,
  Phone,
  StickyNote,
  Truck,
} from "lucide-react";

import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { ShipmentTimeline } from "@/components/orders/ShipmentTimeline";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

/* -------------------------------------------------------------------------- */
/*  Local helpers                                                             */
/* -------------------------------------------------------------------------- */

function getInitials(name: string): string {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function formatDateOnly(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function InitialsAvatar({ name }: { name: string }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand-100 text-base font-semibold text-brand-700 ring-1 ring-brand-200"
    >
      {getInitials(name)}
    </span>
  );
}

function MetaItem({
  icon: Icon,
  label,
  value,
  emphasis = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: React.ReactNode;
  emphasis?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon
        className="mt-0.5 h-4 w-4 shrink-0 text-slate-400"
        aria-hidden="true"
      />
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
          {label}
        </p>
        <p
          className={
            emphasis
              ? "mt-0.5 text-base font-semibold text-slate-900 tabular-nums"
              : "mt-0.5 text-sm font-medium text-slate-800 tabular-nums"
          }
        >
          {value}
        </p>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Status → primary action mapping (UI-only mock)                            */
/* -------------------------------------------------------------------------- */

type OrderStatus =
  | "pending"
  | "prepared"
  | "shipped"
  | "delivered"
  | "cancelled";

function getPrimaryAction(status: string): {
  label: string;
  nextStatus: string;
} | null {
  switch (status as OrderStatus) {
    case "pending":
      return { label: "Hazırlandı olarak işaretle", nextStatus: "prepared" };
    case "prepared":
      return { label: "Kargoya ver", nextStatus: "shipped" };
    case "shipped":
      return {
        label: "Teslim edildi olarak işaretle",
        nextStatus: "delivered",
      };
    default:
      return null;
  }
}

function canCancel(status: string): boolean {
  return status === "pending" || status === "prepared";
}

/* -------------------------------------------------------------------------- */
/*  Server-side stub button (interactive bit lives in tiny client component)  */
/* -------------------------------------------------------------------------- */

// Client component for the mock action button — defined inline so the rest of
// the page stays a Server Component.
import { OrderActionButton } from "./OrderActionButton";

/* -------------------------------------------------------------------------- */
/*  Page                                                                      */
/* -------------------------------------------------------------------------- */

export default async function OrderDetailPage({
  params,
}: {
  params: { id: string };
}) {
  let order: any;
  try {
    order = await api.getOrder(Number(params.id));
  } catch {
    notFound();
  }

  const itemCount = order.items?.length ?? 0;
  const primaryAction = getPrimaryAction(order.status);
  const showCancel = canCancel(order.status);

  return (
    <div className="max-w-5xl space-y-6">
      {/* Breadcrumb / back */}
      <nav aria-label="Sayfa konumu">
        <Link
          href="/orders"
          className="group inline-flex h-11 items-center gap-2 rounded-lg px-2 -ml-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <ArrowLeft
            className="h-4 w-4 transition group-hover:-translate-x-0.5"
            aria-hidden="true"
          />
          <span>Siparişler</span>
          <ChevronRight className="h-4 w-4 text-slate-300" aria-hidden="true" />
          <span className="font-mono text-slate-500">#{order.id}</span>
        </Link>
      </nav>

      {/* Header */}
      <header className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
              Sipariş
            </p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
              #{order.id}
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              {itemCount} kalem · Oluşturuldu {formatDateTime(order.created_at)}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <OrderStatusBadge status={order.status} />
          </div>
        </div>

        {/* Meta grid */}
        <div className="mt-6 grid grid-cols-1 gap-5 border-t border-slate-100 pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <MetaItem
            icon={Package}
            label="Toplam"
            value={formatTRY(order.total)}
            emphasis
          />
          <MetaItem
            icon={CalendarClock}
            label="Oluşturuldu"
            value={formatDateTime(order.created_at)}
          />
          <MetaItem
            icon={CalendarCheck}
            label="Teslimat sözü"
            value={
              order.promised_delivery
                ? formatDateOnly(order.promised_delivery)
                : "—"
            }
          />
          <MetaItem
            icon={Package}
            label="Kalem"
            value={`${itemCount} ürün`}
          />
        </div>
      </header>

      {/* Customer card */}
      <section
        aria-labelledby="customer-heading"
        className="rounded-xl border border-slate-200 bg-white shadow-sm transition hover:border-slate-300"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2
            id="customer-heading"
            className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500"
          >
            Müşteri
          </h2>
          <Link
            href={`/customers/${order.customer.id}`}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-brand-700 transition hover:bg-brand-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            Müşteri detayı
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
        <div className="flex flex-wrap items-center gap-4 p-5">
          <InitialsAvatar name={order.customer.name} />
          <div className="min-w-0 flex-1">
            <Link
              href={`/customers/${order.customer.id}`}
              className="block text-lg font-semibold text-slate-900 hover:text-brand-700 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              {order.customer.name}
            </Link>
            {order.customer.phone ? (
              <a
                href={`tel:${order.customer.phone}`}
                className="mt-1 inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-brand-700"
              >
                <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                <span className="tabular-nums">{order.customer.phone}</span>
              </a>
            ) : (
              <p className="mt-1 inline-flex items-center gap-1.5 text-sm text-slate-400">
                <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                Telefon kayıtlı değil
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Actions */}
      {(primaryAction || showCancel) && (
        <section
          aria-label="Sipariş aksiyonları"
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <CheckCircle2 className="h-4 w-4 text-slate-400" aria-hidden="true" />
              <span>Bu sipariş için kullanılabilir aksiyonlar</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {showCancel && (
                <OrderActionButton
                  variant="destructive"
                  label="İptal et"
                  message={`#${order.id} numaralı sipariş iptal işlemi yakında aktif olacak.`}
                  icon="cancel"
                />
              )}
              {primaryAction && (
                <OrderActionButton
                  variant="primary"
                  label={primaryAction.label}
                  message={`#${order.id}: "${primaryAction.label}" yakında aktif olacak.`}
                />
              )}
            </div>
          </div>
        </section>
      )}

      {/* Items + Shipment */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <section
          aria-labelledby="items-heading"
          className="rounded-xl border border-slate-200 bg-white shadow-sm"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-slate-400" aria-hidden="true" />
              <h2
                id="items-heading"
                className="text-sm font-semibold text-slate-800"
              >
                Sipariş Kalemleri
              </h2>
            </div>
            <span className="text-xs text-slate-500 tabular-nums">
              {itemCount} satır
            </span>
          </div>
          <div className="px-5 pb-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="py-2 text-left">
                    Ürün
                  </th>
                  <th scope="col" className="py-2 text-right">
                    Miktar
                  </th>
                  <th scope="col" className="py-2 text-right">
                    Birim
                  </th>
                  <th scope="col" className="py-2 text-right">
                    Toplam
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {order.items.map((it: any) => (
                  <tr key={it.id} className="odd:bg-slate-50/60">
                    <td className="py-2.5 pl-2 font-medium text-slate-800">
                      {it.product_name}
                    </td>
                    <td className="py-2.5 pr-1 text-right text-slate-700 tabular-nums">
                      {it.quantity}
                    </td>
                    <td className="py-2.5 pr-1 text-right text-slate-700 tabular-nums">
                      {formatTRY(it.unit_price)}
                    </td>
                    <td className="py-2.5 pr-2 text-right font-medium text-slate-900 tabular-nums">
                      {formatTRY(it.quantity * it.unit_price)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-slate-200">
                  <td
                    colSpan={3}
                    className="py-3 pl-2 text-right text-sm font-medium text-slate-600"
                  >
                    Toplam
                  </td>
                  <td className="py-3 pr-2 text-right text-base font-bold text-slate-900 tabular-nums">
                    {formatTRY(order.total)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </section>

        <section
          aria-labelledby="shipment-heading"
          className="rounded-xl border border-slate-200 bg-white shadow-sm"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <div className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-slate-400" aria-hidden="true" />
              <h2
                id="shipment-heading"
                className="text-sm font-semibold text-slate-800"
              >
                Kargo Durumu
              </h2>
            </div>
            {order.shipment?.tracking_no && (
              <span className="font-mono text-xs text-slate-500 tabular-nums">
                {order.shipment.tracking_no}
              </span>
            )}
          </div>
          <div className="p-5">
            <ShipmentTimeline shipment={order.shipment} />
          </div>
        </section>
      </div>

      {/* Notes */}
      {order.note && (
        <section
          aria-labelledby="note-heading"
          className="rounded-xl border border-amber-200 bg-amber-50/60 p-5 shadow-sm"
        >
          <div className="flex items-start gap-3">
            <span
              aria-hidden="true"
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700"
            >
              <StickyNote className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <h3
                id="note-heading"
                className="text-sm font-semibold text-amber-900"
              >
                Not
              </h3>
              <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-amber-900/90">
                {order.note}
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
