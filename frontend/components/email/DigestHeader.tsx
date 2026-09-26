"use client";
import { RefreshCw } from "lucide-react";
import { format, parseISO } from "date-fns";
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
  const d = parseISO(date + "T12:00:00");
  return (
    <div className="card p-5 mb-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h1 className="text-xl font-bold">{format(d, "EEEE, MMMM d")}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} email{total !== 1 ? "s" : ""}</p>
        </div>
        <button onClick={onSync} disabled={syncing} className="btn-ghost disabled:opacity-40" aria-label="Sync all accounts">
          <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
          {syncing ? "Syncing…" : "Sync"}
        </button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(stats)
          .sort((a, b) => b[1] - a[1])
          .map(([cat, count]) => (
            <span key={cat} className={`badge ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}`}>
              {CATEGORY_LABELS[cat] ?? cat}: {count}
            </span>
          ))}
      </div>
    </div>
  );
}
