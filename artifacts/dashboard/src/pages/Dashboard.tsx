import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Ticket, Shield, Users, Server, TrendingUp, Clock, Star, AlertCircle } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface Stats {
  totalTickets: number; openTickets: number; closedTickets: number;
  totalWarnings: number; totalStaff: number;
  recentTickets: any[]; topStaff: any[]; ticketsByDay: any[];
  guild: { name: string; icon: string; memberCount: number; onlineCount: number; id: string } | null;
}

function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: any; label: string; value: string | number; sub?: string; color: string;
}) {
  return (
    <div className="bg-card border border-card-border rounded-xl p-5 hover:border-primary/30 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center flex-shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-popover border border-popover-border rounded-lg px-3 py-2 text-xs shadow-md">
      <p className="text-muted-foreground">{label}</p>
      <p className="font-semibold text-foreground">{payload[0].value} tickets</p>
    </div>
  );
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Stats>("/stats").then(setStats).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-card border border-card-border rounded-xl animate-pulse" />
        ))}
      </div>
    </div>
  );

  const chartData = stats?.ticketsByDay.map(r => ({
    day: r.day?.slice(5) || "",
    count: r.count,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Overview</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {stats?.guild ? `${stats.guild.name} — ${stats.guild.memberCount?.toLocaleString()} members` : "Loading server info..."}
          </p>
        </div>
        {stats?.guild?.onlineCount && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="w-2 h-2 rounded-full bg-chart-2 animate-pulse" />
            {stats.guild.onlineCount.toLocaleString()} online
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Ticket} label="Total Tickets" value={stats?.totalTickets || 0} color="bg-primary/15 text-primary" />
        <StatCard icon={Clock} label="Open Tickets" value={stats?.openTickets || 0} sub="Needs attention" color="bg-chart-3/15 text-chart-3" />
        <StatCard icon={Shield} label="Warnings Issued" value={stats?.totalWarnings || 0} color="bg-destructive/15 text-destructive" />
        <StatCard icon={Users} label="Bot Staff" value={stats?.totalStaff || 0} color="bg-chart-2/15 text-chart-2" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-card border border-card-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4 text-muted-foreground uppercase tracking-wide">Tickets — Last 7 Days</h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(235,86%,65%)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(235,86%,65%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,8%,18%)" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: "hsl(220,9%,55%)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "hsl(220,9%,55%)" }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="count" stroke="hsl(235,86%,65%)" strokeWidth={2} fill="url(#grad)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">No data for this period</div>
          )}
        </div>

        <div className="bg-card border border-card-border rounded-xl p-5">
          <h2 className="text-sm font-semibold mb-4 text-muted-foreground uppercase tracking-wide">Top Staff</h2>
          {stats?.topStaff?.length ? (
            <div className="space-y-3">
              {stats.topStaff.map((s, i) => (
                <div key={s.user_id} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary flex-shrink-0">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{s.user_id}</p>
                    <p className="text-xs text-muted-foreground">{s.tickets_handled} tickets</p>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-chart-3">
                    <Star className="w-3 h-3" />
                    {s.rating_count ? (s.total_rating / s.rating_count).toFixed(1) : "—"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No staff stats yet</p>
          )}
        </div>
      </div>

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-4 text-muted-foreground uppercase tracking-wide">Recent Tickets</h2>
        {stats?.recentTickets?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left pb-3 text-muted-foreground font-medium">#</th>
                  <th className="text-left pb-3 text-muted-foreground font-medium">Category</th>
                  <th className="text-left pb-3 text-muted-foreground font-medium">Status</th>
                  <th className="text-left pb-3 text-muted-foreground font-medium">Opened</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {stats.recentTickets.map(t => (
                  <tr key={t.id} className="hover:bg-accent/50 transition-colors">
                    <td className="py-3 text-muted-foreground font-mono">#{t.ticket_number}</td>
                    <td className="py-3 capitalize">{t.category}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        t.status === "open" ? "bg-chart-2/15 text-chart-2" : "bg-muted text-muted-foreground"
                      }`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="py-3 text-muted-foreground">
                      {new Date(t.open_time * 1000).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <AlertCircle className="w-4 h-4" /> No recent tickets
          </div>
        )}
      </div>
    </div>
  );
}
