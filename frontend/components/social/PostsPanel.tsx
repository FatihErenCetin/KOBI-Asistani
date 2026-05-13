"use client";

import {
  CheckCircle2,
  Clock,
  Eye,
  ImageIcon,
  Send,
  Sparkles,
  Trash2,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface Asset {
  id: number;
  asset_type: string;
  url: string | null;
  status: string;
  provider: string | null;
}

interface Post {
  id: number;
  title: string | null;
  content: string;
  target_platforms: string[];
  hashtags: string[];
  status: string;
  scheduled_at: string | null;
  published_at: string | null;
  ai_generated: boolean;
  related_product_name: string | null;
  last_error: string | null;
  created_at: string;
  assets: Asset[];
}

function statusPill(status: string) {
  const map: Record<string, { label: string; cls: string; icon: any }> = {
    draft: {
      label: "Taslak",
      cls: "bg-slate-100 text-slate-700",
      icon: Eye,
    },
    scheduled: {
      label: "Planlandı",
      cls: "bg-amber-100 text-amber-700",
      icon: Clock,
    },
    published: {
      label: "Yayında",
      cls: "bg-emerald-100 text-emerald-700",
      icon: CheckCircle2,
    },
    failed: {
      label: "Hata",
      cls: "bg-rose-100 text-rose-700",
      icon: XCircle,
    },
  };
  const cfg = map[status] ?? map.draft;
  const Icon = cfg.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded ${cfg.cls}`}
    >
      <Icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

export function PostsPanel() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [busy, setBusy] = useState<number | null>(null);

  async function reload() {
    setPosts(await api.listSocialPosts(filter || undefined));
  }

  useEffect(() => {
    reload();
  }, [filter]);

  async function genAsset(post: Post, asset_type: "image" | "video") {
    const prompt = prompt_for_post(post);
    if (!prompt) return;
    setBusy(post.id);
    try {
      await api.generateSocialAsset(post.id, { asset_type, prompt });
      await reload();
    } finally {
      setBusy(null);
    }
  }

  async function publish(post: Post) {
    if (!confirm(`"${post.title || post.content.slice(0, 40)}" yayınlansın mı?`))
      return;
    setBusy(post.id);
    try {
      await api.publishSocialPost(post.id);
      await reload();
    } finally {
      setBusy(null);
    }
  }

  async function remove(post: Post) {
    if (!confirm("Post silinsin mi?")) return;
    await api.deleteSocialPost(post.id);
    reload();
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Postlar</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded px-2 py-1"
        >
          <option value="">Tümü</option>
          <option value="draft">Taslak</option>
          <option value="scheduled">Planlandı</option>
          <option value="published">Yayında</option>
          <option value="failed">Hata</option>
        </select>
      </div>

      {posts.length === 0 ? (
        <p className="text-sm text-slate-500 italic">
          Bu durumda post yok. "Yeni Taslak" sekmesinden başlayın.
        </p>
      ) : (
        <ul className="space-y-3">
          {posts.map((p) => (
            <li
              key={p.id}
              className="bg-white border border-slate-200 rounded-lg p-4 space-y-2"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    {statusPill(p.status)}
                    {p.ai_generated && (
                      <span className="inline-flex items-center gap-1 text-[11px] text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                        <Sparkles className="h-3 w-3" /> AI
                      </span>
                    )}
                    {p.target_platforms.map((plat) => (
                      <span
                        key={plat}
                        className="text-[10px] uppercase font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded"
                      >
                        {plat}
                      </span>
                    ))}
                    {p.related_product_name && (
                      <span className="text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        Ürün: {p.related_product_name}
                      </span>
                    )}
                  </div>
                  {p.title && (
                    <p className="font-medium text-slate-800">{p.title}</p>
                  )}
                  <p className="text-sm text-slate-700 whitespace-pre-wrap mt-1">
                    {p.content}
                  </p>
                  {p.hashtags.length > 0 && (
                    <p className="text-xs text-brand-700 mt-2">
                      {p.hashtags.join(" ")}
                    </p>
                  )}
                  {p.last_error && (
                    <p className="text-xs text-rose-700 bg-rose-50 px-2 py-1 rounded mt-2">
                      ⚠ {p.last_error}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => remove(p)}
                  className="text-rose-600 hover:bg-rose-50 p-1 rounded"
                  aria-label="Sil"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {p.assets.length > 0 && (
                <div className="flex gap-2 flex-wrap pt-1">
                  {p.assets.map((a) => (
                    <a
                      key={a.id}
                      href={a.url ?? "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-50"
                      title={a.provider ?? ""}
                    >
                      <ImageIcon className="h-3 w-3" />
                      {a.asset_type} ({a.status})
                    </a>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                <button
                  onClick={() => genAsset(p, "image")}
                  disabled={busy === p.id}
                  className="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-50"
                >
                  <ImageIcon className="h-3 w-3 inline mr-1" /> Görsel Üret
                </button>
                <button
                  onClick={() => genAsset(p, "video")}
                  disabled={busy === p.id}
                  className="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-100 disabled:opacity-50"
                  title="API entegrasyonu olmadan stub döner"
                >
                  Video Üret
                </button>
                {p.status !== "published" && (
                  <button
                    onClick={() => publish(p)}
                    disabled={busy === p.id}
                    className="ml-auto text-xs px-3 py-1 rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
                  >
                    <Send className="h-3 w-3 inline mr-1" /> Yayınla
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function prompt_for_post(post: Post): string | null {
  // Asset üretirken default prompt = post içeriği, kullanıcı isterse override.
  const fallback = `${post.title ?? ""} - ${post.content}`.trim();
  const answer = window.prompt(
    "Görsel/video için açıklama (boş bırakırsan post içeriği kullanılır):",
    fallback.slice(0, 240),
  );
  if (answer === null) return null;
  return answer.trim() || fallback;
}
