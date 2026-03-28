import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Plus, Trash2, Edit2, Users, X, Check, Crown, Shield, User } from "lucide-react";

interface Account { id: number; username: string; role: string; discord_id: string | null; created_at: number; }
interface BotStaff { guild_id: string; user_id: string; role: string; added_by: string | null; added_at: number; }

const ROLE_ICONS: Record<string, any> = { admin: Crown, moderator: Shield, staff: User };
const ROLE_COLORS: Record<string, string> = {
  admin: "bg-chart-3/15 text-chart-3 border-chart-3/30",
  moderator: "bg-primary/15 text-primary border-primary/30",
  staff: "bg-chart-2/15 text-chart-2 border-chart-2/30",
};

export default function Staff() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [botStaff, setBotStaff] = useState<BotStaff[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [showAddBot, setShowAddBot] = useState(false);
  const [tab, setTab] = useState<"accounts" | "bot">("accounts");

  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("staff");
  const [newDiscord, setNewDiscord] = useState("");
  const [newBotUser, setNewBotUser] = useState("");
  const [newBotRole, setNewBotRole] = useState("staff");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      api.get<Account[]>("/staff"),
      api.get<BotStaff[]>("/staff/bot-staff"),
    ]).then(([accs, bs]) => { setAccounts(accs); setBotStaff(bs); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const addAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.post("/staff", { username: newUsername, password: newPassword, role: newRole, discord_id: newDiscord || undefined });
      setShowAddAccount(false); setNewUsername(""); setNewPassword(""); setNewRole("staff"); setNewDiscord("");
      fetchData();
    } catch (err: any) { setError(err.message); }
    finally { setSaving(false); }
  };

  const addBotStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.post("/staff/bot-staff", { user_id: newBotUser, role: newBotRole });
      setShowAddBot(false); setNewBotUser(""); setNewBotRole("staff");
      fetchData();
    } catch (err: any) { setError(err.message); }
    finally { setSaving(false); }
  };

  const deleteAccount = async (id: number) => {
    if (!confirm("Delete this account?")) return;
    try { await api.delete(`/staff/${id}`); fetchData(); } catch (e: any) { alert(e.message); }
  };

  const deleteBotStaff = async (userId: string) => {
    if (!confirm("Remove this bot staff member?")) return;
    try { await api.delete(`/staff/bot-staff/${userId}`); fetchData(); } catch (e: any) { alert(e.message); }
  };

  const isAdmin = user?.role === "admin";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Staff Management</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Manage dashboard accounts and bot staff</p>
        </div>
      </div>

      <div className="flex border-b border-border">
        {[["accounts", "Dashboard Accounts"], ["bot", "Bot Staff"]].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key as any)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px ${
              tab === key ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
            }`}>{label}</button>
        ))}
      </div>

      {tab === "accounts" && (
        <div className="space-y-4">
          {isAdmin && (
            <div className="flex justify-end">
              <button onClick={() => { setShowAddAccount(true); setError(""); }}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium transition">
                <Plus className="w-4 h-4" /> Add Account
              </button>
            </div>
          )}

          <div className="bg-card border border-card-border rounded-xl overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-muted-foreground text-sm">Loading...</div>
            ) : (
              <div className="divide-y divide-border">
                {accounts.map(acc => {
                  const RoleIcon = ROLE_ICONS[acc.role] || User;
                  return (
                    <div key={acc.id} className="flex items-center gap-4 px-4 py-3.5 hover:bg-accent/30 transition-colors">
                      <div className="w-9 h-9 rounded-full bg-primary/15 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-bold text-primary">{acc.username[0].toUpperCase()}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">{acc.username}</p>
                          {acc.id === user?.id && <span className="text-xs bg-primary/15 text-primary px-1.5 py-0.5 rounded">You</span>}
                        </div>
                        {acc.discord_id && <p className="text-xs text-muted-foreground font-mono">{acc.discord_id}</p>}
                      </div>
                      <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border capitalize ${ROLE_COLORS[acc.role] || ""}`}>
                        <RoleIcon className="w-3 h-3" />
                        {acc.role}
                      </span>
                      <p className="text-xs text-muted-foreground hidden md:block">
                        {new Date(acc.created_at * 1000).toLocaleDateString()}
                      </p>
                      {isAdmin && acc.id !== user?.id && (
                        <button onClick={() => deleteAccount(acc.id)}
                          className="p-1.5 rounded hover:bg-destructive/15 text-muted-foreground hover:text-destructive transition">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "bot" && (
        <div className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground">These Discord users can use admin bot commands (via <code className="bg-muted px-1 rounded text-xs">!addstaff</code>). They are separate from dashboard accounts.</p>
          </div>
          {isAdmin && (
            <div className="flex justify-end">
              <button onClick={() => { setShowAddBot(true); setError(""); }}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium transition">
                <Plus className="w-4 h-4" /> Add Bot Staff
              </button>
            </div>
          )}

          <div className="bg-card border border-card-border rounded-xl overflow-hidden">
            {botStaff.length === 0 ? (
              <div className="p-10 text-center">
                <Users className="w-10 h-10 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No bot staff yet. Use <code className="bg-muted px-1 rounded text-xs">!addstaff @user</code> in Discord.</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {botStaff.map(s => {
                  const RoleIcon = ROLE_ICONS[s.role] || User;
                  return (
                    <div key={s.user_id} className="flex items-center gap-4 px-4 py-3.5 hover:bg-accent/30 transition-colors">
                      <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-mono">{s.user_id}</p>
                        <p className="text-xs text-muted-foreground">Added {new Date(s.added_at * 1000).toLocaleDateString()}</p>
                      </div>
                      <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border capitalize ${ROLE_COLORS[s.role] || ""}`}>
                        <RoleIcon className="w-3 h-3" />
                        {s.role}
                      </span>
                      {isAdmin && (
                        <button onClick={() => deleteBotStaff(s.user_id)}
                          className="p-1.5 rounded hover:bg-destructive/15 text-muted-foreground hover:text-destructive transition">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {(showAddAccount || showAddBot) && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-card-border rounded-xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold">{showAddAccount ? "Add Dashboard Account" : "Add Bot Staff"}</h2>
              <button onClick={() => { setShowAddAccount(false); setShowAddBot(false); setError(""); }}
                className="text-muted-foreground hover:text-foreground"><X className="w-5 h-5" /></button>
            </div>
            {error && (
              <div className="mb-4 px-3 py-2 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">{error}</div>
            )}
            {showAddAccount ? (
              <form onSubmit={addAccount} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Username</label>
                  <input value={newUsername} onChange={e => setNewUsername(e.target.value)} required
                    className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Password</label>
                  <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required
                    className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Role</label>
                  <select value={newRole} onChange={e => setNewRole(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    <option value="staff">Staff</option>
                    <option value="moderator">Moderator</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Discord ID (optional)</label>
                  <input value={newDiscord} onChange={e => setNewDiscord(e.target.value)} placeholder="000000000000000000"
                    className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
                </div>
                <button type="submit" disabled={saving}
                  className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-sm transition disabled:opacity-50">
                  {saving ? "Creating..." : "Create Account"}
                </button>
              </form>
            ) : (
              <form onSubmit={addBotStaff} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Discord User ID</label>
                  <input value={newBotUser} onChange={e => setNewBotUser(e.target.value)} required placeholder="000000000000000000"
                    className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Role</label>
                  <select value={newBotRole} onChange={e => setNewBotRole(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    <option value="staff">Staff</option>
                    <option value="moderator">Moderator</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <button type="submit" disabled={saving}
                  className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-sm transition disabled:opacity-50">
                  {saving ? "Adding..." : "Add Staff"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
