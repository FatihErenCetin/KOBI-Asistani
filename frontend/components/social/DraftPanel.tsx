"use client";

import { Loader2, Save, Sparkles, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface Template {
  id: string;
  title: string;
  description: string;
  emoji: string;
  prompt_template: string;
}

interface Product {
  id: number;
  name: string;
  unit: string;
  price: number;
}

interface DraftResult {
  title: string;
  content: string;
  hashtags: string[];
  image_prompt: string;
  video_prompt: string;
  suggested_platforms: string[];
}

const PLATFORMS = ["instagram", "tiktok", "youtube", "facebook", "twitter"];

export function DraftPanel({ onSaved }: { onSaved?: () => void }) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [templateId, setTemplateId] = useState<string>("");
  const [productId, setProductId] = useState<string>("");
  const [discountPct, setDiscountPct] = useState<string>("");
  const [prompt, setPrompt] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(["instagram"]);
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState<DraftResult | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.socialTemplates().then(setTemplates);
    api
      .listProducts({})
      .then((rows: any[]) =>
        setProducts(
          rows.map((p) => ({
            id: p.id,
            name: p.name,
            unit: p.unit,
            price: p.price,
          })),
        ),
      );
  }, []);

  function togglePlatform(p: string) {
    setPlatforms((cur) =>
      cur.includes(p) ? cur.filter((x) => x !== p) : [...cur, p],
    );
  }

  async function generate() {
    if (!prompt.trim()) {
      alert("Lütfen ne hakkında post istediğinizi yazın.");
      return;
    }
    setBusy(true);
    setDraft(null);
    try {
      const result = await api.draftSocialPost({
        prompt: prompt.trim(),
        product_id: productId ? Number(productId) : undefined,
        discount_pct: discountPct ? Number(discountPct) : undefined,
        target_platforms: platforms.length > 0 ? platforms : undefined,
        template_id: templateId || undefined,
      });
      setDraft(result);
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (!draft) return;
    setSaving(true);
    try {
      await api.createSocialPost({
        title: draft.title,
        content: draft.content,
        target_platforms: draft.suggested_platforms.length
          ? draft.suggested_platforms
          : platforms,
        hashtags: draft.hashtags,
        related_product_id: productId ? Number(productId) : undefined,
        prompt: prompt.trim(),
      });
      // Reset
      setDraft(null);
      setPrompt("");
      setDiscountPct("");
      setTemplateId("");
      setProductId("");
      onSaved?.();
      alert("Post taslak olarak kaydedildi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">
          Yeni Post Taslağı
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          AI yardımıyla içerik, hashtag, görsel ve video promptu üretir.
        </p>
      </div>

      {/* Şablonlar */}
      {templates.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {templates.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() =>
                setTemplateId((cur) => (cur === t.id ? "" : t.id))
              }
              className={`text-left p-3 rounded-lg border transition ${
                templateId === t.id
                  ? "border-brand-500 bg-brand-50"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <div className="text-xl mb-1">{t.emoji}</div>
              <p className="text-sm font-medium text-slate-800">{t.title}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {t.description}
              </p>
            </button>
          ))}
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
        <div>
          <label className="text-xs text-slate-600 block mb-1">
            Post ne hakkında olsun? <span className="text-rose-600">*</span>
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Örn: Bu hafta sonu reçellerimizde 2 al 1 öde kampanyası..."
            rows={3}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-600 block mb-1">
              İlgili ürün (opsiyonel)
            </label>
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
            >
              <option value="">— Seçilmedi —</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-600 block mb-1">
              İndirim % (opsiyonel)
            </label>
            <input
              type="number"
              min="0"
              max="90"
              value={discountPct}
              onChange={(e) => setDiscountPct(e.target.value)}
              placeholder="örn: 15"
              className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-slate-600 block mb-1">
            Hedef platformlar
          </label>
          <div className="flex flex-wrap gap-2">
            {PLATFORMS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => togglePlatform(p)}
                className={`text-xs px-3 py-1 rounded-full border transition ${
                  platforms.includes(p)
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-slate-300 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={generate}
            disabled={busy || !prompt.trim()}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> AI üretiyor...
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4" /> AI ile Üret
              </>
            )}
          </button>
        </div>
      </div>

      {draft && (
        <div className="bg-white border-2 border-brand-200 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand-600" />
            <h3 className="font-semibold text-slate-800">AI Önerisi</h3>
          </div>
          {draft.title && (
            <div>
              <p className="text-[11px] text-slate-500 uppercase">Başlık</p>
              <p className="text-sm font-medium text-slate-800">
                {draft.title}
              </p>
            </div>
          )}
          <div>
            <p className="text-[11px] text-slate-500 uppercase">İçerik</p>
            <p className="text-sm text-slate-700 whitespace-pre-wrap">
              {draft.content}
            </p>
          </div>
          {draft.hashtags.length > 0 && (
            <div>
              <p className="text-[11px] text-slate-500 uppercase">Hashtag'ler</p>
              <p className="text-sm text-brand-700">
                {draft.hashtags.join(" ")}
              </p>
            </div>
          )}
          {draft.suggested_platforms.length > 0 && (
            <div>
              <p className="text-[11px] text-slate-500 uppercase">
                Önerilen platformlar
              </p>
              <p className="text-sm text-slate-700">
                {draft.suggested_platforms.join(", ")}
              </p>
            </div>
          )}
          {(draft.image_prompt || draft.video_prompt) && (
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
              {draft.image_prompt && (
                <div>
                  <p className="text-[11px] text-slate-500 uppercase">
                    Görsel prompt
                  </p>
                  <p className="text-xs text-slate-700 italic">
                    {draft.image_prompt}
                  </p>
                </div>
              )}
              {draft.video_prompt && (
                <div>
                  <p className="text-[11px] text-slate-500 uppercase">
                    Video prompt
                  </p>
                  <p className="text-xs text-slate-700 italic">
                    {draft.video_prompt}
                  </p>
                </div>
              )}
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => setDraft(null)}
              className="text-sm px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-100"
            >
              Vazgeç
            </button>
            <button
              onClick={save}
              disabled={saving}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Taslak Olarak Kaydet
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
