"use client";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/ui/Sidebar";

const NO_SHELL_PATHS = ["/login", "/digest/view"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showShell = !NO_SHELL_PATHS.some((p) => pathname.startsWith(p));

  if (!showShell) {
    return <>{children}</>;
  }

  return (
    <>
      <Sidebar />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </>
  );
}
