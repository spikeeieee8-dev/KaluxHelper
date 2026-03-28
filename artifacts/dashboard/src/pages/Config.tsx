import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Save, Settings, Shield, Bell, Hash, Check, X } from "lucide-react";

interface Config {
  prefix: string; ticket_staff_role_id: string | null; ticket_log_channel_id: string | null;
  automod_banned_words: string; automod_filter_links: number; automod_max_mentions: number;
  log_channel_id: string | null;
}

export default function Config() {
  const { user } = useAuth();
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<Partial<Config>>({});

  useEffect(() => {
    api.get<Config>("/config").then(c => { setConfig(c); setForm(c); }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setError(""); setSaved(false);
    try {
      await api.patch("/config", form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) { setError(err.message); }
    finally { setSaving(false); }
  };

  const isAdmin = user?.role === "admin";

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold">Bot Configuration</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          {isAdmin ? "Manage bot settings" : "View bot settings (admin only to edit)"}
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        {error && (
          <div className="px-4 py-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
            <X className="w-4 h-4 flex-shrink-0" /> {error}
          </div>
        )}
        {saved && (
          <div className="px-4 py-3 rounded-lg bg-chart-2/10 border border-chart-2/20 text-chart-2 text-sm flex items-center gap-2">
            <Check className="w-4 h-4 flex-shrink-0" /> Settings saved successfully
          </div>
        )}

        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            <Settings className="w-4 h-4" /> General
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Command Prefix</label>
            <input value={form.prefix || ""} onChange={e => setForm(f => ({ ...f, prefix: e.target.value }))}
              placeholder="!" maxLength={5} disabled={!isAdmin}
              className="w-32 px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
            <p className="text-xs text-muted-foreground mt-1">Max 5 characters</p>
          </div>
        </div>

        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            <Hash className="w-4 h-4" /> Tickets
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Staff Role ID</label>
            <input value={form.ticket_staff_role_id || ""} onChange={e => setForm(f => ({ ...f, ticket_staff_role_id: e.target.value || null }))}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Log Channel ID</label>
            <input value={form.ticket_log_channel_id || ""} onChange={e => setForm(f => ({ ...f, ticket_log_channel_id: e.target.value || null }))}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
          </div>
        </div>

        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            <Shield className="w-4 h-4" /> AutoMod
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Banned Words (comma-separated)</label>
            <textarea value={form.automod_banned_words || ""} onChange={e => setForm(f => ({ ...f, automod_banned_words: e.target.value }))}
              rows={3} placeholder="word1, word2, word3" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none disabled:opacity-60" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Max Mentions</label>
              <input type="number" value={form.automod_max_mentions || 5} min={1} max={50}
                onChange={e => setForm(f => ({ ...f, automod_max_mentions: parseInt(e.target.value) }))}
                disabled={!isAdmin}
                className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-3 cursor-pointer">
                <div className="relative">
                  <input type="checkbox" checked={!!form.automod_filter_links} disabled={!isAdmin}
                    onChange={e => setForm(f => ({ ...f, automod_filter_links: e.target.checked ? 1 : 0 }))}
                    className="sr-only peer" />
                  <div className="w-10 h-6 rounded-full bg-muted peer-checked:bg-primary transition-colors" />
                  <div className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
                </div>
                <span className="text-sm font-medium">Filter Links</span>
              </label>
            </div>
          </div>
        </div>

        <div className="bg-card border border-card-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
            <Bell className="w-4 h-4" /> Logs
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Log Channel ID</label>
            <input value={form.log_channel_id || ""} onChange={e => setForm(f => ({ ...f, log_channel_id: e.target.value || null }))}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
          </div>
        </div>

        {isAdmin && (
          <div className="flex justify-end">
            <button type="submit" disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-sm transition disabled:opacity-50">
              <Save className="w-4 h-4" />
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
