import { supabase } from "./supabase";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API}${path}`);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), { headers: await authHeaders() });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PATCH ${path} failed: ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`DELETE ${path} failed: ${res.status}`);
  return res.json();
}

// ── Email API ────────────────────────────────────────────────────────────────

export type DigestStats = Record<string, number>;

export interface EmailSummary {
  id: string;
  account_id: string;
  sender_name: string | null;
  sender_email: string;
  subject: string | null;
  received_at: string;
  snippet: string | null;
  provider_url: string | null;
  has_attachments: boolean;
  is_read: boolean;
  is_starred: boolean;
  ai_analysis: {
    category: string | null;
    summary: string | null;
    priority: string | null;
    action_required: boolean;
    keywords: string[];
  } | null;
  account: {
    provider: string;
    email_address: string;
    display_name: string | null;
  };
}

export interface DigestResponse {
  date: string;
  total: number;
  page: number;
  page_size: number;
  stats: DigestStats;
  emails: EmailSummary[];
}

export interface EmailDetail extends EmailSummary {
  body_text: string | null;
  recipients: string[];
  cc: string[];
  email_attachments: { filename: string; mime_type: string; size_bytes: number }[];
}

export const emailApi = {
  getDigest: (params?: Record<string, string>) =>
    get<DigestResponse>("/emails/digest", params),

  getStats: (params?: Record<string, string>) =>
    get<{ date: string; total: number; stats: DigestStats }>("/emails/digest/stats", params),

  getEmail: (id: string) => get<EmailDetail>(`/emails/${id}`),

  getEmailHtml: (id: string) =>
    get<{ email_id: string; html: string }>(`/emails/${id}/html`),
};

// ── Account API ───────────────────────────────────────────────────────────────

export interface Account {
  id: string;
  provider: "gmail" | "outlook";
  email_address: string;
  display_name: string | null;
  last_sync_at: string | null;
  sync_status: "idle" | "syncing" | "error";
  enabled: boolean;
}

export const accountApi = {
  list: () => get<Account[]>("/accounts"),

  sync: (id: string) => post<{ fetched: number; stored: number }>(`/accounts/${id}/sync`),

  disconnect: (id: string) => del(`/accounts/${id}`),

  startGmailOAuth: () => get<{ url: string }>("/auth/gmail/start"),

  startOutlookOAuth: () => get<{ url: string }>("/auth/outlook/start"),
};

// ── Settings API ──────────────────────────────────────────────────────────────

export interface UserSettings {
  digest_time: string;
  timezone: string;
  ai_enabled: boolean;
  ollama_model: string;
  theme: string;
}

export const settingsApi = {
  get: () => get<UserSettings>("/settings"),
  update: (body: Partial<UserSettings>) => patch<UserSettings>("/settings", body),
};
