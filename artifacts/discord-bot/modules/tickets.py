"""
TICKETS MODULE
Full-featured ticket system for KaluxHost.

Features:
  - 3 categories (General, Billing, Report) → each to a specific Discord category
  - Ticket channels: user + staff role only
  - Claim system: staff must claim before closing; 1 active claim per staff
  - User can close without claim; staff must claim first and provide a reason
  - Rating flow (1-5 stars) after a claimed ticket closes
  - Staff action after rating: Delete → log embed + transcript; Reopen → restore ticket
  - Staff stats: tickets handled, avg rating, reps, duty hours
  - !rep (24h cooldown) | !on / !off duty | !staffstats | !leaderboard
  - !setstaffrole | !setlogchannel
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import datetime
import asyncio

from main.config import DB_PATH, DATA_DIR, COLOR_BRAND
from main.utils.embeds import brand, success, error, warn

# ─── Constants ────────────────────────────────────────────────────────────────

TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

CATEGORY_MAP = {
    "general": ("🎫 General Support", 1485967694309097572),
    "billing":  ("💳 Billing",         1485963499762094221),
    "report":   ("🚨 Report",          1485963858391597097),
}


# ─── DB Init ──────────────────────────────────────────────────────────────────

async def _init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS ticket_config (
                guild_id       TEXT PRIMARY KEY,
                staff_role_id  TEXT,
                log_channel_id TEXT,
                ticket_counter INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id      TEXT    NOT NULL,
                channel_id    TEXT    NOT NULL UNIQUE,
                user_id       TEXT    NOT NULL,
                category      TEXT    NOT NULL,
                status        TEXT    NOT NULL DEFAULT 'open',
                claimed_by    TEXT,
                open_time     INTEGER NOT NULL,
                close_time    INTEGER,
                close_reason  TEXT,
                rating        INTEGER,
                ticket_number INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS staff_stats (
                guild_id        TEXT    NOT NULL,
                user_id         TEXT    NOT NULL,
                tickets_handled INTEGER NOT NULL DEFAULT 0,
                total_rating    INTEGER NOT NULL DEFAULT 0,
                rating_count    INTEGER NOT NULL DEFAULT 0,
                rep_count       INTEGER NOT NULL DEFAULT 0,
                total_duty_secs INTEGER NOT NULL DEFAULT 0,
                on_duty_since   INTEGER,
                last_off_duty   INTEGER,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS reps (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id     TEXT    NOT NULL,
                from_user_id TEXT    NOT NULL,
                to_user_id   TEXT    NOT NULL,
                created_at   INTEGER NOT NULL
            );
        """)
        await db.commit()
        # Safe migration: add last_off_duty column for existing databases
        try:
            await db.execute("ALTER TABLE staff_stats ADD COLUMN last_off_duty INTEGER")
            await db.commit()
        except Exception:
            pass  # Column already exists


# ─── DB Helpers ───────────────────────────────────────────────────────────────

