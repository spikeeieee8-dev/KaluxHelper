import { useEffect, useState } from "react";
import { api } from "../lib/api";
import {
  Ticket, X, ChevronLeft, ChevronRight, Search,
  CheckCircle, Clock, FileText, Star, RefreshCw
} from "lucide-react";

interface TicketItem {
  id: number; ticket_number: number; user_id: string; category: string;
  status: string; claimed_by: string | null; open_time: number;
  close_time: number | null; close_reason: string | null; rating: number | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  general: "bg-blue-500/10 text-blue-400",
  billing: "bg-green-500/10 text-green-400",
  report:  "bg-red-500/10 text-red-400",
};

function StarRating({ rating }: { rating: number | null }) {
  if (!rating) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <span className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star key={i} className={`w-3 h-3 ${i < rating ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground/30"}`} />
      ))}
    </span>
  );
}

export default function Tickets() {
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [closing, setClosing] = useState<number | null>(null);
  const [closeReason, setCloseReason] = useState("");
  const [closeTarget, setCloseTarget] = useState<number | null>(null);

  const [transcriptTicket, setTranscriptTicket] = useState<TicketItem | null>(null);
  const [transcriptContent, setTranscriptContent] = useState<string | null>(null);
  const [transcriptLoading, setTranscriptLoading] = useState(false);
  const [transcriptError, setTranscriptError] = useState("");

  const limit = 15;

  const fetchTickets = () => {
    setLoading(true);
    const params = new URLSearchParams({ status, page: String(page), limit: String(limit) });
    if (search) params.set("search", search);
    api.get<{ tickets: TicketItem[]; total: number }>(`/tickets?${params}`)
      .then(d => { setTickets(d.tickets); setTotal(d.total); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchTickets(); }, [status, page, search]);

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

  const handleViewTranscript = async (ticket: TicketItem) => {
    setTranscriptTicket(ticket);
    setTranscriptContent(null);
    setTranscriptError("");
    setTranscriptLoading(true);
    try {
      const data = await api.get<{ content: string }>(`/tickets/${ticket.id}/transcript`);
      setTranscriptContent(data.content);
    } catch (e: any) {
      setTranscriptError(e.message || "Transcript not available.");
    } finally {
      setTranscriptLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">Tickets</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{total} total tickets</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <form onSubmit={handleSearchSubmit} className="flex gap-1.5">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                value={searchInput}
                onChange={e => setSearchInput(e.target.value)}
                placeholder="Search user ID…"
                className="pl-8 pr-3 py-1.5 rounded-lg bg-card border border-border text-sm w-44 focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground"
              />
            </div>
            <button type="submit" className="px-3 py-1.5 rounded-lg bg-card border border-border text-sm hover:bg-accent transition">
              Go
            </button>
            {search && (
              <button type="button" onClick={() => { setSearch(""); setSearchInput(""); setPage(1); }}
                className="px-3 py-1.5 rounded-lg bg-card border border-border text-sm hover:bg-accent transition text-muted-foreground">
                Clear
              </button>
            )}
          </form>
          <button onClick={fetchTickets} className="p-1.5 rounded-lg bg-card border border-border hover:bg-accent transition text-muted-foreground" title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
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
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium hidden lg:table-cell">Claimed By</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium hidden md:table-cell">Opened</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium hidden md:table-cell">Rating</th>
                  <th className="text-left px-4 py-3 text-muted-foreground font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {tickets.map(t => (
                  <tr key={t.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-muted-foreground text-xs">#{String(t.ticket_number).padStart(4, "0")}</td>
                    <td className="px-4 py-3 font-mono text-xs">{t.user_id}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${CATEGORY_COLORS[t.category] || "bg-muted text-muted-foreground"}`}>
                        {t.category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        t.status === "open" ? "bg-chart-2/15 text-chart-2" : "bg-muted text-muted-foreground"
                      }`}>
                        {t.status === "open" ? <Clock className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell text-xs text-muted-foreground font-mono">
                      {t.claimed_by || "—"}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-xs text-muted-foreground">
                      {new Date(t.open_time * 1000).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <StarRating rating={t.rating} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {t.status === "closed" && (
                          <button onClick={() => handleViewTranscript(t)}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary text-xs font-medium transition">
                            <FileText className="w-3 h-3" />
                            Transcript
                          </button>
                        )}
                        {t.status === "open" && (
                          <button onClick={() => setCloseTarget(t.id)}
                            className="px-2.5 py-1 rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive text-xs font-medium transition">
                            Close
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <span className="text-xs text-muted-foreground">Page {page} of {totalPages} · {total} tickets</span>
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

      {/* Close Ticket Modal */}
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

      {/* Transcript Modal */}
      {transcriptTicket && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-card-border rounded-xl shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <h2 className="font-semibold">
                  Ticket #{String(transcriptTicket.ticket_number).padStart(4, "0")} — Transcript
                </h2>
                <span className="text-xs text-muted-foreground capitalize">· {transcriptTicket.category}</span>
              </div>
              <button onClick={() => { setTranscriptTicket(null); setTranscriptContent(null); }}
                className="text-muted-foreground hover:text-foreground transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {transcriptLoading ? (
                <div className="flex items-center justify-center h-32 text-muted-foreground gap-2">
                  <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  Loading transcript…
                </div>
              ) : transcriptError ? (
                <div className="flex flex-col items-center justify-center h-32 text-muted-foreground gap-2">
                  <FileText className="w-8 h-8 opacity-40" />
                  <p className="text-sm">{transcriptError}</p>
                </div>
              ) : (
                <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-relaxed bg-background/50 rounded-lg p-4 border border-border">
                  {transcriptContent}
                </pre>
              )}
            </div>

            {transcriptContent && (
              <div className="px-5 py-3 border-t border-border flex-shrink-0 flex justify-end">
                <button
                  onClick={() => {
                    const blob = new Blob([transcriptContent], { type: "text/plain" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `transcript-${String(transcriptTicket.ticket_number).padStart(4, "0")}.txt`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary text-sm font-medium transition"
                >
                  Download .txt
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
