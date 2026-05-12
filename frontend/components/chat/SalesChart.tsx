"use client";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatTRY } from "@/lib/format";

export function SalesChart({ data }: { data: any }) {
  const rows = data?.rows ?? [];
  if (!Array.isArray(rows) || rows.length === 0) return null;
  const xKey = data?.group_by === "product" ? "product" : "day";
  const yKey = "revenue";
  return (
    <div className="bg-white border border-slate-200 rounded p-3 mt-2 h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows}>
          <XAxis dataKey={xKey} stroke="#64748b" fontSize={11} />
          <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `${v} TL`} />
          <Tooltip formatter={(v: number) => formatTRY(v)} />
          <Bar dataKey={yKey} fill="#059669" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
