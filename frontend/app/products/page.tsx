import { api } from "@/lib/api";
import { formatTRY } from "@/lib/format";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: { low?: string };
}) {
  const products = await api.listProducts({ low_stock_only: searchParams.low === "1" });
  return (
    <div className="max-w-6xl space-y-5">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Ürünler & Stok</h1>
        <div className="text-sm flex gap-2">
          <a
            className={`px-3 py-1 rounded border ${
              !searchParams.low
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white border-slate-300"
            }`}
            href="/products"
          >
            Tümü
          </a>
          <a
            className={`px-3 py-1 rounded border ${
              searchParams.low
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white border-slate-300"
            }`}
            href="/products?low=1"
          >
            Düşük Stok
          </a>
        </div>
      </header>
      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ürün</th>
            <th className="text-left px-4 py-2">Birim</th>
            <th className="text-right px-4 py-2">Stok</th>
            <th className="text-right px-4 py-2">Eşik</th>
            <th className="text-right px-4 py-2">Fiyat</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p: any) => (
            <tr
              key={p.id}
              className={`border-t border-slate-100 ${p.is_low ? "bg-rose-50" : ""}`}
            >
              <td className="px-4 py-2">{p.name}</td>
              <td className="px-4 py-2">{p.unit}</td>
              <td className="px-4 py-2 text-right font-medium">{p.stock}</td>
              <td className="px-4 py-2 text-right text-slate-500">{p.low_stock_threshold}</td>
              <td className="px-4 py-2 text-right">{formatTRY(p.price)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
