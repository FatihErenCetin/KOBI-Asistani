"use client";

import {
  AlertOctagon,
  Bot,
  Check,
  Clock,
  Loader2,
  MessageSquareWarning,
  Package,
  RefreshCw,
  Truck,
  UserMinus,
  UserX,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

interface Complaint {
  id: number;
  customer_id: number | null;
  telegram_user_id: number | null;
  subject: string;
  description: string | null;
  message_text: string | null;
  risk_score: number;
  signals: string[];
  source: string;
  related_entity_type: string | null;
  related_entity_id: number | null;
  auto_generated: boolean;
  resolved: boolean;
  created_at: string;
}

const SOURCE_META: Record<
  string,
  { label: string; icon: any; color: string }
> = {
  telegram_message: {
    label: "Telegram Mesajı",
    icon: MessageSquareWarning,
    color: "bg-rose-100 text-rose-700",
  },
  shipment_delay: {
    label: "Kargo Gecikmesi",
    icon: Truck,
    color: "bg-amber-100 text-amber-700",
  },
  slow_shipment: {
    label: "Yavaş Kargo",
    icon: Clock,
    color: "bg-amber-100 text-amber-700",
  },
  stale_pending: {
    label: "Bayat Sipariş",
    icon: Package,
    color: "bg-blue-100 text-blue-700",
  },
  repeat_complainer: {
    label: "Tekrarlayan Şikayet",
    icon: UserX,
    color: "bg-rose-100 text-rose-700",
  },
  dormant_customer: {
    label: "Sessizleşen Müşteri",
    icon: UserMinus,
    color: "bg-slate-100 text-slate-700",
  },
};

function relatedLink(c: Complaint): string | null {
  if (!c.related_entity_type || !c.related_entity_id) return null;
  if (c.related_entity_type === "order") return `/orders/${c.related_entity_id}`;
  if (c.related_entity_type === "shipment") return null; // shipment detay sayfası yok; order üzerinden
  if (c.related_entity_type === "customer")
    return `/customers/${c.related_entity_id}`;
  return null;
}

export default function ComplaintsPage() {
  const [rows, setRows] = useState<Complaint[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanReport, setScanReport] = useState<string | null>(null);

  async function reload() {
    setRows(await api.listComplaints());
  }

  useEffect(() => {
    reload();
  }, []);

  async function resolve(id: number) {
    if (!confirm("Bu uyarı çözüldü olarak işaretlensin mi?")) return;
    await api.resolveComplaint(id);
    reload();
  }

  async function scan() {
    setScanning(true);
    setScanReport(null);
    try {
      const r = await api.scanComplaints();
      if (r.total === 0) {
        setScanReport("✓ Yeni risk bulgusu yok.");
      } else {
        const parts: string[] = [];
        if (r.shipment_delay) parts.push(`${r.shipment_delay} gecikmiş kargo`);
        if (r.slow_shipment) parts.push(`${r.slow_shipment} yavaş kargo`);
        if (r.stale_pending) parts.push(`${r.stale_pending} bayat sipariş`);
        if (r.repeat_complainer)
          parts.push(`${r.repeat_complainer} tekrarlayan şikayet`);
        if (r.dormant_customer)
          parts.push(`${r.dormant_customer} sessizleşen müşteri`);
        setScanReport(`✓ ${r.total} yeni bulgu: ${parts.join(", ")}.`);
      }
      reload();
    } catch (e: any) {
      setScanReport(`Hata: ${e?.message ?? "tarama başarısız"}`);
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold inline-flex items-center gap-2">
            <MessageSquareWarning className="h-6 w-6 text-rose-500" />
            Şikayet & Risk Uyarıları
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Telegram mesaj sinyalleri + sistem verisinden otomatik tespit edilen
            riskler. Konu ve açıklamayı AI yazar.
          </p>
        </div>
        <button
          onClick={scan}
          disabled={scanning}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {scanning ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
          Şimdi Tara
        </button>
      </header>

      {scanReport && (
        <p className="text-sm bg-slate-100 border border-slate-200 rounded px-3 py-2">
          {scanReport}
        </p>
      )}

      {rows.length === 0 ? (
        <p className="text-emerald-600 bg-emerald-50 border border-emerald-200 rounded p-4">
          ✓ Açık risk uyarısı yok.
        </p>
      ) : (
        <ul className="space-y-3">
          {rows.map((c) => {
            const meta = SOURCE_META[c.source] ?? SOURCE_META.telegram_message;
            const Icon = meta.icon;
            const link = relatedLink(c);
            return (
              <li
                key={c.id}
                className={`bg-white border rounded-lg p-4 ${
                  c.risk_score >= 0.85
                    ? "border-rose-300"
                    : c.risk_score >= 0.7
                      ? "border-amber-300"
                      : "border-slate-200"
                }`}
              >
                <header className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-start gap-2 flex-1">
                    <AlertOctagon
                      className={`h-4 w-4 mt-0.5 shrink-0 ${
                        c.risk_score >= 0.85
                          ? "text-rose-600"
                          : c.risk_score >= 0.7
                            ? "text-amber-600"
                            : "text-slate-500"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-slate-900 leading-snug">
                        {c.subject}
                      </h3>
                      <div className="flex flex-wrap items-center gap-1.5 mt-1.5 text-xs">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded ${meta.color}`}
                        >
                          <Icon className="h-3 w-3" />
                          {meta.label}
                        </span>
                        {c.auto_generated && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-violet-100 text-violet-700">
                            <Bot className="h-3 w-3" />
                            AI tespiti
                          </span>
                        )}
                        <span className="text-slate-500">
                          Risk %{Math.round(c.risk_score * 100)}
                        </span>
                        <span className="text-slate-400">
                          · {formatDateTime(c.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => resolve(c.id)}
                    className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded border border-slate-300 hover:bg-slate-50"
                  >
                    <Check className="h-3 w-3" /> Çözüldü
                  </button>
                </header>

                {c.description && (
                  <p className="text-sm text-slate-700 mt-2 leading-relaxed">
                    {c.description}
                  </p>
                )}

                {c.message_text && (
                  <p className="text-sm text-slate-600 italic border-l-2 border-slate-300 pl-3 mt-2">
                    "{c.message_text}"
                  </p>
                )}

                <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
                  {c.customer_id && (
                    <Link
                      href={`/customers/${c.customer_id}`}
                      className="text-brand-700 hover:underline"
                    >
                      Müşteri #{c.customer_id}
                    </Link>
                  )}
                  {!c.customer_id && c.telegram_user_id && (
                    <span>TG {c.telegram_user_id}</span>
                  )}
                  {link && (
                    <Link href={link} className="text-brand-700 hover:underline">
                      İlgili kayıt →
                    </Link>
                  )}
                  {c.signals.length > 0 && (
                    <span>
                      Sinyaller:{" "}
                      {c.signals.map((s) => (
                        <span
                          key={s}
                          className="inline-block bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded ml-1"
                        >
                          {s}
                        </span>
                      ))}
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
