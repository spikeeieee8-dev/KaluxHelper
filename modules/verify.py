import discord
from discord.ext import commands
import random
import aiosqlite

class VerifyView(discord.ui.View):
    def __init__(self, target_color, role):
        super().__init__(timeout=60)
        self.target_color = target_color
        self.role = role
        self.colors = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange']
        
        for index, color in enumerate(self.colors):
            style = self.get_style(color)
            row_num = 0 if index < 3 else 1
            button = discord.ui.Button(label=color, style=style, custom_id=color, row=row_num)
            button.callback = self.check_color
            self.add_item(button)

    def get_style(self, color):
        if color == 'Red': return discord.ButtonStyle.danger
        if color == 'Blue': return discord.ButtonStyle.primary
        if color == 'Green': return discord.ButtonStyle.success
        return discord.ButtonStyle.secondary

    async def check_color(self, interaction: discord.Interaction):
        if interaction.data['custom_id'] == self.target_color:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(f"✅ **Verified!** Access granted.", ephemeral=True)
            self.stop()
        else:
            await interaction.response.send_message(f"❌ **Wrong choice.** Please try again.", ephemeral=True)
            self.stop()

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "bot_data.db"

    async def get_saved_role(self, guild_id):
        """Fetches the role ID from the database"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT role_id FROM verify_settings WHERE guild_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setverifyrole(self, ctx, role: discord.Role):
        """Saves the role to the database permanently"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS verify_settings (guild_id INTEGER PRIMARY KEY, role_id INTEGER)")
            await db.execute("INSERT OR REPLACE INTO verify_settings (guild_id, role_id) VALUES (?, ?)", (ctx.guild.id, role.id))
            await db.commit()
        await ctx.send(f"✅ **Saved!** Verification role is now locked in as: {role.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setupverify(self, ctx):
        """Sends the panel using the saved database role"""
        role_id = await self.get_saved_role(ctx.guild.id)
        if not role_id:
            return await ctx.send("❌ **No role found!** Use `!setverifyrole @Role` first.")

        role = ctx.guild.get_role(role_id)
        
        embed = discord.Embed(
            title="🛡️ Security Checkpoint Required",
            description=(
                "To maintain a safe and bot-free environment, please complete this brief challenge.\n\n"
                "**Instructions:**\n"
                "1. Click the **Verify Me** button.\n"
                "2. Match the color name shown in the next message.\n"
                "3. Gain full access to the server."
            ),
            color=0x2f3136
        )
        
        view = discord.ui.View(timeout=None)
        start_btn = discord.ui.Button(label="Verify Me", style=discord.ButtonStyle.grey, custom_id="persistent_verify")
        
        async def start_callback(interaction):
            target = random.choice(['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange'])
            challenge_view = VerifyView(target, role)
            await interaction.response.send_message(f"**Challenge:** Click the **{target}** button!", view=challenge_view, ephemeral=True)

        start_btn.callback = start_callback
        view.add_item(start_btn)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Verification(bot))
