"use client";

import { CheckCircle2, XCircle } from "lucide-react";

type Variant = "primary" | "destructive";

interface Props {
  variant: Variant;
  label: string;
  message: string;
  icon?: "cancel";
}

export function OrderActionButton({ variant, label, message, icon }: Props) {
  const handleClick = () => {
    if (typeof window !== "undefined") {
      window.alert(message);
    }
  };

  const base =
    "inline-flex h-10 items-center gap-2 rounded-lg px-4 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2";
  const styles: Record<Variant, string> = {
    primary:
      "bg-brand-600 text-white hover:bg-brand-700 focus-visible:ring-brand-500",
    destructive:
      "border border-rose-200 bg-white text-rose-700 hover:bg-rose-50 focus-visible:ring-rose-400",
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`${base} ${styles[variant]}`}
    >
      {icon === "cancel" ? (
        <XCircle className="h-4 w-4" aria-hidden="true" />
      ) : (
        <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
      )}
      <span>{label}</span>
    </button>
  );
}
