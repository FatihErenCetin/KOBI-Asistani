import Link from "next/link";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KOBİ Asistanı",
  description: "Akıllı KOBİ/Kooperatif Asistanı Paneli",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <div className="min-h-screen flex">
          <aside className="w-56 bg-slate-900 text-slate-100 p-6">
            <h1 className="text-lg font-bold mb-8">KOBİ Asistanı</h1>
            <nav className="flex flex-col gap-3 text-sm">
              <Link className="hover:text-brand-500" href="/">Bugün</Link>
              <Link className="hover:text-brand-500" href="/orders">Siparişler</Link>
              <Link className="hover:text-brand-500" href="/products">Ürünler</Link>
              <Link className="hover:text-brand-500" href="/customers">Müşteriler</Link>
              <Link className="hover:text-brand-500" href="/chat">AI Asistan</Link>
            </nav>
          </aside>
          <main className="flex-1 bg-slate-50 p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
