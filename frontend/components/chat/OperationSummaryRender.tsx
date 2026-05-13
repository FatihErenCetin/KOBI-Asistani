"use client";

import { AlertTriangle, CheckCircle2, ClipboardList, Lightbulb } from "lucide-react";

function toneClass(tone?: string) {
  if (tone === "rose") return "border-rose-100 bg-rose-50 text-rose-700";
  if (tone === "amber") return "border-amber-100 bg-amber-50 text-amber-700";
  return "border-emerald-100 bg-emerald-50 text-emerald-700";
}

function iconFor(tone?: string) {
  if (tone === "rose") return AlertTriangle;
  if (tone === "amber") return ClipboardList;
  return CheckCircle2;
}

export function OperationSummaryRender({ data }: { data: any }) {
  const cards = Array.isArray(data?.cards) ? data.cards : [];
  const actions = Array.isArray(data?.actions) ? data.actions : [];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {cards.map((card: any) => {
          const Icon = iconFor(card.tone);
          return (
            <div key={card.title} className={`rounded-2xl border p-3 ${toneClass(card.tone)}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] font-extrabold uppercase tracking-[0.12em] opacity-80">{card.title}</p>
                <Icon className="h-4 w-4" aria-hidden="true" />
              </div>
              <p className="mt-2 text-2xl font-extrabold tabular-nums">{card.value}</p>
              <p className="mt-1 text-xs font-semibold leading-5 opacity-80">{card.description}</p>
            </div>
          );
        })}
      </div>

      {actions.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center gap-2 text-sm font-extrabold text-slate-950">
            <Lightbulb className="h-4 w-4 text-amber-500" aria-hidden="true" />
            Önerilen aksiyonlar
          </div>
          <ul className="mt-3 space-y-2">
            {actions.map((action: string, index: number) => (
              <li key={`${action}-${index}`} className="flex gap-2 text-sm font-medium leading-6 text-slate-700">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
