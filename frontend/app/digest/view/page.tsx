"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, ExternalLink, AlertCircle, ChevronDown, ChevronUp, Star } from "lucide-react";
import { emailApi, accountApi, DigestResponse, EmailSummary } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatEmailDate, formatFullDate } from "@/lib/utils";

/* ── helpers ──────────────────────────────────────────────── */
function decodeHtml(str: string): string {
  if (typeof document === "undefined") return str;
  const txt = document.createElement("textarea");
  txt.innerHTML = str;
  return txt.value;
}

const CAT_PILL: Record<string, string> = {
  jobs:         "bg-blue-100 text-blue-800",
  competitions: "bg-purple-100 text-purple-800",
  tech:         "bg-emerald-100 text-emerald-800",
  reddit:       "bg-orange-100 text-orange-800",
  newsletters:  "bg-yellow-100 text-yellow-800",
  college:      "bg-teal-100 text-teal-800",
  personal:     "bg-pink-100 text-pink-800",
  other:        "bg-gray-100 text-gray-600",
};

const CAT_LEFT: Record<string, string> = {
  jobs:         "border-blue-400",
  competitions: "border-purple-400",
  tech:         "border-emerald-400",
  reddit:       "border-orange-400",
  newsletters:  "border-yellow-400",
  college:      "border-teal-400",
  personal:     "border-pink-400",
  other:        "border-gray-300",
};

const TAB_ACTIVE: Record<string, string> = {
  jobs:         "bg-blue-500 text-white border-blue-500",
  competitions: "bg-purple-500 text-white border-purple-500",
  tech:         "bg-emerald-500 text-white border-emerald-500",
  reddit:       "bg-orange-500 text-white border-orange-500",
  newsletters:  "bg-yellow-500 text-white border-yellow-500",
  college:      "bg-teal-500 text-white border-teal-500",
  personal:     "bg-pink-500 text-white border-pink-500",
  other:        "bg-gray-600 text-white border-gray-600",
  all:          "bg-gray-900 text-white border-gray-900",
};

