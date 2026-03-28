import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Ticket, X, ChevronLeft, ChevronRight, Search, CheckCircle, Clock } from "lucide-react";

interface TicketItem {
  id: number; ticket_number: number; user_id: string; category: string;
  status: string; claimed_by: string | null; open_time: number;
  close_time: number | null; close_reason: string | null; rating: number | null;
}

export default function Tickets() {
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [closing, setClosing] = useState<number | null>(null);
  const [closeReason, setCloseReason] = useState("");
  const [closeTarget, setCloseTarget] = useState<number | null>(null);
  const limit = 15;

  const fetchTickets = () => {
    setLoading(true);
    api.get<{ tickets: TicketItem[]; total: number }>(
      `/tickets?status=${status}&page=${page}&limit=${limit}`
    ).then(d => { setTickets(d.tickets); setTotal(d.total); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchTickets(); }, [status, page]);

  const handleClose = async () => {
    if (!closeTarget) return;
    setClosing(closeTarget);
    try {
      await api.post(`/tickets/${closeTarget}/close`, { reason: closeReason || "Closed from dashboard" });
      setCloseTarget(null);
      setCloseReason("");
      fetchTickets();
    } catch (e: any) { alert(e.message); }
    finally { setClosing(null); }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Tickets</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{total} total tickets</p>
        </div>
        <div className="flex gap-2">
          {["all", "open", "closed"].map(s => (
            <button key={s} onClick={() => { setStatus(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition capitalize ${
                status === s ? "bg-primary text-primary-foreground" : "bg-card border border-border text-muted-foreground hover:text-foreground"
              }`}>{s}</button>
          ))}
        </div>
      </div>

      <div className="bg-card border border-card-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : tickets.length === 0 ? (
          <div className="p-10 text-center">
            <Ticket className="w-10 h-10 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground text-sm">No tickets found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium">#</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium">User ID</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium">Category</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium hidden md:table-cell">Claimed By</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium hidden md:table-cell">Opened</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {tickets.map(t => (
                  <tr key={t.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-muted-foreground text-xs">#{t.ticket_number}</td>
                    <td className="px-4 py-3 font-mono text-xs">{t.user_id}</td>
                    <td className="px-4 py-3 capitalize">{t.category}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        t.status === "open" ? "bg-chart-2/15 text-chart-2" : "bg-muted text-muted-foreground"
                      }`}>
                        {t.status === "open" ? <Clock className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-xs text-muted-foreground font-mono">
                      {t.claimed_by || "—"}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-xs text-muted-foreground">
                      {new Date(t.open_time * 1000).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      {t.status === "open" ? (
                        <button onClick={() => setCloseTarget(t.id)}
                          className="px-2.5 py-1 rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive text-xs font-medium transition">
                          Close
                        </button>
                      ) : (
                        <span className="text-xs text-muted-foreground">Closed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <span className="text-xs text-muted-foreground">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="p-1.5 rounded-lg bg-secondary hover:bg-accent disabled:opacity-40 transition">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}
                className="p-1.5 rounded-lg bg-secondary hover:bg-accent disabled:opacity-40 transition">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {closeTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-card-border rounded-xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">Close Ticket</h2>
              <button onClick={() => setCloseTarget(null)} className="text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-4">Provide a reason for closing this ticket.</p>
            <textarea
              value={closeReason}
              onChange={e => setCloseReason(e.target.value)}
              placeholder="Reason (optional)"
              rows={3}
              className="w-full px-3 py-2 rounded-lg bg-background border border-input text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none mb-4"
            />
            <div className="flex gap-3">
              <button onClick={() => setCloseTarget(null)}
                className="flex-1 py-2 rounded-lg border border-border text-sm hover:bg-accent transition">
                Cancel
              </button>
              <button onClick={handleClose} disabled={!!closing}
                className="flex-1 py-2 rounded-lg bg-destructive hover:bg-destructive/90 text-destructive-foreground text-sm font-medium transition disabled:opacity-50">
                {closing ? "Closing..." : "Close Ticket"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