async def _get_config(guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ticket_config WHERE guild_id = ?", (str(guild_id),)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}


async def _get_ticket_by_channel(channel_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE channel_id = ?", (str(channel_id),)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def _bump_counter(guild_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO ticket_config (guild_id, ticket_counter)
            VALUES (?, 1)
            ON CONFLICT(guild_id) DO UPDATE SET ticket_counter = ticket_counter + 1
        """, (str(guild_id),))
        await db.commit()
        async with db.execute(
            "SELECT ticket_counter FROM ticket_config WHERE guild_id = ?", (str(guild_id),)
        ) as cur:
            return (await cur.fetchone())[0]


async def _ensure_staff_row(guild_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO staff_stats (guild_id, user_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id, user_id) DO NOTHING
        """, (str(guild_id), str(user_id)))
        await db.commit()


async def _get_staff_stats(guild_id: int, user_id: int) -> dict:
    await _ensure_staff_row(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM staff_stats WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        ) as cur:
            return dict(await cur.fetchone())


async def _has_active_claim(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM tickets WHERE guild_id = ? AND claimed_by = ? AND status = 'open'",
            (str(guild_id), str(user_id))
        ) as cur:
            return await cur.fetchone() is not None


async def _is_staff(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    config = await _get_config(interaction.guild.id)
    role_id = config.get("staff_role_id")
    if role_id:
        role = interaction.guild.get_role(int(role_id))
        if role and role in interaction.user.roles:
            return True
    return False


# ─── Transcript ───────────────────────────────────────────────────────────────

async def _save_transcript(channel: discord.TextChannel, ticket: dict) -> str:
    lines = [
        f"=== Ticket #{ticket['ticket_number']:04d} Transcript ===",
        f"Guild      : {ticket['guild_id']}",
        f"User       : {ticket['user_id']}",
        f"Category   : {ticket['category'].title()}",
        f"Claimed by : {ticket.get('claimed_by') or 'Not claimed'}",
        f"Reason     : {ticket.get('close_reason') or 'N/A'}",
        f"Rating     : {ticket.get('rating') or 'Not rated'}",
        "=" * 42, "",
    ]
    async for msg in channel.history(limit=500, oldest_first=True):
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content or ""
        for emb in msg.embeds:
            parts = []
            if emb.title:       parts.append(f"[Title: {emb.title}]")
            if emb.description: parts.append(f"[{emb.description}]")
            content = (content + " " + " ".join(parts)).strip()
        lines.append(f"[{ts}] {msg.author} ({msg.author.id}): {content}")

    path = TRANSCRIPTS_DIR / f"ticket-{ticket['ticket_number']:04d}-{ticket['guild_id']}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return str(path)


# ─── Core Logic ───────────────────────────────────────────────────────────────

async def create_ticket(interaction: discord.Interaction, category: str) -> None:
    guild = interaction.guild
    user  = interaction.user

    # Check for existing open ticket
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT channel_id FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'open'",
            (str(guild.id), str(user.id))
        ) as cur:
            existing = await cur.fetchone()

    if existing:
        ch = guild.get_channel(int(existing[0]))
        ref = ch.mention if ch else "an existing channel"
        return await interaction.response.send_message(
            embed=warn(f"You already have an open ticket: {ref}"),
            ephemeral=True,
        )

    config = await _get_config(guild.id)
    cat_name, cat_id = CATEGORY_MAP[category]
    discord_category = guild.get_channel(cat_id)

    num  = await _bump_counter(guild.id)
    slug = user.name[:16].lower().replace(" ", "-")
    channel_name = f"ticket-{num:04d}-{slug}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user:               discord.PermissionOverwrite(
            view_channel=True, send_messages=True,
            read_message_history=True, attach_files=True
        ),
        guild.me:           discord.PermissionOverwrite(
            view_channel=True, send_messages=True,
            manage_channels=True, manage_messages=True
        ),
    }
    staff_role_id = config.get("staff_role_id")
    staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None
    if staff_role:
        # Staff can READ the channel but cannot SEND messages until they claim it
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=False,
            read_message_history=True, attach_files=False
        )

    try:
        channel = await guild.create_text_channel(
            channel_name,
            category=discord_category,
            overwrites=overwrites,
            topic=f"Ticket #{num:04d} | {cat_name} | Opened by {user}",
        )
    except discord.Forbidden:
        return await interaction.response.send_message(
            embed=error("I don't have permission to create channels in that category."),
            ephemeral=True,
        )

    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tickets (guild_id, channel_id, user_id, category, open_time, ticket_number) VALUES (?,?,?,?,?,?)",
            (str(guild.id), str(channel.id), str(user.id), category, now, num),
        )
        await db.commit()

    await interaction.response.send_message(
        embed=success(f"Ticket opened: {channel.mention}"), ephemeral=True
    )

    embed = discord.Embed(
        title=f"{cat_name} — Ticket #{num:04d}",
        description=(
            f"Welcome {user.mention}! A staff member will assist you shortly.\n\n"
            f"**Category:** {cat_name}\n"
            f"**Opened:** <t:{now}:R>\n\n"
            f"> 👮 **Staff:** You must press **Claim** before you can respond to this ticket.\n"
            f"> Only the staff member who claims it may close it."
        ),
        color=COLOR_BRAND,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    embed.set_footer(text="KaluxHost Support | Staff: claim before responding")
    await channel.send(embed=embed, view=TicketControlView())

    if staff_role:
        ping = await channel.send(
            f"{staff_role.mention} — New **{cat_name}** ticket from {user.mention}",
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
        )
        await asyncio.sleep(6)
        try:
            await ping.delete()
        except Exception:
            pass


async def handle_claim(interaction: discord.Interaction) -> None:
    ticket = await _get_ticket_by_channel(interaction.channel.id)
    if not ticket:
        return await interaction.response.send_message(embed=error("Ticket not found."), ephemeral=True)
    if ticket["status"] != "open":
        return await interaction.response.send_message(embed=error("This ticket is not open."), ephemeral=True)
    if ticket["claimed_by"]:
        claimer = interaction.guild.get_member(int(ticket["claimed_by"]))
        name = claimer.display_name if claimer else f"<@{ticket['claimed_by']}>"
        return await interaction.response.send_message(
            embed=warn(f"Already claimed by **{name}**."), ephemeral=True
        )

    if not await _is_staff(interaction):
        return await interaction.response.send_message(embed=error("Only staff can claim tickets."), ephemeral=True)

    if await _has_active_claim(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message(
            embed=error("You already have an active claimed ticket. Close it first before claiming another."),
            ephemeral=True,
        )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET claimed_by = ? WHERE channel_id = ?",
            (str(interaction.user.id), str(interaction.channel.id)),
        )
        await db.commit()

    # Grant claimer individual send_messages so they can now respond
    try:
        await interaction.channel.set_permissions(
            interaction.user,
            view_channel=True, send_messages=True,
            read_message_history=True, attach_files=True,
        )
    except Exception:
        pass

    await interaction.response.send_message(
        embed=success(f"✋ {interaction.user.mention} has claimed this ticket and can now respond.")
    )
    try:
        await interaction.channel.edit(
            topic=f"{interaction.channel.topic} | Claimed by {interaction.user}"
        )
    except Exception:
        pass


async def handle_close(interaction: discord.Interaction) -> None:
    ticket = await _get_ticket_by_channel(interaction.channel.id)
    if not ticket:
        return await interaction.response.send_message(embed=error("Ticket not found."), ephemeral=True)
    if ticket["status"] != "open":
        return await interaction.response.send_message(embed=error("Already closed."), ephemeral=True)

    is_owner = str(interaction.user.id) == ticket["user_id"]
    is_claimer = ticket.get("claimed_by") and str(interaction.user.id) == ticket["claimed_by"]
    staff = await _is_staff(interaction)

    if is_owner:
        # User closing their own ticket — allowed anytime, no reason needed
        await _finalize_close(interaction, ticket, reason=None, by_user=True)
        return

    if staff or is_claimer:
        if not ticket.get("claimed_by"):
            return await interaction.response.send_message(
                embed=error("You must **claim** this ticket before closing it."), ephemeral=True
            )
        if not is_claimer and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                embed=error("Only the staff member who **claimed** this ticket can close it."), ephemeral=True
            )
        # Show reason modal
        await interaction.response.send_modal(CloseReasonModal(ticket["id"]))
        return

    await interaction.response.send_message(embed=error("You cannot close this ticket."), ephemeral=True)


