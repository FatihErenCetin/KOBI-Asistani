import type { ComponentType, ReactNode } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  ClipboardList,
  Truck,
  Package,
  AlertTriangle,
  ArrowUpRight,
} from "lucide-react";
import { formatTRY } from "@/lib/format";

interface Summary {
  orders_last_24h: number;
  revenue_last_24h: number;
  orders_vs_yesterday_pct: number;
  pending_to_prepare: number;
  urgent_today: number;
  shipments_today: number;
  low_stock_count: number;
}

function DeltaPill({ pct }: { pct: number }) {
  const up = pct >= 0;
  const Icon = up ? TrendingUp : TrendingDown;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium tabular-nums ${
        up
          ? "bg-emerald-50 text-emerald-700"
          : "bg-rose-50 text-rose-700"
      }`}
    >
      <Icon className="h-3 w-3" aria-hidden="true" />
      <span>
        {up ? "+" : "−"}%{Math.abs(pct).toFixed(1)}
      </span>
      <span className="sr-only">{up ? "artış" : "düşüş"}</span>
    </span>
  );
}

function CardShell({
  href,
  label,
  ariaUrgent,
  accentBar,
  children,
}: {
  href: string;
  label: string;
  ariaUrgent?: boolean;
  accentBar?: "none" | "amber" | "emerald" | "rose" | "slate";
  children: ReactNode;
}) {
  const bar =
    accentBar === "amber"
      ? "before:bg-amber-400"
      : accentBar === "emerald"
      ? "before:bg-emerald-500"
      : accentBar === "rose"
      ? "before:bg-rose-400"
      : accentBar === "slate"
      ? "before:bg-slate-300"
      : "before:bg-transparent";

  return (
    <Link
      href={href}
      aria-label={label}
      aria-current={ariaUrgent ? "true" : undefined}
      className={`group relative flex h-full flex-col overflow-hidden rounded-xl border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white
        before:absolute before:left-0 before:top-0 before:h-full before:w-1 ${bar}`}
    >
      {children}
    </Link>
  );
}

function CardHeader({
  icon: Icon,
  title,
  tone = "slate",
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  tone?: "slate" | "emerald" | "amber" | "rose";
}) {
  const tones: Record<string, string> = {
    slate: "bg-slate-100 text-slate-600",
    emerald: "bg-brand-50 text-brand-700",
    amber: "bg-amber-100 text-amber-700",
    rose: "bg-rose-100 text-rose-700",
  };
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex h-8 w-8 items-center justify-center rounded-lg ${tones[tone]}`}
        >
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
        <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-slate-500">
          {title}
        </span>
      </div>
      <ArrowUpRight
        className="h-4 w-4 text-slate-300 transition group-hover:text-slate-500"
        aria-hidden="true"
      />
    </div>
  );
}

export function SummaryCards({ summary }: { summary: Summary }) {
  const urgent = summary.urgent_today > 0;
  const lowStock = summary.low_stock_count > 0;

  // Düşük stok için görsel sinyal — kaç ürün eşik altında (0-5+ skalası)
  const lowStockMax = Math.max(5, summary.low_stock_count);
  const lowStockPct = Math.min(
    100,
    Math.round((summary.low_stock_count / lowStockMax) * 100)
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {/* 1) Son 24 saat — gelir + delta */}
      <CardShell
        href="/orders"
        label="Son 24 saat — sipariş listesine git"
        accentBar="emerald"
      >
        <CardHeader icon={ClipboardList} title="Son 24 saat" tone="emerald" />
        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-3xl font-semibold tracking-tight text-slate-900 tabular-nums">
            {summary.orders_last_24h}
          </span>
          <span className="text-sm font-medium text-slate-500">sipariş</span>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <p className="text-sm font-medium text-slate-700 tabular-nums">
            {formatTRY(summary.revenue_last_24h)}
          </p>
          <DeltaPill pct={summary.orders_vs_yesterday_pct} />
        </div>
        <p className="mt-2 text-xs text-slate-500">Dünle karşılaştırma</p>
      </CardShell>

      {/* 2) Hazırlanacak — urgent ise dikkat çekici */}
      <CardShell
        href="/orders?status=pending"
        label={
          urgent
            ? `Hazırlanacak siparişler — ${summary.urgent_today} acil`
            : "Hazırlanacak siparişler"
        }
        ariaUrgent={urgent}
        accentBar={urgent ? "amber" : "slate"}
      >
        <CardHeader
          icon={Package}
          title="Hazırlanacak"
          tone={urgent ? "amber" : "slate"}
        />
        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-3xl font-semibold tracking-tight text-slate-900 tabular-nums">
            {summary.pending_to_prepare}
          </span>
          <span className="text-sm font-medium text-slate-500">sipariş</span>
        </div>
        {urgent ? (
          <div className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-200">
            <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="tabular-nums">{summary.urgent_today}</span>
            <span>acil bugün</span>
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-600">Bugün için acil yok</p>
        )}
        <p className="mt-2 text-xs text-slate-500">
          Listeyi açmak için tıklayın
        </p>
      </CardShell>

      {/* 3) Bugün teslim */}
      <CardShell
        href="/orders?status=shipped"
        label="Bugün teslim edilecek kargolar"
        accentBar="slate"
      >
        <CardHeader icon={Truck} title="Bugün teslim" tone="slate" />
        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-3xl font-semibold tracking-tight text-slate-900 tabular-nums">
            {summary.shipments_today}
          </span>
          <span className="text-sm font-medium text-slate-500">kargo</span>
        </div>
        <p className="mt-3 text-sm text-slate-700">
          {summary.shipments_today > 0
            ? "Yolda olan teslimatlar"
            : "Bugün planlı kargo yok"}
        </p>
        <p className="mt-2 text-xs text-slate-500">Kargo durumlarını görün</p>
      </CardShell>

      {/* 4) Düşük stok — mini progress + sayı */}
      <CardShell
        href="/products?low=1"
        label={
          lowStock
            ? `Düşük stok — ${summary.low_stock_count} ürün eşik altında`
            : "Stok durumu"
        }
        ariaUrgent={lowStock}
        accentBar={lowStock ? "rose" : "slate"}
      >
        <CardHeader
          icon={AlertTriangle}
          title="Düşük stok"
          tone={lowStock ? "rose" : "emerald"}
        />
        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-3xl font-semibold tracking-tight text-slate-900 tabular-nums">
            {summary.low_stock_count}
          </span>
          <span className="text-sm font-medium text-slate-500">
            {lowStock ? "ürün eşik altında" : "ürün"}
          </span>
        </div>
        <div className="mt-3">
          <div
            className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={lowStockMax}
            aria-valuenow={summary.low_stock_count}
            aria-label="Eşik altı ürün oranı"
          >
            <div
              className={`h-full rounded-full transition-all ${
                lowStock ? "bg-rose-400" : "bg-emerald-400"
              }`}
              style={{ width: `${Math.max(lowStock ? 8 : 100, lowStockPct)}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-slate-500">
            {lowStock ? "Stoku tamamlamayı planlayın" : "Tüm ürünler iyi durumda"}
          </p>
        </div>
      </CardShell>
    </div>
  );
}