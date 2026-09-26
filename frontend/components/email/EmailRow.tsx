"use client";
import { Paperclip, Star } from "lucide-react";
import { EmailSummary } from "@/lib/api";
import { formatEmailDate, CATEGORY_COLORS } from "@/lib/utils";

interface Props {
  email: EmailSummary;
  selected: boolean;
  onClick: () => void;
}

export function EmailRow({ email, selected, onClick }: Props) {
  const cat = email.ai_analysis?.category ?? "other";
  const priority = email.ai_analysis?.priority;

  return (
    <button
      onClick={onClick}
      aria-label={`Open: ${email.subject ?? "(no subject)"}`}
      className={`w-full text-left px-4 py-3 border-b border-gray-100 last:border-0 transition-colors
        ${selected ? "bg-brand-50 border-l-2 border-l-brand-500" : "hover:bg-gray-50"}
        ${!email.is_read ? "bg-blue-50/30" : ""}`}>
      <div className="flex items-start gap-2.5">
        {/* priority dot */}
        <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${
          priority === "high" ? "bg-red-500" : priority === "medium" ? "bg-yellow-400" : "bg-gray-200"
        }`} aria-hidden />

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-1">
            <span className={`text-sm truncate ${!email.is_read ? "font-semibold" : "font-medium"}`}>
              {email.sender_name ?? email.sender_email}
            </span>
            <div className="flex items-center gap-1 shrink-0">
              {email.is_starred && <Star size={11} className="text-yellow-400 fill-yellow-400" />}
              {email.has_attachments && <Paperclip size={11} className="text-gray-400" />}
              <span className="text-xs text-gray-400">{formatEmailDate(email.received_at)}</span>
            </div>
          </div>

          <p className={`text-sm truncate mt-0.5 ${!email.is_read ? "text-gray-900" : "text-gray-500"}`}>
            {email.subject ?? "(no subject)"}
          </p>

          <div className="flex items-center gap-1.5 mt-1">
            <span className={`badge text-[10px] ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}`}>{cat}</span>
            <span className="text-xs text-gray-400 truncate">
              {email.ai_analysis?.summary ?? email.snippet ?? ""}
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}
