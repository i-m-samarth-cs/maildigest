"use client";
import { useEffect, useState } from "react";
import { accountApi, Account } from "@/lib/api";
import { RefreshCw, Trash2, CheckCircle, XCircle, Clock } from "lucide-react";
import { formatEmailDate, providerColor } from "@/lib/utils";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    accountApi.list().then(setAccounts).finally(() => setLoading(false));
  }, []);

  async function handleSync(id: string) {
    setSyncing(id);
    try {
      await accountApi.sync(id);
      const updated = await accountApi.list();
      setAccounts(updated);
    } catch (e: any) {
      alert("Sync failed: " + e.message);
    } finally {
      setSyncing(null);
    }
  }

  async function handleDisconnect(id: string, email: string) {
    if (!confirm(`Disconnect ${email}? Stored emails are kept.`)) return;
    await accountApi.disconnect(id);
    setAccounts((p) => p.filter((a) => a.id !== id));
  }

  async function connectGmail() {
    const { url } = await accountApi.startGmailOAuth();
    window.location.href = url;
  }

  async function connectOutlook() {
    const { url } = await accountApi.startOutlookOAuth();
    window.location.href = url;
  }

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-xl font-bold mb-1">Connected Accounts</h1>
      <p className="text-sm text-gray-500 mb-6">MailDigest syncs from these accounts automatically.</p>

      <div className="border rounded-xl divide-y mb-8 bg-white">
        {accounts.length === 0 && (
          <p className="px-5 py-8 text-sm text-gray-400 text-center">No accounts connected yet.</p>
        )}
        {accounts.map((acc) => (
          <div key={acc.id} className="flex items-center gap-4 px-5 py-4">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${providerColor(acc.provider)}`}>
              {acc.provider === "gmail" ? "G" : "O"}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium truncate">{acc.email_address}</span>
                <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5 capitalize">{acc.provider}</span>
              </div>
              <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-400">
                {acc.sync_status === "syncing" && <><Clock size={11} className="animate-spin" /> Syncing…</>}
                {acc.sync_status === "error" && <><XCircle size={11} className="text-red-400" /> Sync error</>}
                {acc.sync_status === "idle" && (
                  <><CheckCircle size={11} className="text-green-400" /> {acc.last_sync_at ? `Last sync: ${formatEmailDate(acc.last_sync_at)}` : "Never synced"}</>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button onClick={() => handleSync(acc.id)} disabled={syncing === acc.id}
                className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900 disabled:opacity-40 px-2 py-1 rounded hover:bg-gray-100"
                aria-label={`Sync ${acc.email_address}`}>
                <RefreshCw size={13} className={syncing === acc.id ? "animate-spin" : ""} />
                Sync
              </button>
              <button onClick={() => handleDisconnect(acc.id, acc.email_address)}
                className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
                aria-label={`Disconnect ${acc.email_address}`}>
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>

      <h2 className="text-sm font-semibold mb-3">Add Account</h2>
      <div className="flex gap-3">
        <button onClick={connectGmail}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 shadow-sm">
          <span className="text-red-600 font-bold">G</span> Connect Gmail
        </button>
        <button onClick={connectOutlook}
          className="flex items-center gap-2 px-4 py-2 bg-[#0078d4] text-white rounded-lg text-sm font-medium hover:bg-[#106ebe] shadow-sm">
          <span className="font-bold">O</span> Connect Outlook
        </button>
      </div>
    </div>
  );
}
