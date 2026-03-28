import discord
from discord.ext import commands
from main.config import COLOR_BRAND
from main.utils.embeds import success, brand, error

class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, style: discord.ButtonStyle):
        super().__init__(
            label=role.name, 
            style=style, 
            custom_id=f"role_{role.id}"
        )
        self.role_id = role.id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message("❌ Role not found.", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"✅ Removed **{role.name}**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Added **{role.name}**", ephemeral=True)

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rolemenu")
    @commands.has_permissions(administrator=True)
    async def create_custom_menu(self, ctx, title: str, color_hex: str, *, roles_input: str):
        """
        Creates a custom role menu.
        Usage: !rolemenu "Color Roles" #FF0000 @Red, @Blue, @Green
        """
        try:
            # Convert hex to discord color
            color_int = int(color_hex.replace("#", ""), 16)
            
            # Clean up role mentions/IDs into actual role objects
            role_mentions = roles_input.replace(",", "").split()
            valid_roles = []
            
            for mention in role_mentions:
                role = await commands.RoleConverter().convert(ctx, mention)
                valid_roles.append(role)

            if not valid_roles:
                return await ctx.send(embed=error("No valid roles found. Mention them like @Role1 @Role2"))

            embed = discord.Embed(
                title=f"🎭 {title}",
                description="Click the buttons below to toggle your roles!",
                color=color_int
            )

            view = discord.ui.View(timeout=None)
            for role in valid_roles:
                # You can change ButtonStyle.primary to secondary or success if you prefer
                view.add_item(RoleButton(role, discord.ButtonStyle.primary))

            await ctx.send(embed=embed, view=view)
            await ctx.message.delete()

        except Exception as e:
            await ctx.send(embed=error(f"Error: {e}\nFormat: `!rolemenu \"Title\" #Hex @Role @Role`"))

async def setup(bot):
    await bot.add_cog(Roles(bot))
