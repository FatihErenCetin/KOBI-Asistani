"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { api } from "@/lib/api";

type Mode = "create" | "edit";

interface ProductLike {
  id?: number;
  name?: string;
  unit?: string;
  price?: number;
  cost?: number;
  stock?: number;
  low_stock_threshold?: number;
  aliases?: string | null;
  description?: string | null;
  barcode?: string | null;
  category?: string | null;
}

export function ProductFormModal({
  open,
  mode,
  product,
  onClose,
  onSaved,
}: {
  open: boolean;
  mode: Mode;
  product?: ProductLike;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<ProductLike>({});
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(
        product ?? {
          name: "",
          unit: "kg",
          price: 0,
          cost: 0,
          stock: 0,
          low_stock_threshold: 0,
          aliases: "",
          description: "",
          barcode: "",
          category: "",
        },
      );
      setReason("");
      setError(null);
    }
  }, [open, product]);

  function update<K extends keyof ProductLike>(k: K, v: ProductLike[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit() {
    setError(null);
    if (!form.name || !form.unit || !(Number(form.price) > 0)) {
      setError("İsim, birim ve fiyat zorunludur.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "create") {
        await api.createProduct({
          name: form.name,
          unit: form.unit,
          price: Number(form.price),
          cost: Number(form.cost ?? 0),
          stock: Number(form.stock ?? 0),
          low_stock_threshold: Number(form.low_stock_threshold ?? 0),
          aliases: form.aliases || null,
          description: form.description || null,
          barcode: form.barcode || null,
          category: form.category || null,
        });
      } else if (product?.id) {
        await api.updateProduct(product.id, {
          name: form.name,
          unit: form.unit,
          price: Number(form.price),
          cost: Number(form.cost ?? 0),
          low_stock_threshold: Number(form.low_stock_threshold ?? 0),
          aliases: form.aliases || null,
          description: form.description || null,
          barcode: form.barcode || null,
          category: form.category || null,
          reason: reason || null,
        });
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
      title={mode === "create" ? "Yeni Ürün" : `Düzenle: ${product?.name ?? ""}`}
      size="lg"
    >
      <div className="grid grid-cols-2 gap-3 text-sm">
        <Field
          label="Ad *"
          value={form.name ?? ""}
          onChange={(v) => update("name", v as string)}
        />
        <Field
          label="Birim * (kg/lt/adet)"
          value={form.unit ?? ""}
          onChange={(v) => update("unit", v as string)}
        />
        <Field
          label="Satış Fiyatı (TL) *"
          type="number"
          value={form.price ?? 0}
          onChange={(v) => update("price", v as number)}
        />
        <Field
          label="Maliyet (TL)"
          type="number"
          value={form.cost ?? 0}
          onChange={(v) => update("cost", v as number)}
        />
        {mode === "create" && (
          <Field
            label="Açılış Stoğu"
            type="number"
            value={form.stock ?? 0}
            onChange={(v) => update("stock", v as number)}
          />
        )}
        <Field
          label="Düşük Stok Eşiği"
          type="number"
          value={form.low_stock_threshold ?? 0}
          onChange={(v) => update("low_stock_threshold", v as number)}
        />
        <Field
          label="Kategori"
          value={form.category ?? ""}
          onChange={(v) => update("category", v as string)}
        />
        <Field
          label="Barkod"
          value={form.barcode ?? ""}
          onChange={(v) => update("barcode", v as string)}
        />
        <Field
          label="Diğer adlar (virgüllü)"
          value={form.aliases ?? ""}
          onChange={(v) => update("aliases", v as string)}
          colSpan={2}
        />
        <Field
          label="Açıklama"
          value={form.description ?? ""}
          onChange={(v) => update("description", v as string)}
          colSpan={2}
        />
        {mode === "edit" && (
          <Field
            label="Değişiklik nedeni (opsiyonel)"
            value={reason}
            onChange={(v) => setReason(v as string)}
            colSpan={2}
          />
        )}
      </div>

      {error && (
        <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2 mt-3">
          {error}
        </p>
      )}

      <footer className="mt-5 flex justify-end gap-2">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm rounded border border-slate-300 hover:bg-slate-50"
        >
          Vazgeç
        </button>
        <button
          onClick={submit}
          disabled={busy}
          className="px-4 py-2 text-sm rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 inline-flex items-center gap-1.5"
        >
          {busy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Kaydet
        </button>
      </footer>
    </Modal>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  colSpan = 1,
}: {
  label: string;
  value: string | number;
  onChange: (v: string | number) => void;
  type?: string;
  colSpan?: 1 | 2;
}) {
  return (
    <div className={colSpan === 2 ? "col-span-2" : ""}>
      <label className="block text-xs text-slate-600 mb-1">{label}</label>
      <input
        type={type}
        value={value as any}
        onChange={(e) =>
          onChange(type === "number" ? Number(e.target.value) : e.target.value)
        }
        className="block w-full rounded border border-slate-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
      />
    </div>
  );
}
