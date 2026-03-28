import { useState } from "react";
import { Link } from "wouter";
import { BookOpen, Search, Bot, Shield, Ticket, Music, Gift, Users, Settings, Star, Info, Hash, Activity, Bell, ChevronRight, Lock, Globe, LogIn } from "lucide-react";

const MODULES = [
  {
    name: "Admin", icon: Settings, color: "text-chart-3 bg-chart-3/10",
    description: "Server configuration and admin utilities",
    commands: [
      { name: "setprefix", syntax: "!setprefix <prefix>", desc: "Change the command prefix for this server", admin: true },
      { name: "prefix", syntax: "!prefix", desc: "Show the current command prefix", admin: false },
      { name: "say", syntax: "!say <message>", desc: "Make the bot send a message", admin: true },
      { name: "announce", syntax: "!announce <#channel> <message>", desc: "Send an announcement embed to a channel", admin: true },
    ]
  },
  {
    name: "Moderation", icon: Shield, color: "text-destructive bg-destructive/10",
    description: "Member moderation tools",
    commands: [
      { name: "ban", syntax: "!ban <@user> [reason]", desc: "Ban a member from the server", admin: true },
      { name: "unban", syntax: "!unban <user_id> [reason]", desc: "Unban a member", admin: true },
      { name: "kick", syntax: "!kick <@user> [reason]", desc: "Kick a member from the server", admin: true },
      { name: "mute", syntax: "!mute <@user> [minutes] [reason]", desc: "Timeout a member", admin: true },
      { name: "unmute", syntax: "!unmute <@user>", desc: "Remove a member's timeout", admin: true },
      { name: "warn", syntax: "!warn <@user> <reason>", desc: "Issue a warning to a member", admin: true },
      { name: "warnings", syntax: "!warnings <@user>", desc: "View a member's warnings", admin: true },
      { name: "clearwarns", syntax: "!clearwarns <@user>", desc: "Clear all warnings for a member", admin: true },
      { name: "purge", syntax: "!purge [amount]", desc: "Bulk delete messages (max 100)", admin: true },
      { name: "lock", syntax: "!lock [#channel]", desc: "Lock a channel", admin: true },
      { name: "unlock", syntax: "!unlock [#channel]", desc: "Unlock a channel", admin: true },
      { name: "slowmode", syntax: "!slowmode <seconds> [#channel]", desc: "Set slowmode in a channel", admin: true },
    ]
  },
  {
    name: "Tickets", icon: Ticket, color: "text-primary bg-primary/10",
    description: "Support ticket system",
    commands: [
      { name: "ticket", syntax: "!ticket [reason]", desc: "Open a support ticket", admin: false },
      { name: "ticketsetup", syntax: "!ticketsetup", desc: "Set up the ticket panel in a channel", admin: true },
      { name: "setstaffrole", syntax: "!setstaffrole <@role>", desc: "Set the staff role for tickets", admin: true },
      { name: "setlogchannel", syntax: "!setlogchannel <#channel>", desc: "Set the ticket transcript log channel", admin: true },
      { name: "close", syntax: "!close [reason]", desc: "Close the current ticket", admin: false },
      { name: "claim", syntax: "!claim", desc: "Claim the current ticket (staff only)", admin: true },
      { name: "staffleaderboard", syntax: "!staffleaderboard", desc: "View staff performance stats", admin: false },
    ]
  },
  {
    name: "Info", icon: Info, color: "text-chart-5 bg-chart-5/10",
    description: "Server and user information",
    commands: [
      { name: "help", syntax: "!help [module]", desc: "Show all commands or module commands", admin: false },
      { name: "ping", syntax: "!ping", desc: "Check the bot's latency", admin: false },
      { name: "serverinfo", syntax: "!serverinfo", desc: "View server information", admin: false },
      { name: "userinfo", syntax: "!userinfo [@user]", desc: "View user information", admin: false },
      { name: "botinfo", syntax: "!botinfo", desc: "View bot information and stats", admin: false },
      { name: "avatar", syntax: "!avatar [@user]", desc: "Get a user's avatar", admin: false },
    ]
  },
  {
    name: "Hosting", icon: Activity, color: "text-chart-2 bg-chart-2/10",
    description: "KaluxHost service information",
    commands: [
      { name: "plans", syntax: "!plans", desc: "View all KaluxHost hosting plans", admin: false },
      { name: "status", syntax: "!status", desc: "Check service status", admin: false },
      { name: "uptime", syntax: "!uptime", desc: "View service uptime statistics", admin: false },
      { name: "node", syntax: "!node", desc: "View node information", admin: false },
      { name: "support", syntax: "!support", desc: "Get support information", admin: false },
    ]
  },
  {
    name: "Music", icon: Music, color: "text-chart-4 bg-chart-4/10",
    description: "Music playback in voice channels",
    commands: [
      { name: "play", syntax: "!play <song/URL>", desc: "Play a song or add to queue", admin: false },
      { name: "pause", syntax: "!pause", desc: "Pause the current track", admin: false },
      { name: "resume", syntax: "!resume", desc: "Resume playback", admin: false },
      { name: "skip", syntax: "!skip", desc: "Skip the current track", admin: false },
      { name: "stop", syntax: "!stop", desc: "Stop playback and clear queue", admin: false },
      { name: "queue", syntax: "!queue", desc: "View the song queue", admin: false },
      { name: "nowplaying", syntax: "!nowplaying", desc: "Show the current song", admin: false },
      { name: "volume", syntax: "!volume <1-100>", desc: "Set the playback volume", admin: false },
      { name: "leave", syntax: "!leave", desc: "Disconnect from voice channel", admin: false },
    ]
  },
  {
    name: "Giveaways", icon: Gift, color: "text-chart-3 bg-chart-3/10",
    description: "Host and manage giveaways",
    commands: [
      { name: "gstart", syntax: "!gstart <duration> <winners> <prize>", desc: "Start a giveaway", admin: true },
      { name: "gend", syntax: "!gend <message_id>", desc: "End a giveaway immediately", admin: true },
      { name: "greroll", syntax: "!greroll <message_id>", desc: "Reroll a giveaway winner", admin: true },
      { name: "glist", syntax: "!glist", desc: "List active giveaways", admin: false },
    ]
  },
  {
    name: "Roles", icon: Users, color: "text-chart-1 bg-chart-1/10",
    description: "Self-assignable roles",
    commands: [
      { name: "role", syntax: "!role <rolename>", desc: "Toggle a self-assignable role", admin: false },
      { name: "roles", syntax: "!roles", desc: "View available self-assignable roles", admin: false },
      { name: "addrolereact", syntax: "!addrolereact <@role>", desc: "Add a role to self-assign list", admin: true },
      { name: "removerolereact", syntax: "!removerolereact <@role>", desc: "Remove a role from self-assign list", admin: true },
    ]
  },
  {
    name: "Staff", icon: Star, color: "text-chart-3 bg-chart-3/10",
    description: "Bot staff management",
    commands: [
      { name: "addstaff", syntax: "!addstaff <@user> [role]", desc: "Add a user as bot staff (admin only)", admin: true },
      { name: "removestaff", syntax: "!removestaff <@user>", desc: "Remove a user from bot staff (admin only)", admin: true },
      { name: "stafflist", syntax: "!stafflist", desc: "List all bot staff members", admin: false },
      { name: "staffcheck", syntax: "!staffcheck [@user]", desc: "Check if a user is bot staff", admin: false },
    ]
  },
  {
    name: "Verification", icon: Shield, color: "text-chart-2 bg-chart-2/10",
    description: "Member verification system",
    commands: [
      { name: "verify", syntax: "!verify", desc: "Send verification panel to a channel", admin: true },
      { name: "setverifyrole", syntax: "!setverifyrole <@role>", desc: "Set the role given on verification", admin: true },
    ]
  },
  {
    name: "Suggestions", icon: Bell, color: "text-primary bg-primary/10",
    description: "Community suggestion system",
    commands: [
      { name: "suggest", syntax: "!suggest <suggestion>", desc: "Submit a suggestion", admin: false },
      { name: "accept", syntax: "!accept <message_id> [reason]", desc: "Accept a suggestion", admin: true },
      { name: "deny", syntax: "!deny <message_id> [reason]", desc: "Deny a suggestion", admin: true },
      { name: "setchannel", syntax: "!setchannel <#channel>", desc: "Set the suggestions channel", admin: true },
    ]
  },
];

