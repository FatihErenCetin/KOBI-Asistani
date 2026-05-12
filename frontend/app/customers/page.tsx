import Link from "next/link";

import { api } from "@/lib/api";

export default async function CustomersPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const customers = await api.listCustomers(searchParams.q);
  return (
    <div className="max-w-5xl space-y-5">
      <header>
        <h1 className="text-2xl font-bold">Müşteriler</h1>
        <form method="get" className="mt-2 flex gap-2">
          <input
            name="q"
            defaultValue={searchParams.q ?? ""}
            placeholder="Ad veya telefon"
            className="border border-slate-300 rounded px-3 py-1 text-sm w-64"
          />
          <button className="px-3 py-1 bg-slate-900 text-white rounded text-sm">Ara</button>
        </form>
      </header>
      <table className="w-full bg-white border border-slate-200 rounded-lg overflow-hidden text-sm">
        <thead className="bg-slate-50 text-xs text-slate-600">
          <tr>
            <th className="text-left px-4 py-2">#</th>
            <th className="text-left px-4 py-2">Ad</th>
            <th className="text-left px-4 py-2">Telefon</th>
            <th className="text-left px-4 py-2">Telegram</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((c: any) => (
            <tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-4 py-2">
                <Link href={`/customers/${c.id}`} className="text-brand-700 hover:underline">
                  #{c.id}
                </Link>
              </td>
              <td className="px-4 py-2">{c.name}</td>
              <td className="px-4 py-2 text-slate-600">{c.phone ?? "—"}</td>
              <td className="px-4 py-2 text-slate-600">{c.telegram_user_id ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
