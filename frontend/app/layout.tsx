"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  LayoutDashboard,
  Package,
  ShoppingBag,
  Sparkles,
  Truck,
  Users,
  Zap,
} from "lucide-react";
import "./globals.css";

const NAV = [
  { href: "/", label: "Bugün", hint: "Operasyon özeti", icon: LayoutDashboard },
  { href: "/orders", label: "Siparişler", hint: "Durum ve takip", icon: ShoppingBag },
  { href: "/products", label: "Ürünler", hint: "Stok yönetimi", icon: Package },
  { href: "/customers", label: "Müşteriler", hint: "Müşteri geçmişi", icon: Users },
  { href: "/carriers", label: "Kargo", hint: "Performans analizi", icon: Truck },
  { href: "/chat", label: "AI Asistan", hint: "Doğal dil paneli", icon: Bot },
];

function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-white/10 bg-ink-950 text-white shadow-2xl lg:flex lg:flex-col">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,.28),transparent_23rem)]" />
      <div className="relative flex h-full flex-col">
        <div className="px-6 pb-5 pt-7">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-500 text-white shadow-glow">
              <Zap className="h-5 w-5" aria-hidden="true" />
            </span>
            <span>
              <span className="block text-lg font-extrabold tracking-tight">KOBİ Asistanı</span>
              <span className="block text-xs font-semibold uppercase tracking-[0.22em] text-brand-300">AI Ops Panel</span>
            </span>
          </Link>
        </div>

        <nav className="relative flex-1 space-y-1 px-4 py-3" aria-label="Ana menü">
          {NAV.map(({ href, label, hint, icon: Icon }) => {
            const active = pathname === href || (href !== "/" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={`group flex items-center gap-3 rounded-2xl px-4 py-3 transition ${
                  active
                    ? "bg-white text-slate-950 shadow-soft"
                    : "text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
              >
                <span
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition ${
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "bg-white/10 text-slate-400 group-hover:bg-white/10 group-hover:text-brand-200"
                  }`}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-bold leading-5">{label}</span>
                  <span className={`block truncate text-xs ${active ? "text-slate-500" : "text-slate-500 group-hover:text-slate-300"}`}>
                    {hint}
                  </span>
                </span>
              </Link>
            );
          })}
        </nav>

        <div className="relative m-4 rounded-3xl border border-white/10 bg-white/10 p-4">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-500/15 text-brand-200 ring-1 ring-brand-400/20">
              <Sparkles className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-bold text-white">Akıllı operasyon paneli</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">
                Sipariş, stok ve müşteri süreçlerini tek ekrandan takip edin.
              </p>
            </div>
          </div>
        </div>

        <div className="relative border-t border-white/10 px-6 py-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          KOBİ Asistanı
        </div>
      </div>
    </aside>
  );
}

function MobileTopbar() {
  const pathname = usePathname();
  const active = NAV.find((item) => pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))) ?? NAV[0];

  return (
    <div className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 px-4 py-3 backdrop-blur lg:hidden">
      <div className="flex items-center justify-between gap-3">
        <Link href="/" className="flex items-center gap-2 font-extrabold text-slate-950">
          <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-brand-600 text-white">
            <Zap className="h-4 w-4" aria-hidden="true" />
          </span>
          KOBİ Asistanı
        </Link>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{active.label}</span>
      </div>
      <nav className="mt-3 flex gap-2 overflow-x-auto pb-1" aria-label="Mobil menü">
        {NAV.map(({ href, label }) => {
          const isActive = active.href === href;
          return (
            <Link key={href} href={href} className={isActive ? "filter-pill filter-pill-active shrink-0" : "filter-pill shrink-0"}>
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <div className="min-h-screen bg-app-radial">
          <MobileTopbar />
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
