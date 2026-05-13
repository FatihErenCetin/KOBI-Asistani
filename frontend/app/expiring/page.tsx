"use client";

import { AlertTriangle, Calendar } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface ExpiringLot {
  lot_id: number;
  product_id: number;
  product_name: string;
  lot_number: string;
  expiry_date: string;
  days_left: number;
  quantity: number;
}

export default function ExpiringPage() {
  const [rows, setRows] = useState<ExpiringLot[]>([]);
  const [days, setDays] = useState(14);

  async function reload() {
    setRows(await api.expiringLots(days));
  }

  useEffect(() => {
    reload();
  }, [days]);

  return (
    <div className="max-w-5xl space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <Calendar className="h-6 w-6 text-amber-500" />
            Yaklaşan Son Kullanma
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Önümüzdeki günlerde son kullanma tarihi gelecek lot'lar.
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 14, 30, 60].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded border ${
                days === d
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white border-slate-300"
              }`}
            >
              {d} gün
            </button>
          ))}
        </div>
      </header>

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ürün</th>
            <th className="text-left px-4 py-2">Lot No</th>
            <th className="text-right px-4 py-2">Miktar</th>
            <th className="text-left px-4 py-2">SKT</th>
            <th className="text-right px-4 py-2">Kalan Gün</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="text-center text-slate-500 py-8">
                Bu aralıkta süresi yaklaşan lot yok.
              </td>
            </tr>
          )}
          {rows.map((r) => (
            <tr
              key={r.lot_id}
              className={`border-t border-slate-100 ${
                r.days_left <= 3 ? "bg-rose-50" : r.days_left <= 7 ? "bg-amber-50" : ""
              }`}
            >
              <td className="px-4 py-2">
                <Link
                  href={`/products/${r.product_id}`}
                  className="text-brand-700 hover:underline font-medium"
                >
                  {r.product_name}
                </Link>
              </td>
              <td className="px-4 py-2 text-slate-600">{r.lot_number}</td>
              <td className="px-4 py-2 text-right">{r.quantity}</td>
              <td className="px-4 py-2 text-slate-600">{r.expiry_date}</td>
              <td className="px-4 py-2 text-right">
                <span
                  className={`inline-flex items-center gap-1 font-medium ${
                    r.days_left <= 3
                      ? "text-rose-700"
                      : r.days_left <= 7
                        ? "text-amber-700"
                        : "text-slate-700"
                  }`}
                >
                  {r.days_left <= 7 && <AlertTriangle className="h-3 w-3" />}
                  {r.days_left} gün
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
