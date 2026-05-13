"use client";

import { Boxes, Pencil, Trash2 } from "lucide-react";
import Link from "next/link";

import { MiniSparkline } from "./MiniSparkline";
import { formatTRY } from "@/lib/format";

interface Product {
  id: number;
  name: string;
  unit: string;
  stock: number;
  low_stock_threshold: number;
  price: number;
  cost: number;
  is_low: boolean;
  profit_margin_pct: number | null;
}

export function ProductRow({
  product,
  onEdit,
  onAdjust,
  onDelete,
}: {
  product: Product;
  onEdit: (p: Product) => void;
  onAdjust: (p: Product) => void;
  onDelete: (p: Product) => void;
}) {
  const margin = product.profit_margin_pct;
  const marginClass =
    margin == null
      ? ""
      : margin < 15
        ? "bg-rose-100 text-rose-700"
        : margin < 30
          ? "bg-amber-100 text-amber-700"
          : "bg-emerald-100 text-emerald-700";

  return (
    <tr
      className={`border-t border-slate-100 ${
        product.is_low ? "bg-rose-50" : ""
      }`}
    >
      <td className="px-4 py-2">
        <Link
          href={`/products/${product.id}`}
          className="text-brand-700 hover:underline font-medium"
        >
          {product.name}
        </Link>
      </td>
      <td className="px-4 py-2 text-xs text-slate-500">{product.unit}</td>
      <td className="px-4 py-2 text-right font-medium">{product.stock}</td>
      <td className="px-4 py-2 text-right text-slate-500">
        {product.low_stock_threshold}
      </td>
      <td className="px-4 py-2 text-right">{formatTRY(product.price)}</td>
      <td className="px-4 py-2 text-right text-xs text-slate-600">
        {product.cost ? formatTRY(product.cost) : "—"}
      </td>
      <td className="px-4 py-2 text-right">
        {margin != null ? (
          <span className={`text-xs px-2 py-0.5 rounded ${marginClass}`}>
            %{margin}
          </span>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        )}
      </td>
      <td className="px-4 py-2">
        <MiniSparkline productId={product.id} />
      </td>
      <td className="px-4 py-2 text-right whitespace-nowrap">
        <button
          onClick={() => onAdjust(product)}
          className="p-1.5 text-slate-500 hover:text-brand-700 hover:bg-brand-50 rounded"
          aria-label="Stok hareketi"
          title="Stok hareketi"
        >
          <Boxes className="h-4 w-4" />
        </button>
        <button
          onClick={() => onEdit(product)}
          className="p-1.5 text-slate-500 hover:text-brand-700 hover:bg-brand-50 rounded ml-1"
          aria-label="Düzenle"
          title="Düzenle"
        >
          <Pencil className="h-4 w-4" />
        </button>
        <button
          onClick={() => onDelete(product)}
          className="p-1.5 text-slate-500 hover:text-rose-700 hover:bg-rose-50 rounded ml-1"
          aria-label="Sil"
          title="Sil"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </td>
    </tr>
  );
}
