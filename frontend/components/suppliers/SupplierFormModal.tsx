"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";

interface SupplierLike {
  id?: number;
  name?: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  notes?: string | null;
}

export function SupplierFormModal({
  open,
  mode,
  supplier,
  onClose,
  onSaved,
}: {
  open: boolean;
  mode: "create" | "edit";
  supplier?: SupplierLike;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<SupplierLike>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(
        supplier ?? {
          name: "",
          contact_name: "",
          phone: "",
          email: "",
          address: "",
          notes: "",
        },
      );
      setError(null);
    }
  }, [open, supplier]);

  async function submit() {
    if (!form.name) {
      setError("Ad zorunludur.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = {
        name: form.name,
        contact_name: form.contact_name || null,
        phone: form.phone || null,
        email: form.email || null,
        address: form.address || null,
        notes: form.notes || null,
      };
      if (mode === "create") {
        await api.createSupplier(payload);
      } else if (supplier?.id) {
        await api.updateSupplier(supplier.id, payload);
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
      title={mode === "create" ? "Yeni Tedarikçi" : "Düzenle"}
      size="md"
    >
      <div className="grid grid-cols-2 gap-3 text-sm">
        {[
          ["name", "Ad *"],
          ["contact_name", "İletişim kişisi"],
          ["phone", "Telefon"],
          ["email", "E-posta"],
        ].map(([k, l]) => (
          <div key={k}>
            <label className="block text-xs text-slate-600 mb-1">{l}</label>
            <input
              value={(form as any)[k] ?? ""}
              onChange={(e) =>
                setForm({ ...form, [k]: e.target.value } as SupplierLike)
              }
              className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm"
            />
          </div>
        ))}
        <div className="col-span-2">
          <label className="block text-xs text-slate-600 mb-1">Adres</label>
          <input
            value={form.address ?? ""}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
            className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-slate-600 mb-1">Not</label>
          <textarea
            value={form.notes ?? ""}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            rows={2}
            className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm"
          />
        </div>
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
