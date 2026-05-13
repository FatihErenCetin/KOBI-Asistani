"use client";

import {
  ArrowDown,
  ArrowUp,
  DollarSign,
  Pencil,
  PieChart as PieChartIcon,
  Plus,
  Receipt,
  TrendingDown,
  TrendingUp,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  CATEGORIES,
  ExpenseFormModal,
} from "@/components/finance/ExpenseFormModal";
import { api } from "@/lib/api";
import { formatDateTime, formatTRY } from "@/lib/format";

const CATEGORY_LABELS: Record<string, string> = Object.fromEntries(
  CATEGORIES.map((c) => [c.value, c.label]),
);

const PIE_COLORS = [
  "#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#64748b",
];

interface Summary {
  revenue: number;
  cogs: number;
  gross_profit: number;
  operating_expenses: number;
  net_profit: number;
  gross_margin_pct: number;
  net_margin_pct: number;
  prev_revenue: number;
  prev_net_profit: number;
  revenue_change_pct: number | null;
  net_profit_change_pct: number | null;
}

export default function FinancePage() {
  const [periodDays, setPeriodDays] = useState(30);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [trend, setTrend] = useState<any[]>([]);
  const [breakdown, setBreakdown] = useState<any[]>([]);
  const [topProducts, setTopProducts] = useState<any[]>([]);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [s, t, b, tp, ex] = await Promise.all([
        api.financeSummary(periodDays),
        api.financeMonthlyTrend(6),
        api.financeCategoryBreakdown(periodDays),
        api.financeTopProducts(periodDays, 8),
        api.listExpenses({ since_days: periodDays, limit: 50 }),
      ]);
      setSummary(s);
      setTrend(t);
      setBreakdown(b);
      setTopProducts(tp);
      setExpenses(ex);
    } finally {
      setLoading(false);
    }
  }, [periodDays]);

  useEffect(() => {
    reload();
  }, [reload]);

  async function deleteExpense(e: any) {
    if (!confirm(`"${CATEGORY_LABELS[e.category]} - ${e.amount} TL" silinsin mi?`))
      return;
    await api.deleteExpense(e.id);
    reload();
  }

  return (
    <div className="max-w-7xl space-y-5">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <DollarSign className="h-6 w-6 text-emerald-600" />
            Finansal Analiz
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Kâr/zarar, gider analizi, aylık trend ve en kârlı ürünler.
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90, 180].map((d) => (
            <button
              key={d}
              onClick={() => setPeriodDays(d)}
              className={`px-3 py-1 text-sm rounded border ${
                periodDays === d
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white border-slate-300"
              }`}
            >
              {d} gün
            </button>
          ))}
          <button
            onClick={() => {
              setEditing(null);
              setModalOpen(true);
            }}
            className="ml-2 inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> Yeni Gider
          </button>
        </div>
      </header>

      {loading && (
        <p className="text-sm text-slate-500">Yükleniyor…</p>
      )}

      {summary && (
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <SummaryCard
            label="Gelir"
            value={formatTRY(summary.revenue)}
            delta={summary.revenue_change_pct}
            positive
          />
          <SummaryCard
            label="Satılan Mal Maliyeti (COGS)"
            value={formatTRY(summary.cogs)}
            sub={`Brüt marj %${summary.gross_margin_pct}`}
          />
          <SummaryCard
            label="Operasyonel Giderler"
            value={formatTRY(summary.operating_expenses)}
            sub={`${expenses.length} kayıt`}
          />
          <SummaryCard
            label="Net Kâr"
            value={formatTRY(summary.net_profit)}
            delta={summary.net_profit_change_pct}
            positive={summary.net_profit >= 0}
            sub={`Net marj %${summary.net_margin_pct}`}
            big
          />
        </section>
      )}

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-5">
          <header className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-brand-600" />
            <h2 className="font-semibold">Aylık Trend (6 ay)</h2>
          </header>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickFormatter={(v) =>
                    v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v
                  }
                />
                <Tooltip
                  formatter={(v: number) => formatTRY(v)}
                  contentStyle={{ fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="revenue" fill="#10b981" name="Gelir" />
                <Bar dataKey="cogs" fill="#f59e0b" name="COGS" />
                <Bar dataKey="opex" fill="#ef4444" name="Gider" />
                <Bar dataKey="net" fill="#3b82f6" name="Net Kâr" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <header className="flex items-center gap-2 mb-3">
            <PieChartIcon className="h-4 w-4 text-brand-600" />
            <h2 className="font-semibold">Gider Kategorileri</h2>
          </header>
          <div className="h-64">
            {breakdown.length === 0 ? (
              <p className="text-sm text-slate-500 mt-4">Gider kaydı yok.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={breakdown}
                    dataKey="total"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    label={(e: any) =>
                      `${CATEGORY_LABELS[e.category] ?? e.category}`
                    }
                    labelLine={false}
                    fontSize={10}
                  >
                    {breakdown.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v: number, name: string) => [
                      formatTRY(v),
                      CATEGORY_LABELS[name] ?? name,
                    ]}
                    contentStyle={{ fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <ul className="text-xs space-y-1 mt-2">
            {breakdown.slice(0, 5).map((b, i) => (
              <li key={b.category} className="flex justify-between">
                <span className="inline-flex items-center gap-1.5">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                  />
                  {CATEGORY_LABELS[b.category] ?? b.category}
                </span>
                <span className="text-slate-600">
                  {formatTRY(b.total)} (%{b.share_pct})
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {topProducts.length > 0 && (
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <header className="px-5 py-3 border-b border-slate-200 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-600" />
            <h2 className="font-semibold">En Kârlı Ürünler ({periodDays} gün)</h2>
          </header>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-600">
              <tr>
                <th className="text-left px-4 py-2">Ürün</th>
                <th className="text-right px-4 py-2">Satılan</th>
                <th className="text-right px-4 py-2">Gelir</th>
                <th className="text-right px-4 py-2">COGS</th>
                <th className="text-right px-4 py-2">Brüt Kâr</th>
                <th className="text-right px-4 py-2">Marj</th>
              </tr>
            </thead>
            <tbody>
              {topProducts.map((p) => (
                <tr key={p.product_id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-medium">{p.name}</td>
                  <td className="px-4 py-2 text-right">
                    {p.units_sold} {p.unit}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {formatTRY(p.revenue)}
                  </td>
                  <td className="px-4 py-2 text-right text-slate-500">
                    {formatTRY(p.cogs)}
                  </td>
                  <td className="px-4 py-2 text-right font-medium text-emerald-700">
                    {formatTRY(p.gross_profit)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        p.gross_margin_pct < 15
                          ? "bg-rose-100 text-rose-700"
                          : p.gross_margin_pct < 30
                            ? "bg-amber-100 text-amber-700"
                            : "bg-emerald-100 text-emerald-700"
                      }`}
                    >
                      %{p.gross_margin_pct}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <header className="px-5 py-3 border-b border-slate-200 flex items-center gap-2">
          <Receipt className="h-4 w-4 text-slate-600" />
          <h2 className="font-semibold">Gider Kayıtları ({periodDays} gün)</h2>
        </header>
        {expenses.length === 0 ? (
          <p className="text-sm text-slate-500 p-5">Bu aralıkta gider yok.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-600">
              <tr>
                <th className="text-left px-4 py-2">Kategori</th>
                <th className="text-left px-4 py-2">Tedarikçi/Kurum</th>
                <th className="text-left px-4 py-2">Açıklama</th>
                <th className="text-right px-4 py-2">Tutar</th>
                <th className="text-left px-4 py-2">Tarih</th>
                <th className="text-right px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((e) => (
                <tr
                  key={e.id}
                  className="border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-4 py-2">
                    <span className="inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {CATEGORY_LABELS[e.category] ?? e.category}
                    </span>
                    {e.is_recurring && (
                      <span
                        className="ml-1.5 text-[10px] text-violet-600"
                        title="Aylık tekrar eden"
                      >
                        🔁
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-slate-600">
                    {e.vendor ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-slate-600 text-xs">
                    {e.description ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-right font-medium">
                    {formatTRY(e.amount)}
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500">
                    {formatDateTime(e.incurred_at)}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    <button
                      onClick={() => {
                        setEditing(e);
                        setModalOpen(true);
                      }}
                      className="p-1.5 text-slate-500 hover:text-brand-700 hover:bg-brand-50 rounded"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => deleteExpense(e)}
                      className="p-1.5 text-slate-500 hover:text-rose-700 hover:bg-rose-50 rounded ml-1"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <ExpenseFormModal
        open={modalOpen}
        expense={editing}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSaved={reload}
      />
    </div>
  );
}

function SummaryCard({
  label,
  value,
  sub,
  delta,
  positive,
  big,
}: {
  label: string;
  value: string;
  sub?: string;
  delta?: number | null;
  positive?: boolean;
  big?: boolean;
}) {
  return (
    <div
      className={`bg-white border rounded-lg p-4 ${
        big
          ? positive
            ? "border-emerald-300"
            : "border-rose-300"
          : "border-slate-200"
      }`}
    >
      <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
      <p
        className={`mt-1 font-semibold ${
          big
            ? positive
              ? "text-emerald-700 text-2xl"
              : "text-rose-700 text-2xl"
            : "text-xl"
        }`}
      >
        {value}
      </p>
      {delta != null && (
        <p className="text-xs mt-1 inline-flex items-center gap-0.5">
          {delta >= 0 ? (
            <ArrowUp className="h-3 w-3 text-emerald-600" />
          ) : (
            <ArrowDown className="h-3 w-3 text-rose-600" />
          )}
          <span
            className={delta >= 0 ? "text-emerald-700" : "text-rose-700"}
          >
            %{Math.abs(delta).toFixed(1)} önceki döneme göre
          </span>
        </p>
      )}
      {sub && !delta && (
        <p className="text-xs text-slate-500 mt-1">{sub}</p>
      )}
    </div>
  );
}