export default function Docs() {
  const [search, setSearch] = useState("");
  const [activeModule, setActiveModule] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "user" | "admin">("all");

  const filtered = MODULES.map(mod => ({
    ...mod,
    commands: mod.commands.filter(cmd => {
      const matchSearch = !search || cmd.name.includes(search.toLowerCase()) || cmd.desc.toLowerCase().includes(search.toLowerCase()) || mod.name.toLowerCase().includes(search.toLowerCase());
      const matchFilter = filter === "all" || (filter === "admin" ? cmd.admin : !cmd.admin);
      return matchSearch && matchFilter;
    })
  })).filter(mod => mod.commands.length > 0 || (!search && filter === "all"));

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
              <Bot className="w-4 h-4 text-primary" />
            </div>
            <div>
              <span className="font-semibold text-sm">KaluxHost</span>
              <span className="text-muted-foreground text-sm"> / Docs</span>
            </div>
          </div>
          <Link href="/login"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-medium transition">
            <LogIn className="w-3.5 h-3.5" /> Staff Login
          </Link>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/15 mb-4">
            <BookOpen className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold">KaluxHost Bot Documentation</h1>
          <p className="text-muted-foreground mt-2 max-w-xl mx-auto">
            Complete guide to all bot commands. Use <code className="bg-muted px-1.5 py-0.5 rounded text-xs">!</code> prefix or <code className="bg-muted px-1.5 py-0.5 rounded text-xs">/</code> slash commands.
          </p>
          <div className="flex items-center justify-center gap-3 mt-4 text-sm">
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-chart-2/10 text-chart-2 border border-chart-2/20">
              <Globe className="w-3.5 h-3.5" /> {MODULES.flatMap(m => m.commands.filter(c => !c.admin)).length} User Commands
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-destructive/10 text-destructive border border-destructive/20">
              <Lock className="w-3.5 h-3.5" /> {MODULES.flatMap(m => m.commands.filter(c => c.admin)).length} Admin Commands
            </span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search commands..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-card border border-card-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex rounded-lg border border-border overflow-hidden">
            {[["all", "All"], ["user", "User"], ["admin", "Admin"]].map(([key, label]) => (
              <button key={key} onClick={() => setFilter(key as any)}
                className={`px-4 py-2.5 text-sm font-medium transition ${
                  filter === key ? "bg-primary text-primary-foreground" : "bg-card text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}>{label}</button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="hidden lg:block">
            <div className="sticky top-20 bg-card border border-card-border rounded-xl p-4 space-y-1">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 px-2">Modules</p>
              {MODULES.map(mod => {
                const Icon = mod.icon;
                return (
                  <a key={mod.name} href={`#${mod.name.toLowerCase()}`}
                    className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm transition ${
                      activeModule === mod.name ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-accent"
                    }`}>
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {mod.name}
                  </a>
                );
              })}
            </div>
          </div>

          <div className="lg:col-span-3 space-y-6">
            {filtered.map(mod => {
              const Icon = mod.icon;
              return (
                <div key={mod.name} id={mod.name.toLowerCase()} className="bg-card border border-card-border rounded-xl overflow-hidden">
                  <div className="px-5 py-4 border-b border-border flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${mod.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h2 className="font-semibold">{mod.name}</h2>
                      <p className="text-xs text-muted-foreground">{mod.description}</p>
                    </div>
                    <span className="ml-auto text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">
                      {mod.commands.length} cmds
                    </span>
                  </div>
                  <div className="divide-y divide-border">
                    {mod.commands.map(cmd => (
                      <div key={cmd.name} className="px-5 py-3.5 flex items-start gap-4 hover:bg-accent/20 transition-colors">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <code className="text-sm font-mono font-semibold text-foreground">{cmd.syntax}</code>
                            {cmd.admin && (
                              <span className="flex items-center gap-1 text-xs bg-destructive/10 text-destructive border border-destructive/20 px-1.5 py-0.5 rounded-full">
                                <Lock className="w-2.5 h-2.5" /> Admin
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground mt-0.5">{cmd.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            {filtered.length === 0 && (
              <div className="text-center py-16 text-muted-foreground">
                <Search className="w-12 h-12 mx-auto mb-3 opacity-40" />
                <p>No commands found for "<strong>{search}</strong>"</p>
              </div>
            )}
          </div>
        </div>

        <footer className="mt-16 pt-8 border-t border-border text-center text-sm text-muted-foreground">
          <p>KaluxHost Bot v2.0.0 · Built for the KaluxHost community</p>
          <p className="mt-1">
            <Link href="/login" className="hover:text-foreground transition-colors">Staff Dashboard</Link>
            {" · "}
            <span>Guild ID: 1485175801887326339</span>
          </p>
        </footer>
      </div>
    </div>
  );
}
