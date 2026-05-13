"use client";

import { Megaphone, Users, Wand2 } from "lucide-react";
import { useState } from "react";

import { AccountsPanel } from "@/components/social/AccountsPanel";
import { DraftPanel } from "@/components/social/DraftPanel";
import { PostsPanel } from "@/components/social/PostsPanel";

type Tab = "draft" | "posts" | "accounts";

const TABS: { id: Tab; label: string; icon: any }[] = [
  { id: "draft", label: "Yeni Taslak", icon: Wand2 },
  { id: "posts", label: "Postlar", icon: Megaphone },
  { id: "accounts", label: "Hesaplar", icon: Users },
];

export default function SocialPage() {
  const [tab, setTab] = useState<Tab>("draft");
  // Bump key to force PostsPanel re-mount after a save → reload list.
  const [postsKey, setPostsKey] = useState(0);

  return (
    <div className="max-w-5xl space-y-5">
      <header>
        <h1 className="text-2xl font-bold">Sosyal Medya Yönetimi</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Instagram, TikTok, YouTube hesaplarınız için kampanya, indirim ve
          fırsat postlarını AI yardımıyla hazırlayın.
        </p>
      </header>

      <div className="border-b border-slate-200">
        <nav className="flex gap-1">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => {
                  setTab(t.id);
                  if (t.id === "posts") setPostsKey((k) => k + 1);
                }}
                className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm rounded-t-md border-b-2 transition ${
                  active
                    ? "border-brand-600 text-brand-700 bg-brand-50/50"
                    : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100"
                }`}
              >
                <Icon className="h-4 w-4" />
                {t.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div>
        {tab === "draft" && (
          <DraftPanel
            onSaved={() => {
              setTab("posts");
              setPostsKey((k) => k + 1);
            }}
          />
        )}
        {tab === "posts" && <PostsPanel key={postsKey} />}
        {tab === "accounts" && <AccountsPanel />}
      </div>
    </div>
  );
}
