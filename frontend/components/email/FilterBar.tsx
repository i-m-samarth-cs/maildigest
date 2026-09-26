"use client";
import { Search, X } from "lucide-react";
import { DigestStats } from "@/lib/api";
import { CATEGORY_LABELS, CATEGORY_COLORS } from "@/lib/utils";

interface Props {
  search: string;
  category: string | null;
  stats: DigestStats;
  onSearch: (v: string) => void;
  onCategory: (v: string | null) => void;
}

export function FilterBar({ search, category, stats, onSearch, onCategory }: Props) {
  return (
    <div className="space-y-2">
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="search"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          placeholder="Search emails…"
          aria-label="Search emails"
          className="w-full pl-8 pr-8 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        {search && (
          <button onClick={() => onSearch("")} aria-label="Clear search"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
            <X size={13} />
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => onCategory(null)}
          className={`badge cursor-pointer transition-opacity ${!category ? "bg-gray-800 text-white" : "bg-gray-100 text-gray-600 opacity-60 hover:opacity-100"}`}>
          All
        </button>
        {Object.entries(stats).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
          <button key={cat}
            onClick={() => onCategory(category === cat ? null : cat)}
            className={`badge cursor-pointer transition-opacity ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other} ${category && category !== cat ? "opacity-40 hover:opacity-80" : ""}`}>
            {CATEGORY_LABELS[cat] ?? cat} {count}
          </button>
        ))}
      </div>
    </div>
  );
}
