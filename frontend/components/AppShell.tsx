"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Users,
  Sparkles,
  LogOut,
} from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";

const NAV = [
  { href: "/", label: "Bugün", icon: LayoutDashboard, exact: true },
  { href: "/orders", label: "Siparişler", icon: ShoppingCart },
  { href: "/products", label: "Ürünler", icon: Package },
  { href: "/customers", label: "Müşteriler", icon: Users },
  { href: "/chat", label: "AI Asistan", icon: Sparkles },
];

function getInitials(name: string): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function UserCard() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="mb-6 rounded-lg border border-slate-700/60 bg-slate-800/60 p-3">
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white"
        >
          {getInitials(user.name)}
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-100">
            {user.name}
          </p>
          <p className="truncate text-[11px] text-slate-400">{user.email}</p>
        </div>
      </div>
      <button
        type="button"
        onClick={logout}
        className="mt-2.5 inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-slate-700 bg-slate-900/60 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition hover:border-rose-500/40 hover:bg-rose-500/10 hover:text-rose-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
        <span>Çıkış</span>
      </button>
    </div>
  );
}

function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-60 shrink-0 flex-col bg-slate-900 p-5 text-slate-100">
      {/* Brand */}
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-2 rounded-md px-1 py-1 -mx-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <span
          aria-hidden="true"
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white"
        >
          <Sparkles className="h-4 w-4" />
        </span>
        <span className="text-base font-bold tracking-tight">
          KOBİ Asistanı
        </span>
      </Link>

      <UserCard />

      <nav aria-label="Ana menü" className="flex flex-col gap-0.5 text-sm">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = item.exact
            ? pathname === item.href
            : pathname === item.href || pathname?.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`group inline-flex items-center gap-2.5 rounded-md px-3 py-2 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                active
                  ? "bg-brand-600/20 text-brand-200"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon
                className={`h-4 w-4 ${
                  active
                    ? "text-brand-300"
                    : "text-slate-400 group-hover:text-slate-200"
                }`}
                aria-hidden="true"
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-6 text-[11px] text-slate-500">
        © {new Date().getFullYear()} KOBİ Asistanı
      </div>
    </aside>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLogin = pathname === "/login" || pathname?.startsWith("/login/");

  if (isLogin) {
    // Login owns the full viewport — no sidebar, no chrome.
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 bg-slate-50 p-8">{children}</main>
    </div>
  );
}
