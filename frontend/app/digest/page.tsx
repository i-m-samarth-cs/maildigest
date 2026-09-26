"use client";
import { useCallback, useEffect, useState } from "react";
import { emailApi, accountApi, DigestResponse } from "@/lib/api";
import { DigestHeader } from "@/components/email/DigestHeader";
import { FilterBar } from "@/components/email/FilterBar";
import { EmailRow } from "@/components/email/EmailRow";
import { EmailPanel } from "@/components/email/EmailPanel";

export default function DigestPage() {
  const today = new Date().toISOString().slice(0, 10);

  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { date: today };
      if (search) params.search = search;
      if (category) params.category = category;
      const data = await emailApi.getDigest(params);
      setDigest(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [today, search, category]);

  useEffect(() => { load(); }, [load]);

  async function handleSync() {
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

  return (
    <div className="flex h-full">
      {/* List column */}
      <div className={`flex flex-col border-r border-gray-200 ${selectedId ? "w-96 shrink-0" : "flex-1"}`}>
        <div className="p-4 border-b border-gray-100 space-y-3">
          <DigestHeader date={today} total={digest?.total ?? 0} stats={stats} onSync={handleSync} syncing={syncing} />
          <FilterBar search={search} category={category} stats={stats} onSearch={setSearch} onCategory={setCategory} />
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading && <div className="flex items-center justify-center h-32 text-sm text-gray-400">Loading…</div>}
          {error && <div className="p-6 text-sm text-red-500">{error} — <button onClick={load} className="underline">retry</button></div>}
          {!loading && !error && emails.length === 0 && (
            <div className="flex flex-col items-center justify-center h-40 text-sm text-gray-400 gap-2">
              {search || category ? "No emails match your filters." : "No emails yet. Hit Sync to fetch."}
            </div>
          )}
          {!loading && emails.map((email) => (
            <EmailRow
              key={email.id}
              email={email}
              selected={email.id === selectedId}
              onClick={() => setSelectedId(selectedId === email.id ? null : email.id)}
            />
          ))}
        </div>

        {digest && digest.total > digest.page_size && (
          <div className="px-4 py-2 border-t text-xs text-gray-400">
            Showing {emails.length} of {digest.total}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selectedId && (
        <div className="flex-1 flex overflow-hidden">
          <EmailPanel emailId={selectedId} onClose={() => setSelectedId(null)} />
        </div>
      )}
    </div>
  );
}
