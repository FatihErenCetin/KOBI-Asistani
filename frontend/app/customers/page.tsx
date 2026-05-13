import Link from "next/link";
import { Phone, Search, Users } from "lucide-react";

import { api } from "@/lib/api";

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export default async function CustomersPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const customers = await api.listCustomers(searchParams.q);

  return (
    <div className="page-wrap">
      <header className="surface-card px-7 py-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-bold text-brand-700">
              <Users className="h-3.5 w-3.5" aria-hidden="true" />
              Müşteri merkezi
            </div>
            <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-950">Müşteriler</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Sipariş geçmişine ve iletişim bilgilerine hızlı erişim.
            </p>
          </div>
          <form method="get" className="flex w-full max-w-md items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
            <Search className="ml-2 h-4 w-4 text-slate-400" aria-hidden="true" />
            <input
              name="q"
              defaultValue={searchParams.q ?? ""}
              placeholder="Ad veya telefon ara"
              className="min-w-0 flex-1 border-0 bg-transparent px-1 py-2 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none"
            />
            <button className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white transition hover:bg-brand-700">Ara</button>
          </form>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {customers.map((c: any) => (
          <Link
            key={c.id}
            href={`/customers/${c.id}`}
            className="group rounded-3xl border border-white/70 bg-white/90 p-5 shadow-card transition duration-300 hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-soft"
          >
            <div className="flex items-start gap-4">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-emerald-700 text-sm font-extrabold text-white shadow-glow">
                {initials(c.name)}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-extrabold text-slate-950 group-hover:text-brand-700">{c.name}</p>
                    <p className="mt-1 font-mono text-xs font-bold text-brand-700">#{c.id}</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-500">Detay</span>
                </div>
                <div className="mt-4 space-y-2 text-sm text-slate-500">
                  <p className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-slate-300" aria-hidden="true" />
                    {c.phone ?? "Telefon yok"}
                  </p>
                  <p className="text-xs font-medium text-slate-400">Telegram: {c.telegram_user_id ?? "Bağlı değil"}</p>
                </div>
              </div>
            </div>
          </Link>
        ))}
        {customers.length === 0 && (
          <div className="surface-card col-span-full px-6 py-16 text-center">
            <Users className="mx-auto h-10 w-10 text-slate-300" aria-hidden="true" />
            <p className="mt-3 text-sm font-semibold text-slate-500">Müşteri bulunamadı</p>
          </div>
        )}
      </div>
    </div>
  );
}
