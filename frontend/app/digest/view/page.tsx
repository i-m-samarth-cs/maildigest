"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, ExternalLink, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { emailApi, DigestResponse, EmailSummary } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatEmailDate, formatFullDate } from "@/lib/utils";

const CATEGORY_BG: Record<string, string> = {
  jobs:         "bg-blue-50 border-blue-200",
  competitions: "bg-purple-50 border-purple-200",
  tech:         "bg-green-50 border-green-200",
  reddit:       "bg-orange-50 border-orange-200",
  newsletters:  "bg-yellow-50 border-yellow-200",
  college:      "bg-teal-50 border-teal-200",
  personal:     "bg-pink-50 border-pink-200",
  other:        "bg-gray-50 border-gray-200",
};

const CATEGORY_ACCENT: Record<string, string> = {
  jobs:         "border-blue-500 text-blue-700 bg-blue-50",
  competitions: "border-purple-500 text-purple-700 bg-purple-50",
  tech:         "border-green-500 text-green-700 bg-green-50",
  reddit:       "border-orange-500 text-orange-700 bg-orange-50",
  newsletters:  "border-yellow-500 text-yellow-700 bg-yellow-50",
  college:      "border-teal-500 text-teal-700 bg-teal-50",
  personal:     "border-pink-500 text-pink-700 bg-pink-50",
  other:        "border-gray-400 text-gray-700 bg-gray-50",
};

function EmailCard({ email }: { email: EmailSummary }) {
  const [expanded, setExpanded] = useState(false);
  const cat = email.ai_analysis?.category ?? "other";
  const priority = email.ai_analysis?.priority;

  return (
    <div className={`border rounded-xl overflow-hidden transition-shadow hover:shadow-md ${CATEGORY_BG[cat] ?? CATEGORY_BG.other}`}>
      {/* Card header */}
      <div
        className="flex items-start gap-3 p-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Unread dot */}
        <div className="mt-1.5 shrink-0">
          {!email.is_read
            ? <div className="w-2 h-2 rounded-full bg-brand-500" />
            : <div className="w-2 h-2 rounded-full bg-transparent" />}
        </div>

        <div className="flex-1 min-w-0">
          {/* Sender + date */}
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="font-semibold text-sm text-gray-900 truncate">{email.sender_name || email.sender_email}</span>
            <span className="text-xs text-gray-400 shrink-0">{formatEmailDate(email.received_at)}</span>
          </div>

          {/* Subject */}
          <p className="text-sm font-medium text-gray-800 truncate mb-1">{email.subject ?? "(no subject)"}</p>

          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}`}>
              {CATEGORY_LABELS[cat] ?? cat}
            </span>
            {priority === "high" && (
              <span className="inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-medium bg-red-100 text-red-700">
                <AlertCircle size={9} /> High priority
              </span>
            )}
            {email.ai_analysis?.action_required && (
              <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium bg-amber-100 text-amber-700">
                Action needed
              </span>
            )}
          </div>

          {/* AI summary (always visible if present) */}
          {email.ai_analysis?.summary && !expanded && (
            <p className="mt-2 text-xs text-gray-500 line-clamp-2">{email.ai_analysis.summary}</p>
          )}
        </div>

        <button className="shrink-0 text-gray-400 hover:text-gray-600 mt-0.5">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Expanded body */}
      {expanded && (
        <div className="border-t border-current border-opacity-10 px-4 pb-4 pt-3 space-y-3">
          {/* Full meta */}
          <div className="text-xs text-gray-500 space-y-0.5">
            <div><span className="font-medium text-gray-700">From:</span> {email.sender_name ? `${email.sender_name} <${email.sender_email}>` : email.sender_email}</div>
            <div><span className="font-medium text-gray-700">Date:</span> {formatFullDate(email.received_at)}</div>
          </div>

          {/* AI summary */}
          {email.ai_analysis?.summary && (
            <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-current border-opacity-10">
              <p className="text-xs font-semibold text-brand-600 mb-1">✦ AI Summary</p>
              <p className="text-sm text-gray-700 leading-relaxed">{email.ai_analysis.summary}</p>
              {email.ai_analysis.keywords?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {email.ai_analysis.keywords.map((k) => (
                    <span key={k} className="text-[10px] bg-white border rounded-full px-2 py-0.5 text-gray-500">{k}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Snippet */}
          {email.snippet && (
            <p className="text-sm text-gray-600 leading-relaxed">{email.snippet}</p>
          )}

          {/* Open original */}
          {email.provider_url && (
            <a
              href={email.provider_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-600 hover:text-brand-700 hover:underline"
            >
              <ExternalLink size={12} />
              Open in {email.account?.provider === "gmail" ? "Gmail" : "Outlook"}
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default function DigestViewPage() {
  const router = useRouter();
  const today = new Date().toISOString().slice(0, 10);

  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await emailApi.getDigest({ date: today, page_size: "200" });
      setDigest(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [today]);

  useEffect(() => { load(); }, [load]);

  async function handleSync() {
    const { accountApi } = await import("@/lib/api");
    setSyncing(true);
    try {
      const accounts = await accountApi.list();
      await Promise.allSettled(accounts.map((a) => accountApi.sync(a.id)));
      await load();
    } finally {
      setSyncing(false);
    }
  }

  const emails = digest?.emails ?? [];
  const stats = digest?.stats ?? {};

  // Build category tabs from actual data
  const tabs = [
    { key: "all", label: "All", count: digest?.total ?? 0 },
    ...Object.entries(stats)
      .sort((a, b) => b[1] - a[1])
      .map(([cat, count]) => ({ key: cat, label: CATEGORY_LABELS[cat] ?? cat, count })),
  ];

  const visibleEmails = activeTab === "all"
    ? emails
    : emails.filter((e) => (e.ai_analysis?.category ?? "other") === activeTab);

  const formattedDate = new Date(today + "T12:00:00").toLocaleDateString("en-IN", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Top navbar */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft size={15} />
              Back
            </button>
            <div className="h-4 w-px bg-gray-200" />
            <span className="text-base font-bold text-brand-500">MailDigest</span>
          </div>

          <div className="text-center hidden sm:block">
            <h1 className="text-sm font-semibold text-gray-900">{formattedDate}</h1>
            <p className="text-xs text-gray-400">{digest?.total ?? 0} emails</p>
          </div>

          <button
            onClick={handleSync}
            disabled={syncing || loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={13} className={syncing ? "animate-spin" : ""} />
            {syncing ? "Syncing…" : "Sync"}
          </button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        {/* Category tab bar */}
        <div className="flex gap-2 overflow-x-auto pb-1 mb-6 scrollbar-hide">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                activeTab === tab.key
                  ? tab.key === "all"
                    ? "bg-gray-900 text-white border-gray-900"
                    : `border-2 ${CATEGORY_ACCENT[tab.key] ?? CATEGORY_ACCENT.other}`
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
              }`}
            >
              {tab.label}
              <span className={`text-xs font-bold rounded-full px-1.5 py-0.5 ${
                activeTab === tab.key ? "bg-white bg-opacity-30" : "bg-gray-100 text-gray-500"
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Email grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 text-gray-400 gap-3">
            <RefreshCw size={24} className="animate-spin" />
            <p className="text-sm">Loading your digest…</p>
          </div>
        ) : visibleEmails.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-gray-400 gap-2">
            <p className="text-lg">📭</p>
            <p className="text-sm font-medium">No emails in this category</p>
            <p className="text-xs">Try syncing or switch to a different tab</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {visibleEmails.map((email) => (
              <EmailCard key={email.id} email={email} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
