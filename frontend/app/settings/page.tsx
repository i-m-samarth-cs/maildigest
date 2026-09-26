"use client";
import { useEffect, useState } from "react";
import { settingsApi, UserSettings } from "@/lib/api";

const TIMEZONES = ["Asia/Kolkata", "UTC", "America/New_York", "America/Los_Angeles", "Europe/London"];
const OLLAMA_MODELS = ["llama3.2", "llama3.1", "mistral", "phi3", "gemma2"];

export default function SettingsPage() {
  const [s, setS] = useState<Partial<UserSettings>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => { settingsApi.get().then(setS); }, []);

  function set(key: keyof UserSettings, val: any) {
    setS((p) => ({ ...p, [key]: val }));
  }

  async function save() {
    setSaving(true);
    await settingsApi.update(s);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="max-w-lg mx-auto p-8 space-y-6">
      <h1 className="text-xl font-bold">Settings</h1>

      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="tz">Timezone</label>
        <select id="tz" value={s.timezone ?? "Asia/Kolkata"} onChange={(e) => set("timezone", e.target.value)}
          className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
          {TIMEZONES.map((t) => <option key={t}>{t}</option>)}
        </select>
      </div>

      <div className="flex items-center justify-between p-4 border rounded-xl">
        <div>
          <p className="text-sm font-medium">AI Classification</p>
          <p className="text-xs text-gray-500 mt-0.5">Local Ollama. Falls back to rule-based if offline.</p>
        </div>
        <input type="checkbox" checked={!!s.ai_enabled} onChange={(e) => set("ai_enabled", e.target.checked)}
          className="w-4 h-4 accent-brand-500" aria-label="Enable AI classification" />
      </div>

      {s.ai_enabled && (
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="model">Ollama Model</label>
          <select id="model" value={s.ollama_model ?? "llama3.2"} onChange={(e) => set("ollama_model", e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
            {OLLAMA_MODELS.map((m) => <option key={m}>{m}</option>)}
          </select>
          <p className="text-xs text-gray-500 mt-1">Run <code className="font-mono bg-gray-100 px-1 rounded">ollama serve</code> before syncing.</p>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button onClick={save} disabled={saving}
          className="px-4 py-2 bg-brand-500 text-white rounded-lg text-sm font-medium hover:bg-brand-600 disabled:opacity-50">
          {saving ? "Saving…" : "Save"}
        </button>
        {saved && <span className="text-sm text-green-600">Saved.</span>}
      </div>
    </div>
  );
}
