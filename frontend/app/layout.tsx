import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { AuthGuard } from "@/components/AuthGuard";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "MailDigest",
  description: "Your personal daily email digest",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen flex overflow-hidden bg-gray-50 text-gray-900">
        <AuthProvider>
          <AuthGuard>
            <AppShell>{children}</AppShell>
          </AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
