"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatTRY } from "@/lib/format";

export function SalesChart({ data }: { data: any }) {
  const rows = data?.rows ?? [];
  if (!Array.isArray(rows) || rows.length === 0) return null;
  const xKey = data?.group_by === "product" ? "product" : "day";

  return (
    <div className="h-72 rounded-2xl border border-slate-200 bg-white p-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
          <XAxis dataKey={xKey} stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${Number(v).toLocaleString("tr-TR")} TL`} />
          <Tooltip
            cursor={{ fill: "rgba(15, 23, 42, 0.04)" }}
            formatter={(v: number) => formatTRY(v)}
            contentStyle={{ borderRadius: 18, borderColor: "#e2e8f0", boxShadow: "0 18px 50px -32px rgba(15,23,42,.45)" }}
          />
          <Bar dataKey="revenue" fill="#059669" radius={[10, 10, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
