"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mail, User, Settings } from "lucide-react";

const NAV = [
  { href: "/digest",            label: "Digest",   Icon: Mail },
  { href: "/settings/accounts", label: "Accounts", Icon: User },
  { href: "/settings",          label: "Settings", Icon: Settings },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-52 shrink-0 bg-white border-r border-gray-200 flex flex-col">
      <div className="px-5 py-5 border-b border-gray-200">
        <span className="text-lg font-bold text-brand-500 tracking-tight">MailDigest</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, Icon }) => {
          const active = path === href || (href !== "/settings" && path.startsWith(href));
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? "bg-brand-50 text-brand-600"
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
              }`}>
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-3 border-t border-gray-200 text-xs text-gray-400">
        {new Date().toLocaleDateString("en-IN", { dateStyle: "medium" })}
      </div>
    </aside>
  );
}
