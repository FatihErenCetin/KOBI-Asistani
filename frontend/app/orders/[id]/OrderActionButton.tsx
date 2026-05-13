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
    window.alert(message);
  };

  const styles: Record<Variant, string> = {
    primary: "bg-brand-600 text-white shadow-sm hover:bg-brand-700 focus-visible:ring-brand-500",
    destructive: "border border-rose-200 bg-white text-rose-700 hover:bg-rose-50 focus-visible:ring-rose-400",
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex h-11 items-center gap-2 rounded-2xl px-4 text-sm font-extrabold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${styles[variant]}`}
    >
      {icon === "cancel" ? <XCircle className="h-4 w-4" aria-hidden="true" /> : <CheckCircle2 className="h-4 w-4" aria-hidden="true" />}
      <span>{label}</span>
    </button>
  );
}
