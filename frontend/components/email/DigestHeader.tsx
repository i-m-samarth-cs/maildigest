"use client";
import { RefreshCw, LayoutGrid } from "lucide-react";
import { format, parseISO } from "date-fns";
import { useRouter } from "next/navigation";
import { DigestStats } from "@/lib/api";
import { CATEGORY_LABELS, CATEGORY_COLORS } from "@/lib/utils";

interface Props {
  date: string;
  total: number;
  stats: DigestStats;
  onSync: () => void;
  syncing: boolean;
}

export function DigestHeader({ date, total, stats, onSync, syncing }: Props) {
  const router = useRouter();
  const d = parseISO(date + "T12:00:00");
  return (
    <div className="card p-5 mb-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h1 className="text-xl font-bold">{format(d, "EEEE, MMMM d")}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} email{total !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onSync} disabled={syncing} className="btn-ghost disabled:opacity-40" aria-label="Sync all accounts">
            <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
            {syncing ? "Syncing…" : "Sync"}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {Object.entries(stats)
          .sort((a, b) => b[1] - a[1])
          .map(([cat, count]) => (
            <span key={cat} className={`badge ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}`}>
              {CATEGORY_LABELS[cat] ?? cat}: {count}
            </span>
          ))}
      </div>
      {total > 0 && (
        <button
          onClick={() => router.push("/digest/view")}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <LayoutGrid size={15} />
          View Full Digest
        </button>
      )}
    </div>
  );
}
