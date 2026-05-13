import type { Metadata } from "next";
import "./globals.css";

import { AuthProvider } from "@/contexts/AuthContext";
import { AuthGuard } from "@/components/AuthGuard";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "KOBİ Asistanı",
  description: "Akıllı KOBİ/Kooperatif Asistanı Paneli",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body>
        <AuthProvider>
          <AuthGuard>
            <AppShell>{children}</AppShell>
          </AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