async def _finalize_close(
    interaction: discord.Interaction,
    ticket: dict,
    reason: str | None,
    by_user: bool = False,
) -> None:
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status='closed', close_time=?, close_reason=? WHERE id=?",
            (now, reason, ticket["id"]),
        )
        await db.commit()

    # Reload fresh
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tickets WHERE id=?", (ticket["id"],)) as cur:
            ticket = dict(await cur.fetchone())

    was_claimed = bool(ticket.get("claimed_by"))
    channel     = interaction.channel
    guild       = interaction.guild

    # Acknowledge
    if not by_user:
        try:
            await interaction.response.send_message(embed=success("Closing ticket…"), ephemeral=True)
        except Exception:
            pass
    else:
        await interaction.response.send_message(embed=success("Closing ticket…"), ephemeral=True)

    # Lock channel
    user_member = guild.get_member(int(ticket["user_id"]))
    try:
        await channel.set_permissions(guild.default_role, view_channel=False, send_messages=False)
        if user_member:
            await channel.set_permissions(
                user_member, view_channel=True, send_messages=False, read_message_history=True
            )
    except Exception:
        pass

    close_embed = discord.Embed(
        title="🔒 Ticket Closed",
        color=0xED4245,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    close_embed.add_field(name="Closed by", value=interaction.user.mention,  inline=True)
    close_embed.add_field(name="Reason",    value=reason or "User closed",   inline=True)
    close_embed.set_footer(text="KaluxHost Support")
    await channel.send(embed=close_embed)

    if was_claimed:
        user_ref = user_member.mention if user_member else f"<@{ticket['user_id']}>"
        rate_embed = discord.Embed(
            description=(
                f"{user_ref} — How was your support experience?\n"
                "Please rate your ticket from **1 to 5 ⭐**"
            ),
            color=COLOR_BRAND,
        )
        rate_embed.set_footer(text="KaluxHost Support | Your feedback helps us improve.")
        await channel.send(embed=rate_embed, view=RatingView())
    else:
        staff_embed = discord.Embed(
            description="This ticket was **not claimed**. Staff: choose an action.",
            color=0xFEE75C,
        )
        await channel.send(embed=staff_embed, view=StaffActionView())


async def handle_rating(interaction: discord.Interaction, stars: int) -> None:
    ticket = await _get_ticket_by_channel(interaction.channel.id)
    if not ticket:
        return await interaction.response.send_message(embed=error("Ticket not found."), ephemeral=True)
    if str(interaction.user.id) != ticket["user_id"]:
        return await interaction.response.send_message(embed=error("Only the ticket owner can rate."), ephemeral=True)
    if ticket.get("rating"):
        return await interaction.response.send_message(embed=warn("You already rated this ticket."), ephemeral=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tickets SET rating=? WHERE id=?", (stars, ticket["id"]))
        await db.commit()

    # Update staff stats
    if ticket.get("claimed_by"):
        await _ensure_staff_row(ticket["guild_id"], ticket["claimed_by"])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE staff_stats
                SET tickets_handled = tickets_handled + 1,
                    total_rating    = total_rating + ?,
                    rating_count    = rating_count + 1
                WHERE guild_id = ? AND user_id = ?
            """, (stars, ticket["guild_id"], ticket["claimed_by"]))
            await db.commit()

    star_str = "⭐" * stars
    await interaction.response.send_message(
        embed=success(f"Thank you! You rated this ticket **{star_str}** ({stars}/5)")
    )
    try:
        await interaction.message.edit(view=None)
    except Exception:
        pass

    # Hide channel from user
    user_member = interaction.guild.get_member(int(ticket["user_id"]))
    if user_member:
        try:
            await interaction.channel.set_permissions(user_member, view_channel=False)
        except Exception:
            pass

    staff_embed = discord.Embed(
        description=f"User rated this ticket **{stars}/5** {star_str}\nStaff: delete or reopen below.",
        color=COLOR_BRAND,
    )
    await interaction.channel.send(embed=staff_embed, view=StaffActionView())


async def handle_delete(interaction: discord.Interaction) -> None:
    ticket = await _get_ticket_by_channel(interaction.channel.id)
    if not ticket:
        return await interaction.response.send_message(embed=error("Ticket not found."), ephemeral=True)
    if not await _is_staff(interaction):
        return await interaction.response.send_message(embed=error("Staff only."), ephemeral=True)

    await interaction.response.send_message(embed=success("Saving transcript and deleting…"), ephemeral=True)

    transcript_path = await _save_transcript(interaction.channel, ticket)
    config = await _get_config(interaction.guild.id)
    log_ch_id = config.get("log_channel_id")

    if log_ch_id:
        log_ch = interaction.guild.get_channel(int(log_ch_id))
        if log_ch:
            opener  = interaction.guild.get_member(int(ticket["user_id"]))
            claimer = interaction.guild.get_member(int(ticket["claimed_by"])) if ticket.get("claimed_by") else None
            stars   = ticket.get("rating")
            star_str = ("⭐" * stars + f" ({stars}/5)") if stars else "Not rated"

            log_embed = discord.Embed(
                title=f"📋 Ticket #{ticket['ticket_number']:04d} — Log",
                color=COLOR_BRAND,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            log_embed.add_field(name="Category",    value=ticket["category"].title(),                               inline=True)
            log_embed.add_field(name="Opened by",   value=opener.mention  if opener  else f"<@{ticket['user_id']}>", inline=True)
            log_embed.add_field(name="Claimed by",  value=claimer.mention if claimer else "Not claimed",             inline=True)
            log_embed.add_field(name="Closed by",   value=interaction.user.mention,                                  inline=True)
            log_embed.add_field(name="Close reason",value=ticket.get("close_reason") or "N/A",                       inline=True)
            log_embed.add_field(name="Rating",       value=star_str,                                                  inline=True)
            log_embed.add_field(
                name="Opened",
                value=f"<t:{ticket['open_time']}:F>" if ticket.get("open_time") else "N/A",
                inline=True,
            )
            log_embed.add_field(
                name="Closed",
                value=f"<t:{ticket['close_time']}:F>" if ticket.get("close_time") else "N/A",
                inline=True,
            )
            log_embed.set_footer(text=f"KaluxHost | Ticket #{ticket['ticket_number']:04d}")
            try:
                await log_ch.send(
                    embed=log_embed,
                    file=discord.File(transcript_path, filename=f"transcript-{ticket['ticket_number']:04d}.txt"),
                )
            except Exception:
                await log_ch.send(embed=log_embed)

    await asyncio.sleep(2)
    try:
        await interaction.channel.delete(reason=f"Ticket #{ticket['ticket_number']:04d} closed")
    except Exception:
        pass


async def handle_reopen(interaction: discord.Interaction) -> None:
    ticket = await _get_ticket_by_channel(interaction.channel.id)
    if not ticket:
        return await interaction.response.send_message(embed=error("Ticket not found."), ephemeral=True)
    if not await _is_staff(interaction):
        return await interaction.response.send_message(embed=error("Staff only."), ephemeral=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE tickets
            SET status='open', claimed_by=NULL, close_time=NULL, close_reason=NULL, rating=NULL
            WHERE id=?
        """, (ticket["id"],))
        await db.commit()

    config      = await _get_config(interaction.guild.id)
    old_claimer = interaction.guild.get_member(int(ticket["claimed_by"])) if ticket.get("claimed_by") else None
    user_member = interaction.guild.get_member(int(ticket["user_id"]))
    staff_role  = interaction.guild.get_role(int(config["staff_role_id"])) if config.get("staff_role_id") else None

    try:
        # Restore user access
        if user_member:
            await interaction.channel.set_permissions(
                user_member, view_channel=True, send_messages=True, read_message_history=True
            )
        # Reset staff role back to read-only (must claim again)
        if staff_role:
            await interaction.channel.set_permissions(
                staff_role, view_channel=True, send_messages=False, read_message_history=True
            )
        # Remove the old claimer's individual overwrite (they must claim again)
        if old_claimer:
            await interaction.channel.set_permissions(old_claimer, overwrite=None)
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
    except Exception:
        pass

    await interaction.response.send_message(embed=success("Ticket reopened."))

    reopen_embed = discord.Embed(
        title=f"🔓 Ticket Reopened — #{ticket['ticket_number']:04d}",
        description=f"Reopened by {interaction.user.mention}",
        color=COLOR_BRAND,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    reopen_embed.set_footer(text="KaluxHost Support")
    await interaction.channel.send(embed=reopen_embed, view=TicketControlView())


# ─── Views (Persistent) ───────────────────────────────────────────────────────

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="General",  emoji="🎫", style=discord.ButtonStyle.primary, custom_id="kalux:t:open:general")
    async def btn_general(self, interaction: discord.Interaction, _):
        await create_ticket(interaction, "general")

    @discord.ui.button(label="Billing",  emoji="💳", style=discord.ButtonStyle.success, custom_id="kalux:t:open:billing")
    async def btn_billing(self, interaction: discord.Interaction, _):
        await create_ticket(interaction, "billing")

    @discord.ui.button(label="Report",   emoji="🚨", style=discord.ButtonStyle.danger,  custom_id="kalux:t:open:report")
    async def btn_report(self, interaction: discord.Interaction, _):
        await create_ticket(interaction, "report")


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim",         emoji="🙋", style=discord.ButtonStyle.primary, custom_id="kalux:t:claim")
    async def btn_claim(self, interaction: discord.Interaction, _):
        await handle_claim(interaction)

    @discord.ui.button(label="Close Ticket",  emoji="🔒", style=discord.ButtonStyle.danger,  custom_id="kalux:t:close")
    async def btn_close(self, interaction: discord.Interaction, _):
        await handle_close(interaction)


class CloseReasonModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(
        label="Reason for closing",
        placeholder="Why is this ticket being closed?",
        min_length=3,
        max_length=500,
    )

    def __init__(self, ticket_id: int):
        super().__init__()
        self.ticket_id = ticket_id

    async def on_submit(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tickets WHERE id=?", (self.ticket_id,)) as cur:
                ticket = dict(await cur.fetchone())
        await _finalize_close(interaction, ticket, reason=str(self.reason), by_user=False)


class RatingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="1 ⭐", style=discord.ButtonStyle.secondary, custom_id="kalux:t:rate:1")
    async def r1(self, i: discord.Interaction, _): await handle_rating(i, 1)

    @discord.ui.button(label="2 ⭐", style=discord.ButtonStyle.secondary, custom_id="kalux:t:rate:2")
    async def r2(self, i: discord.Interaction, _): await handle_rating(i, 2)

    @discord.ui.button(label="3 ⭐", style=discord.ButtonStyle.secondary, custom_id="kalux:t:rate:3")
    async def r3(self, i: discord.Interaction, _): await handle_rating(i, 3)

    @discord.ui.button(label="4 ⭐", style=discord.ButtonStyle.secondary, custom_id="kalux:t:rate:4")
    async def r4(self, i: discord.Interaction, _): await handle_rating(i, 4)

    @discord.ui.button(label="5 ⭐", style=discord.ButtonStyle.success,   custom_id="kalux:t:rate:5")
    async def r5(self, i: discord.Interaction, _): await handle_rating(i, 5)


class StaffActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket", emoji="🗑️", style=discord.ButtonStyle.danger,  custom_id="kalux:t:delete")
    async def btn_delete(self, i: discord.Interaction, _): await handle_delete(i)

    @discord.ui.button(label="Reopen",         emoji="🔓", style=discord.ButtonStyle.success, custom_id="kalux:t:reopen")
    async def btn_reopen(self, i: discord.Interaction, _): await handle_reopen(i)


# ─── Cog ─────────────────────────────────────────────────────────────────────

class Tickets(commands.Cog, name="Tickets"):
    """🎫 Ticket system with claims, ratings, transcripts & staff stats."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Config ────────────────────────────────────────────────────────────────

    @commands.command(name="setstaffrole", aliases=["staffrole"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setstaffrole_cmd(self, ctx: commands.Context, role: discord.Role):
        """Set the staff role (pinged on new tickets, can claim/close)."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO ticket_config (guild_id, staff_role_id) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET staff_role_id = excluded.staff_role_id
            """, (str(ctx.guild.id), str(role.id)))
            await db.commit()
        await ctx.reply(embed=success(f"Staff role set to {role.mention}"), mention_author=False)

    @commands.command(name="setlogchannel", aliases=["logchannel"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setlogchannel_cmd(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the channel where closed ticket logs are sent."""
        ch = channel or ctx.channel
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO ticket_config (guild_id, log_channel_id) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET log_channel_id = excluded.log_channel_id
            """, (str(ctx.guild.id), str(ch.id)))
            await db.commit()
        await ctx.reply(embed=success(f"Log channel set to {ch.mention}"), mention_author=False)

    # ── !ticket ───────────────────────────────────────────────────────────────

    @commands.command(name="ticket", aliases=["new", "openticket"])
    @commands.guild_only()
    async def ticket_cmd(self, ctx: commands.Context):
        """Open a support ticket — select a category."""
        embed = discord.Embed(
            title="🎫 KaluxHost Support",
            description=(
                "Select the category that best fits your issue:\n\n"
                "🎫 **General** — General support & questions\n"
                "💳 **Billing** — Payments, invoices & billing issues\n"
                "🚨 **Report** — Report a user or incident"
            ),
            color=COLOR_BRAND,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_footer(text="KaluxHost Support | One ticket per user")
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(embed=embed, view=TicketOpenView())

    # ── Duty ──────────────────────────────────────────────────────────────────

    @commands.command(name="on", aliases=["onduty"])
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def on_duty(self, ctx: commands.Context):
        """Go on duty — tracks active support time."""
        if not await _is_staff_ctx(ctx):
            return await ctx.reply(embed=error("Staff only."), mention_author=False)

        await _ensure_staff_row(ctx.guild.id, ctx.author.id)
        stats = await _get_staff_stats(ctx.guild.id, ctx.author.id)

        if stats.get("on_duty_since"):
            return await ctx.reply(embed=warn("You are already on duty."), mention_author=False)

        # Abuse prevention: must wait 5 min after going off before going on again
        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        last_off = stats.get("last_off_duty")
        if last_off:
            cooldown_remaining = 300 - (now - last_off)
            if cooldown_remaining > 0:
                return await ctx.reply(
                    embed=warn(
                        f"You must wait **{cooldown_remaining}s** before going on duty again.\n"
                        f"This prevents rapid on/off cycling."
                    ),
                    mention_author=False,
                )

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE staff_stats SET on_duty_since=? WHERE guild_id=? AND user_id=?",
                (now, str(ctx.guild.id), str(ctx.author.id)),
            )
            await db.commit()
        await ctx.reply(
            embed=success(f"🟢 **{ctx.author.display_name}** is now **on duty** — <t:{now}:R>"),
            mention_author=False,
        )

    @commands.command(name="off", aliases=["offduty"])
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def off_duty(self, ctx: commands.Context):
        """Go off duty — logs the session time."""
        if not await _is_staff_ctx(ctx):
            return await ctx.reply(embed=error("Staff only."), mention_author=False)

        await _ensure_staff_row(ctx.guild.id, ctx.author.id)
        stats = await _get_staff_stats(ctx.guild.id, ctx.author.id)

        if not stats.get("on_duty_since"):
            return await ctx.reply(embed=warn("You are not currently on duty."), mention_author=False)

        now          = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        session_secs = now - stats["on_duty_since"]

        # Abuse prevention: minimum 5-minute session before going off
        MIN_SESSION = 300  # 5 minutes
        if session_secs < MIN_SESSION:
            remaining = MIN_SESSION - session_secs
            return await ctx.reply(
                embed=warn(
                    f"You must be on duty for at least **5 minutes** before going off.\n"
                    f"Time remaining: **{remaining}s**"
                ),
                mention_author=False,
            )

        new_total = (stats["total_duty_secs"] or 0) + session_secs
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE staff_stats SET on_duty_since=NULL, total_duty_secs=?, last_off_duty=? WHERE guild_id=? AND user_id=?",
                (new_total, now, str(ctx.guild.id), str(ctx.author.id)),
            )
            await db.commit()

        await ctx.reply(
            embed=success(
                f"🔴 **{ctx.author.display_name}** is now **off duty**.\n"
                f"Session: **{_fmt_duration(session_secs)}** | Total worked: **{_fmt_duration(new_total)}**"
            ),
            mention_author=False,
        )

    # ── Unclaim ───────────────────────────────────────────────────────────────

    @commands.command(name="unclaim")
    @commands.guild_only()
    async def unclaim_cmd(self, ctx: commands.Context):
        """Unclaim the current ticket — only the staff who claimed it can do this."""
        ticket = await _get_ticket_by_channel(ctx.channel.id)
        if not ticket:
            return await ctx.reply(embed=error("This is not a ticket channel."), mention_author=False)
        if ticket["status"] != "open":
            return await ctx.reply(embed=error("This ticket is not open."), mention_author=False)
        if not ticket.get("claimed_by"):
            return await ctx.reply(embed=warn("This ticket is not currently claimed."), mention_author=False)
        if str(ctx.author.id) != ticket["claimed_by"]:
            claimer = ctx.guild.get_member(int(ticket["claimed_by"]))
            name = claimer.display_name if claimer else f"<@{ticket['claimed_by']}>"
            return await ctx.reply(
                embed=error(f"Only **{name}** (who claimed this ticket) can unclaim it."),
                mention_author=False,
            )

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE tickets SET claimed_by=NULL WHERE channel_id=?",
                (str(ctx.channel.id),),
            )
            await db.commit()

        config     = await _get_config(ctx.guild.id)
        staff_role = ctx.guild.get_role(int(config["staff_role_id"])) if config.get("staff_role_id") else None
        try:
            await ctx.channel.set_permissions(ctx.author, overwrite=None)
            if staff_role:
                await ctx.channel.set_permissions(
                    staff_role, view_channel=True, send_messages=False, read_message_history=True
                )
        except Exception:
            pass

        try:
            topic = ctx.channel.topic or ""
            new_topic = topic.replace(f" | Claimed by {ctx.author}", "").strip()
            await ctx.channel.edit(topic=new_topic)
        except Exception:
            pass

        await ctx.reply(
            embed=success(
                f"↩️ **{ctx.author.display_name}** has unclaimed this ticket.\n"
                f"It is now available for any staff member to claim."
            ),
            mention_author=False,
        )

    # ── Listener: remind unclaimed staff ──────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Warn staff who message in a ticket they haven't claimed."""
        if message.author.bot or not message.guild:
            return

        ticket = await _get_ticket_by_channel(message.channel.id)
        if not ticket or ticket["status"] != "open":
            return

        if str(message.author.id) == ticket["user_id"]:
            return

        config        = await _get_config(message.guild.id)
        is_admin      = message.author.guild_permissions.administrator
        staff_role_id = config.get("staff_role_id")
        is_staff_role = False
        if staff_role_id:
            role = message.guild.get_role(int(staff_role_id))
            if role and role in message.author.roles:
                is_staff_role = True

        if not (is_admin or is_staff_role):
            return

        claimed_by = ticket.get("claimed_by")
        if claimed_by and str(message.author.id) == claimed_by:
            return

        if not claimed_by:
            text = (
                f"{message.author.mention} — this ticket is **not claimed** yet.\n"
                f"Please press the **Claim** button before responding to it!"
            )
        else:
            claimer = message.guild.get_member(int(claimed_by))
            name    = claimer.display_name if claimer else f"<@{claimed_by}>"
            text    = (
                f"{message.author.mention} — this ticket is already claimed by **{name}**.\n"
                f"Please don't respond to tickets claimed by other staff."
            )

        try:
            await message.channel.send(embed=warn(text), delete_after=12)
        except Exception:
            pass

    # ── Rep ───────────────────────────────────────────────────────────────────

    @commands.command(name="rep")
    @commands.guild_only()
    async def rep_cmd(self, ctx: commands.Context, member: discord.Member):
        """Give a rep to a staff member (once per 24h per person)."""
        if member.id == ctx.author.id:
            return await ctx.reply(embed=error("You cannot rep yourself."), mention_author=False)
        if member.bot:
            return await ctx.reply(embed=error("You cannot rep a bot."), mention_author=False)

        cutoff = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).timestamp())
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("""
                SELECT 1 FROM reps
                WHERE guild_id=? AND from_user_id=? AND to_user_id=? AND created_at>?
            """, (str(ctx.guild.id), str(ctx.author.id), str(member.id), cutoff)) as cur:
                if await cur.fetchone():
                    return await ctx.reply(
                        embed=warn("You already repped that person in the last 24 hours."), mention_author=False
                    )

        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO reps (guild_id, from_user_id, to_user_id, created_at) VALUES (?,?,?,?)",
                (str(ctx.guild.id), str(ctx.author.id), str(member.id), now),
            )
            await db.commit()

        await _ensure_staff_row(ctx.guild.id, member.id)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE staff_stats SET rep_count=rep_count+1 WHERE guild_id=? AND user_id=?",
                (str(ctx.guild.id), str(member.id)),
            )
            await db.commit()

        stats = await _get_staff_stats(ctx.guild.id, member.id)
        await ctx.reply(
            embed=success(
                f"👍 Repped **{member.display_name}**!\n"
                f"They now have **{stats['rep_count']}** rep(s)."
            ),
            mention_author=False,
        )

    # ── Stats & Leaderboard ───────────────────────────────────────────────────

    @commands.command(name="staffstats", aliases=["stats", "mystats"])
    @commands.guild_only()
    async def staffstats_cmd(self, ctx: commands.Context, member: discord.Member = None):
        """View staff stats — tickets handled, rating, reps, duty time."""
        m     = member or ctx.author
        stats = await _get_staff_stats(ctx.guild.id, m.id)

        avg     = (stats["total_rating"] / stats["rating_count"]) if stats["rating_count"] else 0
        rating  = f"{avg:.1f}/5 ⭐ ({stats['rating_count']} review(s))" if stats["rating_count"] else "No reviews yet"

        total_secs = stats["total_duty_secs"] or 0
        status_dot = "🔴 Off Duty"
        if stats.get("on_duty_since"):
            now         = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            total_secs += now - stats["on_duty_since"]
            status_dot  = "🟢 On Duty"

        embed = discord.Embed(
            title=f"📊 Staff Stats — {m.display_name}",
            color=COLOR_BRAND,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="Duty Status",      value=status_dot,                         inline=True)
        embed.add_field(name="Total Worked",     value=_fmt_duration(total_secs),           inline=True)
        embed.add_field(name="Tickets Handled",  value=str(stats["tickets_handled"]),       inline=True)
        embed.add_field(name="Avg Rating",       value=rating,                              inline=True)
        embed.add_field(name="Reps",             value=f"👍 {stats['rep_count']}",           inline=True)
        embed.set_footer(text=f"KaluxHost | ID: {m.id}")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="leaderboard", aliases=["lb", "stafflb"])
    @commands.guild_only()
    async def leaderboard_cmd(self, ctx: commands.Context):
        """Staff leaderboard — ranked by tickets, rating, and reps."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM staff_stats WHERE guild_id=?
                ORDER BY tickets_handled DESC, rep_count DESC, rating_count DESC
                LIMIT 10
            """, (str(ctx.guild.id),)) as cur:
                rows = await cur.fetchall()

        if not rows:
            return await ctx.reply(embed=warn("No staff stats recorded yet."), mention_author=False)

        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines  = []
        for i, row in enumerate(rows):
            m    = ctx.guild.get_member(int(row["user_id"]))
            name = m.display_name if m else f"<@{row['user_id']}>"
            avg  = (row["total_rating"] / row["rating_count"]) if row["rating_count"] else 0
            duty = "🟢" if row["on_duty_since"] else "🔴"
            lines.append(
                f"{medals[i]} **{name}** {duty}\n"
                f"  Tickets: `{row['tickets_handled']}` · Rating: `{avg:.1f}⭐` · Reps: `{row['rep_count']}`"
            )

        embed = discord.Embed(
            title="🏆 KaluxHost Staff Leaderboard",
            description="\n".join(lines),
            color=COLOR_BRAND,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_footer(text="KaluxHost Support Team")
        await ctx.reply(embed=embed, mention_author=False)

    # ── Slash Variants ────────────────────────────────────────────────────────

    @app_commands.command(name="ticket", description="Open a support ticket")
    @app_commands.guild_only()
    async def slash_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 KaluxHost Support",
            description=(
                "Select a category:\n\n"
                "🎫 **General** · 💳 **Billing** · 🚨 **Report**"
            ),
            color=COLOR_BRAND,
        )
        embed.set_footer(text="KaluxHost Support")
        await interaction.response.send_message(embed=embed, view=TicketOpenView(), ephemeral=True)

    @app_commands.command(name="staffstats", description="View staff stats")
    @app_commands.guild_only()
    async def slash_staffstats(self, interaction: discord.Interaction, member: discord.Member = None):
        m     = member or interaction.user
        stats = await _get_staff_stats(interaction.guild.id, m.id)
        avg   = (stats["total_rating"] / stats["rating_count"]) if stats["rating_count"] else 0
        rating = f"{avg:.1f}/5 ⭐ ({stats['rating_count']} review(s))" if stats["rating_count"] else "No reviews yet"
        total_secs = stats["total_duty_secs"] or 0
        duty_status = "🔴 Off Duty"
        if stats.get("on_duty_since"):
            total_secs += int(datetime.datetime.now(datetime.timezone.utc).timestamp()) - stats["on_duty_since"]
            duty_status = "🟢 On Duty"
        embed = discord.Embed(title=f"📊 Staff Stats — {m.display_name}", color=COLOR_BRAND)
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="Duty Status",     value=duty_status,               inline=True)
        embed.add_field(name="Total Worked",    value=_fmt_duration(total_secs), inline=True)
        embed.add_field(name="Tickets Handled", value=str(stats["tickets_handled"]), inline=True)
        embed.add_field(name="Avg Rating",      value=rating,                    inline=True)
        embed.add_field(name="Reps",            value=f"👍 {stats['rep_count']}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rep", description="Give a rep to a staff member")
    @app_commands.guild_only()
    async def slash_rep(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message(embed=error("Can't rep yourself."), ephemeral=True)
        cutoff = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).timestamp())
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("""
                SELECT 1 FROM reps WHERE guild_id=? AND from_user_id=? AND to_user_id=? AND created_at>?
            """, (str(interaction.guild.id), str(interaction.user.id), str(member.id), cutoff)) as cur:
                if await cur.fetchone():
                    return await interaction.response.send_message(
                        embed=warn("Already repped in last 24h."), ephemeral=True
                    )
        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO reps (guild_id, from_user_id, to_user_id, created_at) VALUES (?,?,?,?)",
                (str(interaction.guild.id), str(interaction.user.id), str(member.id), now),
            )
            await db.commit()
        await _ensure_staff_row(interaction.guild.id, member.id)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE staff_stats SET rep_count=rep_count+1 WHERE guild_id=? AND user_id=?",
                (str(interaction.guild.id), str(member.id)),
            )
            await db.commit()
        stats = await _get_staff_stats(interaction.guild.id, member.id)
        await interaction.response.send_message(
            embed=success(f"👍 Repped **{member.display_name}**! Total: **{stats['rep_count']}** rep(s).")
        )

    @app_commands.command(name="leaderboard", description="View the staff leaderboard")
    @app_commands.guild_only()
    async def slash_leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM staff_stats WHERE guild_id=?
                ORDER BY tickets_handled DESC, rep_count DESC LIMIT 10
            """, (str(interaction.guild.id),)) as cur:
                rows = await cur.fetchall()
        if not rows:
            return await interaction.response.send_message(embed=warn("No stats yet."), ephemeral=True)
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines  = []
        for i, row in enumerate(rows):
            m    = interaction.guild.get_member(int(row["user_id"]))
            name = m.display_name if m else f"<@{row['user_id']}>"
            avg  = (row["total_rating"] / row["rating_count"]) if row["rating_count"] else 0
            duty = "🟢" if row["on_duty_since"] else "🔴"
            lines.append(f"{medals[i]} **{name}** {duty} — `{row['tickets_handled']}` tickets · `{avg:.1f}⭐` · `{row['rep_count']}` reps")
        embed = discord.Embed(title="🏆 KaluxHost Staff Leaderboard", description="\n".join(lines), color=COLOR_BRAND)
        await interaction.response.send_message(embed=embed)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fmt_duration(total_seconds: int) -> str:
    if total_seconds <= 0:
        return "0m"
    d = total_seconds // 86400
    h = (total_seconds % 86400) // 3600
    m = (total_seconds % 3600) // 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m or not parts: parts.append(f"{m}m")
    return " ".join(parts)


async def _is_staff_ctx(ctx: commands.Context) -> bool:
    if ctx.author.guild_permissions.administrator:
        return True
    config = await _get_config(ctx.guild.id)
    role_id = config.get("staff_role_id")
    if role_id:
        role = ctx.guild.get_role(int(role_id))
        if role and role in ctx.author.roles:
            return True
    return False


# ─── Setup ────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot) -> None:
    await _init_db()
    bot.add_view(TicketOpenView())
    bot.add_view(TicketControlView())
    bot.add_view(RatingView())
    bot.add_view(StaffActionView())
    await bot.add_cog(Tickets(bot))
