import { useState } from "react";
import { api } from "../lib/api";
import { Shield, Ban, UserMinus, Clock, AlertTriangle, Search, Check, X } from "lucide-react";

type Action = "warn" | "mute" | "kick" | "ban";

function ActionCard({ icon: Icon, label, color, onClick }: {
  icon: any; label: string; color: string; onClick: () => void;
}) {
  return (
    <button onClick={onClick}
      className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all hover:scale-105 ${color}`}>
      <Icon className="w-6 h-6" />
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

interface ModalProps {
  action: Action; onClose: () => void;
}

function ActionModal({ action, onClose }: ModalProps) {
  const [userId, setUserId] = useState("");
  const [reason, setReason] = useState("");
  const [minutes, setMinutes] = useState("10");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);

  const titles: Record<Action, string> = {
    warn: "Warn Member", mute: "Mute Member", kick: "Kick Member", ban: "Ban Member"
  };
  const colors: Record<Action, string> = {
    warn: "text-chart-3", mute: "text-chart-5", kick: "text-chart-1", ban: "text-destructive"
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      if (action === "warn") await api.post("/moderation/warn", { user_id: userId, reason });
      else if (action === "mute") await api.post("/moderation/mute", { user_id: userId, minutes: parseInt(minutes), reason });
      else if (action === "kick") await api.post("/moderation/kick", { user_id: userId, reason });
      else if (action === "ban") await api.post("/moderation/ban", { user_id: userId, reason });
      setResult({ ok: true, msg: `${titles[action]} successful` });
      setUserId(""); setReason("");
    } catch (err: any) {
      setResult({ ok: false, msg: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-card-border rounded-xl p-6 w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className={`font-semibold ${colors[action]}`}>{titles[action]}</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
        </div>

        {result && (
          <div className={`mb-4 px-4 py-3 rounded-lg flex items-center gap-2 text-sm ${
            result.ok ? "bg-chart-2/10 border border-chart-2/20 text-chart-2" : "bg-destructive/10 border border-destructive/20 text-destructive"
          }`}>
            {result.ok ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
            {result.msg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">Discord User ID</label>
            <input value={userId} onChange={e => setUserId(e.target.value)} placeholder="000000000000000000" required
              className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
            <p className="text-xs text-muted-foreground mt-1">Right-click on user in Discord → Copy User ID</p>
          </div>

          {action === "mute" && (
            <div>
              <label className="block text-sm font-medium mb-1.5">Duration (minutes)</label>
              <input type="number" value={minutes} onChange={e => setMinutes(e.target.value)} min="1" max="40320"
                className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1.5">Reason</label>
            <textarea value={reason} onChange={e => setReason(e.target.value)} rows={3}
              placeholder={`Reason for ${action}`}
              className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none" />
          </div>

          <div className="flex gap-3">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-border text-sm hover:bg-accent transition">
              Cancel
            </button>
            <button type="submit" disabled={loading}
              className={`flex-1 py-2.5 rounded-lg font-medium text-sm transition disabled:opacity-50 ${
                action === "ban" ? "bg-destructive hover:bg-destructive/90 text-destructive-foreground" :
                action === "kick" ? "bg-primary/80 hover:bg-primary/70 text-primary-foreground" :
                "bg-primary hover:bg-primary/90 text-primary-foreground"
              }`}>
              {loading ? "Applying..." : titles[action]}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Moderation() {
  const [activeAction, setActiveAction] = useState<Action | null>(null);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [warnUserId, setWarnUserId] = useState("");
  const [loadingWarns, setLoadingWarns] = useState(false);

  const lookupWarnings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!warnUserId.trim()) return;
    setLoadingWarns(true);
    try {
      const data = await api.get<any[]>(`/moderation/warnings/${warnUserId}`);
      setWarnings(data);
    } catch (e: any) { alert(e.message); }
    finally { setLoadingWarns(false); }
  };

  const deleteWarning = async (id: number) => {
    try {
      await api.delete(`/moderation/warnings/${id}`);
      setWarnings(warnings.filter(w => w.id !== id));
    } catch (e: any) { alert(e.message); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Moderation</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Manage members and view moderation history</p>
      </div>

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <ActionCard icon={AlertTriangle} label="Warn" color="border-chart-3/30 bg-chart-3/5 text-chart-3 hover:bg-chart-3/10" onClick={() => setActiveAction("warn")} />
          <ActionCard icon={Clock} label="Mute" color="border-chart-5/30 bg-chart-5/5 text-chart-5 hover:bg-chart-5/10" onClick={() => setActiveAction("mute")} />
          <ActionCard icon={UserMinus} label="Kick" color="border-chart-1/30 bg-chart-1/5 text-chart-1 hover:bg-chart-1/10" onClick={() => setActiveAction("kick")} />
          <ActionCard icon={Ban} label="Ban" color="border-destructive/30 bg-destructive/5 text-destructive hover:bg-destructive/10" onClick={() => setActiveAction("ban")} />
        </div>
      </div>

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">Warning Lookup</h2>
        <form onSubmit={lookupWarnings} className="flex gap-2">
          <input value={warnUserId} onChange={e => setWarnUserId(e.target.value)} placeholder="Discord User ID"
            className="flex-1 px-3 py-2 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
          <button type="submit" disabled={loadingWarns}
            className="px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium transition disabled:opacity-50 flex items-center gap-2">
            <Search className="w-4 h-4" />
            Search
          </button>
        </form>

        {warnings.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm text-muted-foreground">{warnings.length} warning(s) found</p>
            {warnings.map(w => (
              <div key={w.id} className="flex items-start justify-between p-3 rounded-lg bg-muted/30 border border-border">
                <div>
                  <p className="text-sm font-medium">{w.reason}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    By {w.mod_id} · {new Date(w.created_at * 1000).toLocaleDateString()}
                  </p>
                </div>
                <button onClick={() => deleteWarning(w.id)}
                  className="ml-3 p-1.5 rounded hover:bg-destructive/15 text-muted-foreground hover:text-destructive transition flex-shrink-0">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {warnings.length === 0 && warnUserId && !loadingWarns && (
          <p className="mt-3 text-sm text-muted-foreground text-center py-4">No warnings found for this user</p>
        )}
      </div>

      {activeAction && <ActionModal action={activeAction} onClose={() => setActiveAction(null)} />}
    </div>
  );
}
