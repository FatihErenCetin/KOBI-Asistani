"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";

const CATEGORIES = [
  { value: "rent", label: "Kira" },
  { value: "salaries", label: "Maaşlar" },
  { value: "utilities", label: "Faturalar (elektrik/su/internet)" },
  { value: "marketing", label: "Reklam / Pazarlama" },
  { value: "logistics", label: "Lojistik / Kargo" },
  { value: "maintenance", label: "Bakım / Onarım" },
  { value: "tax", label: "Vergi" },
  { value: "supplies", label: "Ofis Malzemeleri" },
  { value: "insurance", label: "Sigorta" },
  { value: "other", label: "Diğer" },
];

export function ExpenseFormModal({
  open,
  expense,
  onClose,
  onSaved,
}: {
  open: boolean;
  expense?: any;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!expense?.id;
  const [form, setForm] = useState<any>({
    category: "other",
    amount: "",
    vendor: "",
    description: "",
    incurred_at: "",
    is_recurring: false,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(
        expense
          ? {
              category: expense.category,
              amount: expense.amount,
              vendor: expense.vendor ?? "",
              description: expense.description ?? "",
              incurred_at: expense.incurred_at?.slice(0, 10) ?? "",
              is_recurring: expense.is_recurring,
            }
          : {
              category: "other",
              amount: "",
              vendor: "",
              description: "",
              incurred_at: new Date().toISOString().slice(0, 10),
              is_recurring: false,
            },
      );
      setError(null);
    }
  }, [open, expense]);

  async function submit() {
    setError(null);
    const amt = Number(form.amount);
    if (!form.category || !amt || amt <= 0) {
      setError("Kategori ve geçerli bir tutar gerekli.");
      return;
    }
    setBusy(true);
    try {
      const payload: any = {
        category: form.category,
        amount: amt,
        vendor: form.vendor || null,
        description: form.description || null,
        is_recurring: !!form.is_recurring,
      };
      if (form.incurred_at) {
        payload.incurred_at = new Date(form.incurred_at).toISOString();
      }
      if (isEdit) {
        await api.updateExpense(expense.id, payload);
      } else {
        await api.createExpense(payload);
      }
      onSaved();
      onClose();
    } catch (e: any) {
      setError(e?.message ?? "Kayıt başarısız");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? "Gideri Düzenle" : "Yeni Gider Ekle"}
      size="md"
    >
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="col-span-2">
          <label className="block text-xs text-slate-600 mb-1">Kategori *</label>
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            className="w-full border border-slate-300 rounded px-3 py-1.5"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-600 mb-1">Tutar (TL) *</label>
          <input
            type="number"
            step="0.01"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            className="w-full border border-slate-300 rounded px-3 py-1.5"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-600 mb-1">Tarih</label>
          <input
            type="date"
            value={form.incurred_at}
            onChange={(e) => setForm({ ...form, incurred_at: e.target.value })}
            className="w-full border border-slate-300 rounded px-3 py-1.5"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-slate-600 mb-1">
            Tedarikçi / Kurum
          </label>
          <input
            value={form.vendor}
            onChange={(e) => setForm({ ...form, vendor: e.target.value })}
            placeholder="ör: BEDAŞ, ev sahibi, kargo firması"
            className="w-full border border-slate-300 rounded px-3 py-1.5"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-slate-600 mb-1">Açıklama</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2}
            className="w-full border border-slate-300 rounded px-3 py-1.5"
          />
        </div>
        <label className="col-span-2 inline-flex items-center text-sm">
          <input
            type="checkbox"
            checked={form.is_recurring}
            onChange={(e) =>
              setForm({ ...form, is_recurring: e.target.checked })
            }
            className="mr-2"
          />
          Aylık tekrar eden gider
        </label>
      </div>
      {error && (
        <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2 mt-3">
          {error}
        </p>
      )}
      <footer className="mt-4 flex justify-end gap-2">
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm rounded border border-slate-300"
        >
          Vazgeç
        </button>
        <button
          onClick={submit}
          disabled={busy}
          className="px-3 py-1.5 text-sm rounded bg-brand-600 text-white disabled:opacity-50 inline-flex items-center gap-1.5"
        >
          {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Kaydet
        </button>
      </footer>
    </Modal>
  );
}

export { CATEGORIES };
