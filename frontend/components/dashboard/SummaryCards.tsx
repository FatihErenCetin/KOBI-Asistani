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

export function SummaryCards({ summary }: { summary: Summary }) {
  const pctSign = summary.orders_vs_yesterday_pct >= 0 ? "▲" : "▼";
  const cards = [
    {
      title: "Son 24 saat",
      main: `${summary.orders_last_24h} sipariş`,
      sub: `${formatTRY(summary.revenue_last_24h)} • ${pctSign} %${Math.abs(summary.orders_vs_yesterday_pct)}`,
      tone: "bg-white",
    },
    {
      title: "Hazırlanacak",
      main: `${summary.pending_to_prepare}`,
      sub: `${summary.urgent_today} acil bugün`,
      tone: summary.urgent_today > 0 ? "bg-amber-50 border-amber-200" : "bg-white",
    },
    {
      title: "Bugün teslim",
      main: `${summary.shipments_today} kargo`,
      sub: "Aktif kargolar",
      tone: "bg-white",
    },
    {
      title: "Düşük stok",
      main: `${summary.low_stock_count}`,
      sub: summary.low_stock_count > 0 ? "Eşik altında" : "Hepsi iyi",
      tone: summary.low_stock_count > 0 ? "bg-rose-50 border-rose-200" : "bg-white",
    },
  ];
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.title} className={`rounded-lg border border-slate-200 p-5 ${c.tone}`}>
          <p className="text-xs uppercase tracking-wider text-slate-500">{c.title}</p>
          <p className="text-2xl font-semibold mt-1">{c.main}</p>
          <p className="text-sm text-slate-600 mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}
