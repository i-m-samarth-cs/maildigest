import { format, isToday, isYesterday, parseISO } from "date-fns";
import clsx, { ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatEmailDate(iso: string): string {
  const d = parseISO(iso);
  if (isToday(d)) return format(d, "h:mm a");
  if (isYesterday(d)) return "Yesterday";
  return format(d, "MMM d");
}

export function formatFullDate(iso: string): string {
  return format(parseISO(iso), "EEEE, MMMM d, yyyy 'at' h:mm a");
}

export const CATEGORY_LABELS: Record<string, string> = {
  jobs: "Jobs",
  competitions: "Competitions",
  tech: "Tech",
  reddit: "Reddit",
  newsletters: "Newsletters",
  college: "College",
  personal: "Personal",
  other: "Other",
};

export const CATEGORY_COLORS: Record<string, string> = {
  jobs:         "bg-blue-100 text-blue-800",
  competitions: "bg-purple-100 text-purple-800",
  tech:         "bg-green-100 text-green-800",
  reddit:       "bg-orange-100 text-orange-800",
  newsletters:  "bg-yellow-100 text-yellow-800",
  college:      "bg-teal-100 text-teal-800",
  personal:     "bg-pink-100 text-pink-800",
  other:        "bg-gray-100 text-gray-700",
};

export const PRIORITY_COLORS: Record<string, string> = {
  high:   "text-red-600",
  medium: "text-yellow-600",
  low:    "text-gray-400",
};

export function providerIcon(provider: string): string {
  return provider === "gmail" ? "G" : "O";
}

export function providerColor(provider: string): string {
  return provider === "gmail"
    ? "bg-red-100 text-red-700"
    : "bg-blue-100 text-blue-700";
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
