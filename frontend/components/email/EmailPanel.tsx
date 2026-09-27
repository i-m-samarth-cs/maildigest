"use client";
import { useEffect, useState } from "react";
import { X, ExternalLink, Paperclip, AlertCircle } from "lucide-react";
import { emailApi, EmailDetail } from "@/lib/api";
import { formatFullDate, CATEGORY_COLORS, PRIORITY_COLORS, formatFileSize } from "@/lib/utils";

interface Props {
  emailId: string;
  onClose: () => void;
}

export function EmailPanel({ emailId, onClose }: Props) {
  const [email, setEmail] = useState<EmailDetail | null>(null);
  const [html, setHtml] = useState<string | null>(null);
  const [styles, setStyles] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"html" | "text">("html");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setEmail(null);
    setHtml(null);
    setStyles("");
    Promise.all([emailApi.getEmail(emailId), emailApi.getEmailHtml(emailId)])
      .then(([e, h]) => {
        if (!alive) return;
        setEmail(e);
        setHtml((h as any).html);
        setStyles((h as any).styles ?? "");
      })
      .catch(console.error)
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [emailId]);

  if (loading) return <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">Loading…</div>;
  if (!email) return <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">Not found.</div>;

  const cat = email.ai_analysis?.category ?? "other";
  const analysis = email.ai_analysis;

  return (
    <div className="flex flex-col h-full bg-white border-l border-gray-200">
      {/* Top bar */}
      <div className="flex items-start gap-3 p-5 border-b border-gray-100">
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-base leading-snug">{email.subject ?? "(no subject)"}</h2>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            <span className={`badge ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}`}>{cat}</span>
            {analysis?.priority && (
              <span className={`text-xs font-medium ${PRIORITY_COLORS[analysis.priority]}`}>{analysis.priority} priority</span>
            )}
            {analysis?.action_required && (
              <span className="badge bg-red-50 text-red-600">
                <AlertCircle size={10} /> Action needed
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {email.provider_url && (
            <a href={email.provider_url} target="_blank" rel="noopener noreferrer"
              className="btn-ghost text-xs text-gray-500" aria-label="Open in provider">
              <ExternalLink size={13} /> Open original
            </a>
          )}
          <button onClick={onClose} className="btn-ghost p-1.5" aria-label="Close panel">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Meta */}
      <div className="px-5 py-3 border-b border-gray-100 text-xs text-gray-500 space-y-1">
        <div><strong className="text-gray-700">From:</strong> {email.sender_name ? `${email.sender_name} <${email.sender_email}>` : email.sender_email}</div>
        {email.recipients?.length > 0 && <div><strong className="text-gray-700">To:</strong> {email.recipients.join(", ")}</div>}
        {email.cc?.length > 0 && <div><strong className="text-gray-700">CC:</strong> {email.cc.join(", ")}</div>}
        <div><strong className="text-gray-700">Date:</strong> {formatFullDate(email.received_at)}</div>
        <div><strong className="text-gray-700">Account:</strong> {email.account.email_address} ({email.account.provider})</div>
        {email.email_attachments?.length > 0 && (
          <div className="flex items-center gap-1">
            <Paperclip size={11} />
            {email.email_attachments.map((a) => (
              <span key={a.filename} className="bg-gray-100 rounded px-1.5 py-0.5">
                {a.filename} ({formatFileSize(a.size_bytes)})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* AI summary */}
      {analysis?.summary && (
        <div className="mx-5 my-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-xs font-semibold text-brand-600 mb-0.5">AI Summary</p>
          <p className="text-sm text-gray-700">{analysis.summary}</p>
          {analysis.keywords?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {analysis.keywords.map((k) => (
                <span key={k} className="badge bg-white border text-gray-500 text-[10px]">{k}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* View toggle */}
      {html && email.body_text && (
        <div className="flex gap-4 px-5 border-b border-gray-100">
          {(["html", "text"] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)}
              className={`py-2 text-xs font-medium border-b-2 transition-colors ${mode === m ? "border-brand-500 text-brand-600" : "border-transparent text-gray-400 hover:text-gray-700"}`}>
              {m === "html" ? "Formatted" : "Plain text"}
            </button>
          ))}
        </div>
      )}

      {/* Body — HTML is sandboxed, scripts fully blocked */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {mode === "html" && html ? (
          <iframe
            title="Email body"
            sandbox="allow-same-origin"
            srcDoc={`<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src https: data: cid:;">
<style>
  html, body { margin: 0; padding: 0; width: 100% !important; max-width: 100% !important; box-sizing: border-box; }
  body { padding: 16px 20px; font: 14px/1.6 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #111; word-break: break-word; overflow-x: hidden; }
  a { color: #2563eb; }
  img { max-width: 100% !important; width: auto !important; height: auto !important; }
  table { max-width: 100% !important; width: 100% !important; }
  td, th { word-break: break-word; }
</style>
<style>${styles}</style>
</head><body>${html}</body></html>`}
            style={{ flex: 1, width: "100%", border: "none", display: "block", minHeight: "400px" }}
          />
        ) : (
          <pre className="flex-1 p-5 text-sm font-sans whitespace-pre-wrap text-gray-700 leading-relaxed overflow-auto">
            {email.body_text ?? email.snippet ?? "(no content)"}
          </pre>
        )}
      </div>
    </div>
  );
}
