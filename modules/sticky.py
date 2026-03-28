import discord
from discord.ext import commands
import aiosqlite
import aiohttp
from main.config import DB_PATH, COLOR_BRAND
from main.utils.embeds import success, brand, error

class Sticky(commands.Cog, name="Sticky"):
    """📌 Premium Sticky Messages & Polls for KaluxHost."""

    def __init__(self, bot):
        self.bot = bot
        # Cache format: {channel_id: {"content": str, "last_id": int, "count": int, "slow": bool, "image": str, "webhook": str}}
        self.cache = {}

    async def cog_load(self):
        """Initialize DB and perform migrations for all premium features."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sticky_messages (
                    channel_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    is_slow INTEGER DEFAULT 0,
                    image_url TEXT,
                    webhook_url TEXT
                )
            """)
            
            # Migration: Add new columns if they don't exist
            cols = [("is_slow", "INTEGER DEFAULT 0"), ("image_url", "TEXT"), ("webhook_url", "TEXT")]
            for col_name, col_type in cols:
                try:
                    await db.execute(f"ALTER TABLE sticky_messages ADD COLUMN {col_name} {col_type}")
                except aiosqlite.OperationalError:
                    pass 
            
            await db.commit()

            # Load existing stickies into memory
            async with db.execute("SELECT * FROM sticky_messages") as cursor:
                async for row in cursor:
                    self.cache[int(row[0])] = {
                        "content": row[1], "last_id": None, "count": 0, 
                        "slow": bool(row[2]), "image": row[3], "webhook": row[4]
                    }

    # ── Sticky Commands ───────────────────────────────────────────────────────

    @commands.command(name="stickembed")
    @commands.has_permissions(manage_messages=True)
    async def stick_embed(self, ctx, *, message: str):
        """[cite: 20, 22] Create a standard sticky embed."""
        await self._update_sticky(ctx, message, slow=False)
        await ctx.send(embed=success("Standard sticky activated."))

    @commands.command(name="stickslow")
    @commands.has_permissions(manage_messages=True)
    async def stick_slow(self, ctx, *, message: str):
        """[cite: 24, 26] Sticky that posts every 13 messages (approx 35s)."""
        await self._update_sticky(ctx, message, slow=True)
        await ctx.send(embed=success("Slow sticky activated (13 message buffer)."))

    @commands.command(name="setwebhook")
    @commands.has_permissions(manage_guild=True)
    async def set_webhook(self, ctx, url: str):
        """[cite: 1, 12] Sets the WebHook URL (URL is deleted for security)."""
        await ctx.message.delete() 
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE sticky_messages SET webhook_url = ? WHERE channel_id = ?", (url, str(ctx.channel.id)))
            await db.commit()
        if ctx.channel.id in self.cache: 
            self.cache[ctx.channel.id]["webhook"] = url
        await ctx.send(embed=success("Webhook URL set successfully."), delete_after=5)

    @commands.command(name="setimage")
    @commands.has_permissions(manage_guild=True)
    async def set_image(self, ctx, url: str):
        """[cite: 27, 29] Sets a large banner image for the sticky."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE sticky_messages SET image_url = ? WHERE channel_id = ?", (url, str(ctx.channel.id)))
            await db.commit()
        if ctx.channel.id in self.cache: 
            self.cache[ctx.channel.id]["image"] = url
        await ctx.send(embed=success("Sticky image updated."))

    @commands.command(name="stickstop")
    @commands.has_permissions(manage_messages=True)
    async def stick_stop(self, ctx):
        """[cite: 17, 19, 23] Stop all stickies in this channel."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM sticky_messages WHERE channel_id = ?", (str(ctx.channel.id),))
            await db.commit()
        self.cache.pop(ctx.channel.id, None)
        await ctx.send(embed=brand("Stopped", "Sticky removed."))

    # ── Sticky Polls ─────────────────────────────────────────────────────────

    @commands.command(name="stickpoll")
    @commands.has_permissions(manage_messages=True)
    async def stick_poll(self, ctx, mode: str, *, question: str):
        """[cite: 60, 62] Create yes/no or multi-choice sticky polls."""
        if mode.lower() == "yesno":
            view = PollView(["Yes", "No"], question)
            await ctx.send(content=f"📊 **Poll:** {question}", view=view)
        elif mode.lower() == "multi":
            parts = [p.strip() for p in question.split(",")]
            if len(parts) < 3: 
                return await ctx.send(embed=error("Usage: !stickpoll multi Question, Opt1, Opt2"))
            view = PollView(parts[1:8], parts[0]) # [cite: 64] Max 7 options
            await ctx.send(content=f"📊 **Poll:** {parts[0]}", view=view)

    # ── Internal Logic ───────────────────────────────────────────────────────

    async def _update_sticky(self, ctx, content, slow):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO sticky_messages (channel_id, content, is_slow) VALUES (?, ?, ?)", 
                             (str(ctx.channel.id), content, 1 if slow else 0))
            await db.commit()
        self.cache[ctx.channel.id] = {"content": content, "last_id": None, "count": 0, "slow": slow, "image": None, "webhook": None}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id not in self.cache: 
            return
        
        data = self.cache[message.channel.id]
        data["count"] += 1
        
        # [cite: 26] Buffer for slow mode
        if data["slow"] and data["count"] < 13: 
            return

        data["count"] = 0
        if data["last_id"]:
            try:
                old = await message.channel.fetch_message(data["last_id"])
                await old.delete()
            except: 
                pass

        embed = discord.Embed(description=data["content"], color=COLOR_BRAND)
        if data["image"]: 
            embed.set_image(url=data["image"])
        
        # [cite: 8, 10] Use Webhook if configured
        if data["webhook"]:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(data["webhook"], session=session)
                msg = await webhook.send(embed=embed, wait=True, username="KaluxHost Sticky", avatar_url=self.bot.user.avatar.url)
                data["last_id"] = msg.id
        else:
            msg = await message.channel.send(embed=embed)
            data["last_id"] = msg.id

class PollView(discord.ui.View):
    """[cite: 72, 75] View for handling interactive poll buttons."""
    def __init__(self, options, question):
        super().__init__(timeout=None)
        self.results = {opt: 0 for opt in options}
        self.question = question
        for opt in options:
            btn = discord.ui.Button(label=opt, custom_id=f"poll_{opt}", style=discord.ButtonStyle.primary)
            btn.callback = self.create_callback(opt)
            self.add_item(btn)

    def create_callback(self, opt):
        async def callback(interaction):
            self.results[opt] += 1
            res_str = "\n".join([f"{k}: {v} votes" for k, v in self.results.items()])
            await interaction.response.edit_message(content=f"📊 **Poll:** {self.question}\n{res_str}")
        return callback

async def setup(bot):
    await bot.add_cog(Sticky(bot))
