"use client";

import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface Account {
  id: number;
  platform: string;
  handle: string;
  display_name: string | null;
  profile_url: string | null;
  is_active: boolean;
  connected_at: string;
}

const PLATFORMS = [
  { value: "instagram", label: "Instagram" },
  { value: "tiktok", label: "TikTok" },
  { value: "youtube", label: "YouTube" },
  { value: "facebook", label: "Facebook" },
  { value: "twitter", label: "X (Twitter)" },
];

function platformBadge(p: string) {
  const map: Record<string, string> = {
    instagram: "bg-pink-100 text-pink-700",
    tiktok: "bg-slate-900 text-white",
    youtube: "bg-red-100 text-red-700",
    facebook: "bg-blue-100 text-blue-700",
    twitter: "bg-sky-100 text-sky-700",
  };
  return map[p] ?? "bg-slate-100 text-slate-700";
}

export function AccountsPanel() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    platform: "instagram",
    handle: "",
    display_name: "",
    profile_url: "",
  });

  async function reload() {
    setAccounts(await api.listSocialAccounts());
  }

  useEffect(() => {
    reload();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.handle.trim()) return;
    await api.createSocialAccount(form);
    setForm({
      platform: "instagram",
      handle: "",
      display_name: "",
      profile_url: "",
    });
    setOpen(false);
    reload();
  }

  async function remove(a: Account) {
    if (!confirm(`@${a.handle} hesabı silinsin mi?`)) return;
    await api.deleteSocialAccount(a.id);
    reload();
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">
            Bağlı Hesaplar
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Instagram, TikTok, YouTube ve diğer platform hesaplarınızı buradan
            yönetin.
          </p>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> Hesap Ekle
        </button>
      </div>

      {open && (
        <form
          onSubmit={submit}
          className="bg-white border border-slate-200 rounded-lg p-4 space-y-3"
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-600 block mb-1">
                Platform
              </label>
              <select
                value={form.platform}
                onChange={(e) =>
                  setForm({ ...form, platform: e.target.value })
                }
                className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
              >
                {PLATFORMS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">
                Kullanıcı adı (@'siz)
              </label>
              <input
                value={form.handle}
                onChange={(e) => setForm({ ...form, handle: e.target.value })}
                placeholder="kobimarket"
                required
                className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">
                Görünen ad
              </label>
              <input
                value={form.display_name}
                onChange={(e) =>
                  setForm({ ...form, display_name: e.target.value })
                }
                placeholder="KOBİ Market"
                className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">
                Profil URL
              </label>
              <input
                value={form.profile_url}
                onChange={(e) =>
                  setForm({ ...form, profile_url: e.target.value })
                }
                placeholder="https://instagram.com/kobimarket"
                className="w-full border border-slate-300 rounded px-2 py-1.5 text-sm"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="px-3 py-1.5 text-sm rounded border border-slate-300 hover:bg-slate-100"
            >
              İptal
            </button>
            <button
              type="submit"
              className="px-3 py-1.5 text-sm rounded bg-brand-600 text-white hover:bg-brand-700"
            >
              Kaydet
            </button>
          </div>
        </form>
      )}

      {accounts.length === 0 ? (
        <p className="text-sm text-slate-500 italic">
          Henüz hesap eklenmedi. "Hesap Ekle" ile başlayın.
        </p>
      ) : (
        <ul className="bg-white border border-slate-200 rounded-lg divide-y divide-slate-100">
          {accounts.map((a) => (
            <li
              key={a.id}
              className="flex items-center justify-between px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`inline-flex items-center justify-center px-2 py-0.5 text-[10px] font-semibold uppercase rounded ${platformBadge(a.platform)}`}
                >
                  {a.platform}
                </span>
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    @{a.handle}
                  </p>
                  {a.display_name && (
                    <p className="text-xs text-slate-500">{a.display_name}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {a.profile_url && (
                  <a
                    href={a.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-brand-700 hover:underline"
                  >
                    Profil →
                  </a>
                )}
                <button
                  onClick={() => remove(a)}
                  className="text-rose-600 hover:bg-rose-50 p-1 rounded"
                  aria-label="Sil"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
