"use client";
import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const PUBLIC_PATHS = ["/login"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
    if (!session && !isPublic) {
      router.replace("/login");
    }
    if (session && isPublic) {
      router.replace("/digest");
    }
  }, [session, loading, pathname, router]);

  // Show nothing while determining auth state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-sm text-gray-400">Loading…</div>
      </div>
    );
  }

  // Don't render protected content for unauthenticated users
  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  if (!session && !isPublic) return null;

  return <>{children}</>;
}