/* ── EmailCard ─────────────────────────────────────────────── */
function EmailCard({ email }: { email: EmailSummary }) {
  const [open, setOpen] = useState(false);
  const cat = email.ai_analysis?.category ?? "other";
  const ai  = email.ai_analysis;

  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden border-l-4 ${CAT_LEFT[cat] ?? CAT_LEFT.other}`}>

      {/* ── header (always visible) ─────────────────────────── */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left px-5 py-4 flex items-start gap-4 hover:bg-gray-50 transition-colors"
      >
        {/* unread indicator */}
        <span className="mt-2 shrink-0">
          {!email.is_read
            ? <span className="block w-2 h-2 rounded-full bg-blue-500" />
            : <span className="block w-2 h-2 rounded-full bg-gray-200" />}
        </span>

        <div className="flex-1 min-w-0">
          {/* sender + time */}
          <div className="flex items-center justify-between gap-4 mb-0.5">
            <span className="font-semibold text-gray-900 truncate">
              {decodeHtml(email.sender_name || email.sender_email)}
            </span>
            <span className="text-xs text-gray-400 shrink-0 tabular-nums">
              {formatEmailDate(email.received_at)}
            </span>
          </div>

          {/* subject */}
          <p className="text-sm text-gray-700 font-medium truncate mb-2">
            {decodeHtml(email.subject ?? "(no subject)")}
          </p>

          {/* badges */}
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className={`text-[11px] font-semibold rounded-full px-2.5 py-0.5 ${CAT_PILL[cat] ?? CAT_PILL.other}`}>
              {CATEGORY_LABELS[cat] ?? cat}
            </span>
            {ai?.priority === "high" && (
              <span className="text-[11px] font-semibold rounded-full px-2.5 py-0.5 bg-red-100 text-red-700 flex items-center gap-1">
                <AlertCircle size={9} /> High priority
              </span>
            )}
            {ai?.action_required && (
              <span className="text-[11px] font-semibold rounded-full px-2.5 py-0.5 bg-amber-100 text-amber-700">
                Action needed
              </span>
            )}
            {email.is_starred && (
              <Star size={12} className="text-yellow-400 fill-yellow-400" />
            )}
          </div>

          {/* ai summary preview (collapsed) */}
          {!open && ai?.summary && (
            <p className="mt-2 text-xs text-gray-400 line-clamp-1 italic">
              {ai.summary}
            </p>
          )}
        </div>

        <span className="shrink-0 text-gray-300 mt-1">
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {/* ── expanded body ───────────────────────────────────── */}
      {open && (
        <div className="px-5 pb-5 pt-1 border-t border-gray-100 space-y-4">

          {/* meta */}
          <div className="text-xs text-gray-500 space-y-0.5 pt-1">
            <div>
              <span className="font-medium text-gray-700">From: </span>
              {email.sender_name
                ? `${decodeHtml(email.sender_name)} <${email.sender_email}>`
                : email.sender_email}
            </div>
            <div>
              <span className="font-medium text-gray-700">Date: </span>
              {formatFullDate(email.received_at)}
            </div>
          </div>

          {/* AI summary box */}
          {ai?.summary && (
            <div className="rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 p-4">
              <p className="text-xs font-bold text-blue-600 uppercase tracking-wide mb-1.5">✦ AI Summary</p>
              <p className="text-sm text-gray-800 leading-relaxed">{ai.summary}</p>
              {ai.keywords?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {ai.keywords.map((k) => (
                    <span key={k} className="text-[11px] bg-white border border-blue-200 text-blue-600 rounded-full px-2 py-0.5">
                      {k}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* snippet */}
          {email.snippet && (
            <p className="text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-xl px-4 py-3">
              {decodeHtml(email.snippet)}
            </p>
          )}

          {/* open in gmail */}
          {email.provider_url && (
            <a
              href={email.provider_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline"
            >
              <ExternalLink size={13} />
              Open in {email.account?.provider === "gmail" ? "Gmail" : "Outlook"}
            </a>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Page ──────────────────────────────────────────────────── */
export default function DigestViewPage() {
  const router = useRouter();
  const today  = new Date().toISOString().slice(0, 10);

  const [digest,  setDigest]  = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [tab,     setTab]     = useState("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await emailApi.getDigest({ date: today, page_size: "200" });
      setDigest(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [today]);

  useEffect(() => { load(); }, [load]);

  async function handleSync() {
    setSyncing(true);
    try {
      const accounts = await accountApi.list();
      await Promise.allSettled(accounts.map(a => accountApi.sync(a.id)));
      await load();
    } finally { setSyncing(false); }
  }

  const emails  = digest?.emails ?? [];
  const stats   = digest?.stats  ?? {};

  const tabs = [
    { key: "all", label: "All", count: digest?.total ?? 0 },
    ...Object.entries(stats)
      .sort((a, b) => b[1] - a[1])
      .map(([cat, count]) => ({
        key: cat,
        label: CATEGORY_LABELS[cat] ?? cat,
        count,
      })),
  ];

  const visible = tab === "all"
    ? emails
    : emails.filter(e => (e.ai_analysis?.category ?? "other") === tab);

  const dateLabel = new Date(today + "T12:00:00").toLocaleDateString("en-IN", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── sticky header ──────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm">
        <div className="w-full px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={15} /> Back
          </button>

          <div className="text-center flex-1">
            <h1 className="text-sm font-bold text-gray-900 leading-tight">{dateLabel}</h1>
            <p className="text-xs text-gray-400">{digest?.total ?? 0} emails synced</p>
          </div>

          <button
            onClick={handleSync}
            disabled={syncing || loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={13} className={syncing ? "animate-spin" : ""} />
            {syncing ? "Syncing…" : "Sync"}
          </button>
        </div>

        {/* ── tab bar ──────────────────────────────────────── */}
        <div className="w-full px-4 sm:px-8 pb-3 flex gap-2 overflow-x-auto scrollbar-hide">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                tab === t.key
                  ? TAB_ACTIVE[t.key] ?? TAB_ACTIVE.all
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
              }`}
            >
              {t.label}
              <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                tab === t.key ? "bg-white bg-opacity-25" : "bg-gray-100 text-gray-500"
              }`}>
                {t.count}
              </span>
            </button>
          ))}
        </div>
      </header>

      {/* ── content ────────────────────────────────────────── */}
      <main className="w-full px-4 sm:px-8 py-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 text-gray-400 gap-3">
            <RefreshCw size={28} className="animate-spin" />
            <p className="text-sm">Loading your digest…</p>
          </div>
        ) : visible.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-gray-400 gap-2">
            <p className="text-4xl">📭</p>
            <p className="text-base font-semibold text-gray-500 mt-2">No emails here</p>
            <p className="text-sm">Try a different tab or sync your accounts</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {visible.map(email => (
              <EmailCard key={email.id} email={email} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
