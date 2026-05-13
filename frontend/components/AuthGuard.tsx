"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";

const PUBLIC_PATHS = ["/login", "/register"];

function isPublic(pathname: string | null): boolean {
  if (!pathname) return false;
  // Landing page herkese açık; PUBLIC_PATHS startsWith eşleşmesi "/"'da
  // tüm route'lara yayılacağı için exact match olarak ele alıyoruz.
  if (pathname === "/") return true;
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

function FullPageLoader({ label }: { label: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center gap-3 text-slate-500">
        <Loader2
          className="h-6 w-6 animate-spin text-brand-500"
          aria-hidden="true"
        />
        <p className="text-sm font-medium" aria-live="polite">
          {label}
        </p>
      </div>
    </div>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const onPublicRoute = isPublic(pathname);

  useEffect(() => {
    if (isLoading) return;
    if (onPublicRoute) return;
    if (!user) {
      router.replace("/login");
    }
  }, [isLoading, onPublicRoute, user, router]);

  // Public route — render as-is (e.g. /login)
  if (onPublicRoute) {
    return <>{children}</>;
  }

  // Hydrating from localStorage
  if (isLoading) {
    return <FullPageLoader label="Oturum kontrol ediliyor…" />;
  }

  // Will redirect; render nothing in the meantime
  if (!user) {
    return <FullPageLoader label="Giriş sayfasına yönlendiriliyor…" />;
  }

  return <>{children}</>;
}
