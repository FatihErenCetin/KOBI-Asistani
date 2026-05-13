"use client";

import { ArrowLeft, Download, FileUp, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { api } from "@/lib/api";

export default function ImportProductsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.importProductsCsv(file);
      setResult(r);
    } catch (e: any) {
      setError(e?.message ?? "Yükleme başarısız");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <header className="flex items-center gap-3">
        <Link
          href="/products"
          className="p-1.5 rounded hover:bg-slate-100"
          aria-label="Geri"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">CSV ile Toplu İçe Aktarım</h1>
          <p className="text-sm text-slate-500">
            Mevcut ürünler isim eşleşmesi ile güncellenir, yenisi oluşturulur.
          </p>
        </div>
      </header>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-semibold mb-2 text-sm">Beklenen kolonlar</h2>
            <p className="text-xs text-slate-600 mb-3">
              <code className="bg-slate-100 px-1.5 py-0.5 rounded">
                name, unit, price, cost, stock, low_stock_threshold, barcode,
                category, aliases, description
              </code>
            </p>
            <p className="text-xs text-slate-500">
              UTF-8 (BOM destekli). İlk satır header zorunlu.{" "}
              <code>name</code> boş olan satırlar atlanır ve{" "}
              <em>skipped</em> listesinde döner. Mevcut ürün isim eşleşmesiyle
              güncellenir.
            </p>
          </div>
          <a
            href="/products-import-template.csv"
            download
            className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded border border-brand-600 text-brand-700 hover:bg-brand-50"
          >
            <Download className="h-3.5 w-3.5" /> Örnek Şablon İndir
          </a>
        </div>
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">
            Excel'de açıp düzenleme ipuçları
          </summary>
          <ul className="list-disc ml-5 mt-2 space-y-1">
            <li>
              Excel'de dosyayı açtıktan sonra "Farklı Kaydet → CSV UTF-8
              (virgülle ayrılmış) (*.csv)" seçeneğini kullanın.
            </li>
            <li>
              Türkçe karakterler için UTF-8 zorunludur; ANSI/Windows-1254
              kullanmayın.
            </li>
            <li>
              <code>aliases</code> alanı virgülle ayrılmış birden fazla isim
              içerebilir; bunu çift tırnak içinde yazın:{" "}
              <code>"çiçek balı,suzme bal"</code>.
            </li>
            <li>
              <code>id</code> kolonu eklerseniz o satırlar id ile bulunur ve
              güncellenir.
            </li>
          </ul>
        </details>
      </section>

      <section className="bg-white border border-slate-200 rounded-lg p-5">
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm mb-4"
        />
        <div className="flex gap-2">
          <button
            onClick={submit}
            disabled={!file || busy}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 text-sm rounded bg-brand-600 text-white disabled:opacity-50"
          >
            {busy ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <FileUp className="h-3.5 w-3.5" />
            )}
            İçe Aktar
          </button>
        </div>
      </section>

      {error && (
        <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
          {error}
        </p>
      )}

      {result && (
        <section className="bg-white border border-slate-200 rounded-lg p-5">
          <h2 className="font-semibold mb-3">Sonuç</h2>
          <ul className="text-sm space-y-1 mb-3">
            <li>
              Toplam satır: <span className="font-medium">{result.total_rows}</span>
            </li>
            <li>
              Oluşturulan:{" "}
              <span className="font-medium text-emerald-700">{result.created}</span>
            </li>
            <li>
              Güncellenen:{" "}
              <span className="font-medium text-blue-700">{result.updated}</span>
            </li>
            <li>
              Atlanan:{" "}
              <span className="font-medium text-amber-700">
                {result.skipped?.length ?? 0}
              </span>
            </li>
          </ul>
          {result.skipped?.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Atlanan satırlar:</p>
              <ul className="text-xs space-y-1 max-h-48 overflow-y-auto">
                {result.skipped.map((s: any, i: number) => (
                  <li key={i} className="text-slate-600">
                    Satır {s.row}: {s.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
