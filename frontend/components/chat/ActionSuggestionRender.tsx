"use client";

import { Clipboard, CheckCircle2, Mail, Loader2, AlertCircle } from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";

export function ActionSuggestionRender({ data }: { data: any }) {
  const [copied, setCopied] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState<{ to: string; message_id?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const body = String(data?.body ?? "");
  const subject = String(data?.subject ?? data?.title ?? "Tedarik Talebi");
  const canSendMail = data?.action === "supplier_email" && Boolean(body.trim());

  async function copy() {
    try {
      await navigator.clipboard.writeText(body);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  async function sendMail() {
    if (!canSendMail || sending || sent) return;
    setSending(true);
    setError(null);
    try {
      const result = await api.sendSupplierMail({ subject, body });
      setSent({ to: result.to, message_id: result.message_id });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Mail gönderilemedi.";
      setError(msg);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-extrabold text-slate-950">{data?.title ?? "Aksiyon taslağı"}</p>
          <p className="mt-1 text-xs font-medium text-slate-500">
            {data?.description ?? "Kontrol edip ilgili kanaldan gönderebilirsiniz."}
          </p>
          {data?.subject && (
            <p className="mt-2 text-xs font-bold text-slate-600">Konu: {data.subject}</p>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 transition hover:border-brand-200 hover:text-brand-700"
          >
            {copied ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clipboard className="h-3.5 w-3.5" />}
            {copied ? "Kopyalandı" : "Kopyala"}
          </button>

          {canSendMail && (
            <button
              type="button"
              onClick={sendMail}
              disabled={sending || Boolean(sent)}
              className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-extrabold text-white transition ${
                sent ? "bg-emerald-600" : "bg-brand-600 hover:bg-brand-700"
              } disabled:cursor-not-allowed disabled:opacity-80`}
            >
              {sending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : sent ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : (
                <Mail className="h-3.5 w-3.5" />
              )}
              {sending ? "Gönderiliyor" : sent ? "Mail gönderildi" : data?.primaryActionLabel ?? "Onayla ve mail gönder"}
            </button>
          )}
        </div>
      </div>

      <pre className="mt-3 whitespace-pre-wrap rounded-xl bg-white p-3 text-sm font-medium leading-6 text-slate-700 ring-1 ring-slate-200">{body}</pre>

      {sent && (
        <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700">
          Mail gönderildi: {sent.to}{sent.message_id ? ` · ID: ${sent.message_id}` : ""}
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-bold leading-5 text-rose-700">
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
