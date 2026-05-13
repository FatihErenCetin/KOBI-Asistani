"use client";

import {
  AlertTriangle,
  Bot,
  Calendar,
  Check,
  Database,
  Loader2,
  Sparkles,
  X,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
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

interface LotActionItem {
  id: number;
  action_type: string;
  subject: string;
  description: string;
  suggested_discount_pct: number | null;
  priority: number;
  status: string;
}

const ACTION_META: Record<string, { label: string; emoji: string; color: string }> = {
  discount: { label: "İndirim", emoji: "🏷️", color: "bg-rose-100 text-rose-700" },
  bundle: { label: "Paket", emoji: "📦", color: "bg-purple-100 text-purple-700" },
  waste: { label: "Fire", emoji: "🗑️", color: "bg-slate-200 text-slate-700" },
  notify: { label: "Bildirim", emoji: "📢", color: "bg-blue-100 text-blue-700" },
  delay_reorder: {
    label: "Siparişi Ertele",
    emoji: "⏸️",
    color: "bg-amber-100 text-amber-700",
  },
};

export default function ExpiringPage() {
  const [rows, setRows] = useState<ExpiringLot[]>([]);
  const [days, setDays] = useState(14);
  const [enriching, setEnriching] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeMsg, setAnalyzeMsg] = useState<string | null>(null);
  const [openLot, setOpenLot] = useState<ExpiringLot | null>(null);
  const [lotActions, setLotActions] = useState<LotActionItem[]>([]);
  const [actionsLoading, setActionsLoading] = useState(false);

  async function reload() {
    setRows(await api.expiringLots(days));
  }

  async function analyzeAll() {
    setAnalyzing(true);
    setAnalyzeMsg(null);
    try {
      const r = await api.analyzeExpiringLots(days);
      if (r.actions_created === 0 && r.lots_skipped > 0) {
        setAnalyzeMsg(
          `Mevcut ${r.lots_skipped} lot için zaten öneri var. Yenisini görmek için satırdaki "AI Önerisi"ne tıkla.`,
        );
      } else {
        setAnalyzeMsg(
          `✓ ${r.lots_analyzed} lot için ${r.actions_created} öneri üretildi.${
            r.lots_skipped > 0 ? ` (${r.lots_skipped} mevcuttu, atlandı)` : ""
          }`,
        );
      }
    } catch (e: any) {
      setAnalyzeMsg(`Hata: ${e?.message ?? "analiz başarısız"}`);
    } finally {
      setAnalyzing(false);
    }
  }

  async function openLotActions(lot: ExpiringLot) {
    setOpenLot(lot);
    setActionsLoading(true);
    setLotActions([]);
    try {
      let actions = await api.lotActions(lot.lot_id);
      // Hiç öneri yoksa üret
      if (actions.length === 0) {
        actions = await api.analyzeSingleLot(lot.lot_id);
      }
      setLotActions(actions);
    } catch (e: any) {
      setAnalyzeMsg(`Hata: ${e?.message}`);
    } finally {
      setActionsLoading(false);
    }
  }

  async function applyAction(action_id: number) {
    await api.applyLotAction(action_id);
    if (openLot) await openLotActions(openLot);
  }

  async function dismissAction(action_id: number) {
    await api.dismissLotAction(action_id);
    if (openLot) await openLotActions(openLot);
  }

  useEffect(() => {
    reload();
  }, [days]);

  async function loadDemoData() {
    if (
      !confirm(
        "Demo verilerini yükle?\n\n" +
          "Eksik depolar, çoklu depo dağılımı ve SKT'li lotlar idempotent olarak eklenir. " +
          "Mevcut veriler korunur, bu işlem güvenle birden fazla kez çalıştırılabilir.",
      )
    )
      return;
    setEnriching(true);
    setEnrichMsg(null);
    try {
      const r = await api.enrichDemoData();
      const parts: string[] = [];
      if (r.warehouses_created)
        parts.push(`${r.warehouses_created} yeni depo`);
      if (r.suppliers_created)
        parts.push(`${r.suppliers_created} tedarikçi`);
      if (r.supplier_links_created)
        parts.push(`${r.supplier_links_created} ürün-tedarikçi bağı`);
      if (r.products_split)
        parts.push(`${r.products_split} ürün çoklu depoya dağıtıldı`);
      if (r.lots_created) parts.push(`${r.lots_created} lot`);
      if (r.price_history_rows_created)
        parts.push(`${r.price_history_rows_created} fiyat geçmişi kaydı`);
      setEnrichMsg(
        parts.length === 0
          ? "✓ Tüm demo verileri zaten yüklü."
          : `✓ ${parts.join(", ")} oluşturuldu.`,
      );
      reload();
    } catch (e: any) {
      setEnrichMsg(`Hata: ${e?.message ?? "yükleme başarısız"}`);
    } finally {
      setEnriching(false);
    }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <Calendar className="h-6 w-6 text-amber-500" />
            Yaklaşan Son Kullanma
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Önümüzdeki günlerde son kullanma tarihi gelecek lot'lar.
          </p>
        </div>
        <div className="flex gap-2 items-center flex-wrap">
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
          <button
            onClick={analyzeAll}
            disabled={analyzing}
            className="ml-1 inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
            title="Yaklaşan tüm lot'lar için AI öneri üret"
          >
            {analyzing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            AI ile Toplu Analiz
          </button>
          <button
            onClick={loadDemoData}
            disabled={enriching}
            className="inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded border border-violet-300 text-violet-700 hover:bg-violet-50 disabled:opacity-50"
            title="Eksik demo verisini yükle (depolar, lot'lar, dağılım)"
          >
            {enriching ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Database className="h-3.5 w-3.5" />
            )}
            Demo Veriyi Yükle
          </button>
        </div>
      </header>

      {enrichMsg && (
        <p className="text-sm bg-violet-50 border border-violet-200 text-violet-800 rounded px-3 py-2">
          {enrichMsg}
        </p>
      )}
      {analyzeMsg && (
        <p className="text-sm bg-brand-50 border border-brand-200 text-brand-800 rounded px-3 py-2">
          {analyzeMsg}
        </p>
      )}

      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">Ürün</th>
            <th className="text-left px-4 py-2">Lot No</th>
            <th className="text-right px-4 py-2">Miktar</th>
            <th className="text-left px-4 py-2">SKT</th>
            <th className="text-right px-4 py-2">Kalan Gün</th>
            <th className="text-right px-4 py-2">AI Önerisi</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={6} className="text-center py-10">
                <div className="flex flex-col items-center gap-3 text-slate-500">
                  <Calendar className="h-10 w-10 text-slate-300" />
                  <p>Bu aralıkta süresi yaklaşan lot yok.</p>
                  <p className="text-xs">
                    Henüz hiç ürün lot kaydı oluşturmadıysanız, üst kısımdaki{" "}
                    <strong>"Demo Veriyi Yükle"</strong> butonuyla örnek
                    SKT'li lotlar oluşturabilirsiniz.
                  </p>
                </div>
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
              <td className="px-4 py-2 text-right">
                <button
                  onClick={() => openLotActions(r)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded border border-brand-300 text-brand-700 hover:bg-brand-50"
                >
                  <Sparkles className="h-3 w-3" />
                  Öneri Al
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal
        open={openLot !== null}
        onClose={() => {
          setOpenLot(null);
          setLotActions([]);
        }}
        title={
          openLot
            ? `AI Önerileri: ${openLot.product_name} (${openLot.lot_number})`
            : ""
        }
        size="lg"
      >
        {openLot && (
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm bg-slate-50 border border-slate-200 rounded px-3 py-2">
              <span>
                <strong>{openLot.quantity}</strong> {openLot.product_name.includes("Yumurta") ? "adet" : "kg"}{" "}
                stokta
              </span>
              <span className="text-slate-400">·</span>
              <span
                className={`inline-flex items-center gap-1 font-medium ${
                  openLot.days_left <= 3
                    ? "text-rose-700"
                    : openLot.days_left <= 7
                      ? "text-amber-700"
                      : "text-slate-700"
                }`}
              >
                <Calendar className="h-3.5 w-3.5" />
                {openLot.days_left} gün kaldı ({openLot.expiry_date})
              </span>
            </div>

            {actionsLoading && (
              <div className="flex items-center gap-2 text-sm text-slate-500 py-4">
                <Loader2 className="h-4 w-4 animate-spin" />
                AI öneri üretiyor...
              </div>
            )}

            {!actionsLoading && lotActions.length === 0 && (
              <p className="text-sm text-slate-500">Öneri yok.</p>
            )}

            {!actionsLoading &&
              lotActions.map((a) => {
                const meta = ACTION_META[a.action_type] ?? {
                  label: a.action_type,
                  emoji: "•",
                  color: "bg-slate-100 text-slate-700",
                };
                return (
                  <div
                    key={a.id}
                    className={`border rounded-lg p-3 ${
                      a.status === "applied"
                        ? "border-emerald-300 bg-emerald-50"
                        : a.status === "dismissed"
                          ? "border-slate-200 bg-slate-50 opacity-60"
                          : a.priority === 1
                            ? "border-rose-300"
                            : "border-slate-200"
                    }`}
                  >
                    <header className="flex items-start justify-between gap-3 mb-1.5">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <Bot className="h-4 w-4 text-brand-600 shrink-0" />
                        <h3 className="font-semibold text-slate-900 leading-snug">
                          {a.subject}
                        </h3>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded ${meta.color}`}
                        >
                          {meta.emoji} {meta.label}
                        </span>
                        {a.priority === 1 && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-100 text-rose-700">
                            Acil
                          </span>
                        )}
                      </div>
                    </header>
                    <p className="text-sm text-slate-700 leading-relaxed">
                      {a.description}
                    </p>
                    {a.suggested_discount_pct != null && (
                      <p className="text-xs text-rose-700 font-medium mt-1">
                        Önerilen indirim: %{a.suggested_discount_pct}
                      </p>
                    )}
                    {a.status === "pending" && (
                      <footer className="flex gap-2 mt-2">
                        <button
                          onClick={() => applyAction(a.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
                        >
                          <Check className="h-3 w-3" /> Uygula
                        </button>
                        <button
                          onClick={() => dismissAction(a.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded border border-slate-300 hover:bg-slate-50"
                        >
                          <X className="h-3 w-3" /> Reddet
                        </button>
                      </footer>
                    )}
                    {a.status === "applied" && (
                      <p className="text-xs text-emerald-700 mt-1.5">
                        ✓ Uygulandı
                      </p>
                    )}
                    {a.status === "dismissed" && (
                      <p className="text-xs text-slate-500 mt-1.5">
                        ✗ Reddedildi
                      </p>
                    )}
                  </div>
                );
              })}
          </div>
        )}
      </Modal>
    </div>
  );
}
