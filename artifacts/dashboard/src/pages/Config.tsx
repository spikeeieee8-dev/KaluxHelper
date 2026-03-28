import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Save, Settings, Shield, Bell, Hash, Check, X, UserPlus } from "lucide-react";

interface Config {
  prefix: string;
  ticket_staff_role_id: string | null;
  ticket_log_channel_id: string | null;
  automod_banned_words: string;
  automod_filter_links: number;
  automod_max_mentions: number;
  log_channel_id: string | null;
  welcome_enabled: number;
  welcome_channel_id: string | null;
  welcome_message: string;
  welcome_role_id: string | null;
}

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <div className="relative">
        <input type="checkbox" checked={checked} disabled={disabled}
          onChange={e => onChange(e.target.checked)} className="sr-only peer" />
        <div className="w-10 h-6 rounded-full bg-muted peer-checked:bg-primary transition-colors" />
        <div className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
      </div>
    </label>
  );
}

const PLACEHOLDER_HINTS = [
  { tag: "{user}", desc: "Mentions the new member" },
  { tag: "{username}", desc: "Their display name" },
  { tag: "{server}", desc: "Server name" },
  { tag: "{count}", desc: "Current member count" },
];

export default function Config() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [form, setForm] = useState<Partial<Config>>({});

  useEffect(() => {
    api.get<Config>("/config")
      .then(c => setForm(c))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const f = <K extends keyof Config>(key: K) => (val: Config[K] | null | undefined) =>
    setForm(prev => ({ ...prev, [key]: val }));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setSaveError(""); setSaved(false);
    try {
      await api.patch("/config", form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) { setSaveError(err.message); }
    finally { setSaving(false); }
  };

  const isAdmin = user?.role === "admin";

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold">Bot Configuration</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          {isAdmin ? "Manage bot settings" : "View bot settings (admin only to edit)"}
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        {saveError && (
          <div className="px-4 py-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
            <X className="w-4 h-4 flex-shrink-0" /> {saveError}
          </div>
        )}
        {saved && (
          <div className="px-4 py-3 rounded-lg bg-chart-2/10 border border-chart-2/20 text-chart-2 text-sm flex items-center gap-2">
            <Check className="w-4 h-4 flex-shrink-0" /> Settings saved successfully
          </div>
        )}

        {/* General */}
        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            <Settings className="w-4 h-4" /> General
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Command Prefix</label>
            <input value={form.prefix || ""} onChange={e => f("prefix")(e.target.value)}
              placeholder="!" maxLength={5} disabled={!isAdmin}
              className="w-32 px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
            <p className="text-xs text-muted-foreground mt-1">Max 5 characters</p>
          </div>
        </div>

        {/* Welcome */}
        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              <UserPlus className="w-4 h-4" /> Welcome
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{form.welcome_enabled ? "Enabled" : "Disabled"}</span>
              <Toggle
                checked={!!form.welcome_enabled}
                onChange={v => f("welcome_enabled")(v ? 1 : 0)}
                disabled={!isAdmin}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Welcome Channel ID</label>
            <input value={form.welcome_channel_id || ""} onChange={e => f("welcome_channel_id")(e.target.value || null)}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
            <p className="text-xs text-muted-foreground mt-1">Channel where welcome messages are posted</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Auto-Assign Role ID <span className="text-muted-foreground font-normal">(optional)</span></label>
            <input value={form.welcome_role_id || ""} onChange={e => f("welcome_role_id")(e.target.value || null)}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
            <p className="text-xs text-muted-foreground mt-1">Role given to new members automatically on join</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Welcome Message</label>
            <textarea value={form.welcome_message || ""} onChange={e => f("welcome_message")(e.target.value)}
              rows={3} maxLength={500} disabled={!isAdmin}
              placeholder="Welcome to the server, {user}! We're glad to have you."
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none disabled:opacity-60" />
            <div className="mt-2 flex flex-wrap gap-2">
              {PLACEHOLDER_HINTS.map(h => (
                <span key={h.tag} className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-muted rounded-full text-muted-foreground">
                  <code className="font-mono text-primary">{h.tag}</code>
                  <span>— {h.desc}</span>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Tickets */}
        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            <Hash className="w-4 h-4" /> Tickets
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Staff Role ID</label>
            <input value={form.ticket_staff_role_id || ""} onChange={e => f("ticket_staff_role_id")(e.target.value || null)}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Log Channel ID</label>
            <input value={form.ticket_log_channel_id || ""} onChange={e => f("ticket_log_channel_id")(e.target.value || null)}
              placeholder="000000000000000000" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
          </div>
        </div>

        {/* AutoMod */}
        <div className="bg-card border border-card-border rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            <Shield className="w-4 h-4" /> AutoMod
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Banned Words <span className="text-muted-foreground font-normal">(comma-separated)</span></label>
            <textarea value={form.automod_banned_words || ""} onChange={e => f("automod_banned_words")(e.target.value)}
              rows={3} placeholder="word1, word2, word3" disabled={!isAdmin}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none disabled:opacity-60" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Max Mentions</label>
              <input type="number" value={form.automod_max_mentions || 5} min={1} max={50}
                onChange={e => f("automod_max_mentions")(parseInt(e.target.value))}
                disabled={!isAdmin}
                className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60" />
            </div>
            <div className="flex flex-col justify-center">
              <label className="block text-sm font-medium mb-1.5">Filter Links</label>
              <Toggle
                checked={!!form.automod_filter_links}
                onChange={v => f("automod_filter_links")(v ? 1 : 0)}
                disabled={!isAdmin}
              />
            </div>
          </div>
        </div>

        {/* Logs */}
        <div className="bg-card border border-card-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">
            <Bell className="w-4 h-4" /> Logs
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Log Channel ID</label>
            <input value={form.log_channel_id || ""} onChange={e => f("log_channel_id")(e.target.value || null)}
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
