"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";

const OPERATIONS = [
  { value: "percent_increase", label: "Yüzde artır (+%)" },
  { value: "percent_decrease", label: "Yüzde azalt (−%)" },
  { value: "set_absolute", label: "Sabit değere ata (TL)" },
];

export function BulkPriceModal({
  open,
  onClose,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [operation, setOperation] = useState("percent_increase");
  const [target, setTarget] = useState<"price" | "cost">("price");
  const [value, setValue] = useState<number>(0);
  const [category, setCategory] = useState("");
  const [namePattern, setNamePattern] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<number | null>(null);

  useEffect(() => {
    if (open) {
      setOperation("percent_increase");
      setTarget("price");
      setValue(0);
      setCategory("");
      setNamePattern("");
      setReason("");
      setError(null);
      setDone(null);
    }
  }, [open]);

  async function submit() {
    setError(null);
    if (!reason.trim()) {
      setError("Sebep zorunlu — fiyat geçmişine yazılacak.");
      return;
    }
    if (value === 0) {
      setError("Değer 0 olamaz.");
      return;
    }
    setBusy(true);
    try {
      const r = await api.bulkPriceUpdate({
        operation: operation as any,
        target,
        value,
        category: category || undefined,
        name_pattern: namePattern || undefined,
        reason,
      });
      setDone(r.updated);
      onSaved();
    } catch (e: any) {
      setError(e?.message ?? "Hata");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Toplu Fiyat / Maliyet Güncelle">
      <div className="space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-slate-600 mb-1">Hedef</label>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value as "price" | "cost")}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            >
              <option value="price">Satış fiyatı</option>
              <option value="cost">Maliyet</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">İşlem</label>
            <select
              value={operation}
              onChange={(e) => setOperation(e.target.value)}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            >
              {OPERATIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="col-span-2">
            <label className="block text-xs text-slate-600 mb-1">
              Değer (
              {operation === "set_absolute" ? "TL" : "% — örn. 10 = +%10"})
            </label>
            <input
              type="number"
              step="0.01"
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
        </div>

        <p className="text-xs text-slate-500 font-medium pt-2">
          Filtre (boş bırakırsanız tüm aktif ürünler etkilenir):
        </p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-slate-600 mb-1">
              Kategori
            </label>
            <input
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="ör: Gida"
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">
              İsim deseni (ILIKE)
            </label>
            <input
              value={namePattern}
              onChange={(e) => setNamePattern(e.target.value)}
              placeholder="ör: bal"
              className="w-full border border-slate-300 rounded px-3 py-1.5"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-slate-600 mb-1">
            Sebep *{" "}
            <span className="text-slate-400">
              (fiyat geçmişinde görünür)
            </span>
          </label>
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="ör: Tedarikçi zammı"
            className="w-full border border-slate-300 rounded px-3 py-1.5"
          />
        </div>

        {error && (
          <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
            {error}
          </p>
        )}
        {done !== null && (
          <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
            ✓ {done} ürün güncellendi.
          </p>
        )}
      </div>

      <footer className="mt-5 flex justify-end gap-2">
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm rounded border border-slate-300"
        >
          Kapat
        </button>
        <button
          onClick={submit}
          disabled={busy}
          className="px-3 py-1.5 text-sm rounded bg-brand-600 text-white disabled:opacity-50 inline-flex items-center gap-1.5"
        >
          {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Uygula
        </button>
      </footer>
    </Modal>
  );
}
