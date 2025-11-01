import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from cogs.database import supabase  # ✅ use the shared Supabase client only

ADMIN_ROLE_ID = 1431189241685344348  # Replace with your actual Admin Role ID


class Setup(commands.Cog):
    """🧩 Initializes Elura's database and settings for new servers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Initialize Elura Utility for this server.")
    async def setup_command(self, interaction: discord.Interaction):
        # ✅ Permission check
        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            return await interaction.response.send_message("⚠️ You don't have permission to run setup.", ephemeral=True)

        guild = interaction.guild
        await interaction.response.send_message("⚙️ Starting setup for Elura Utility...", ephemeral=True)

        # 🧭 Create progress embed
        embed = discord.Embed(
            title="🚀 Elura Setup In Progress",
            description="Connecting to Supabase...",
            color=discord.Color.blurple()
        )
        msg = await interaction.followup.send(embed=embed, wait=True)

        await asyncio.sleep(1.5)
        embed.description = "✅ Connected to Supabase.\n\nChecking required tables..."
        await msg.edit(embed=embed)

        # ✅ Required tables
        required_tables = ["economy", "counting", "warns", "settings"]
        missing_tables = []

        for table_name in required_tables:
            try:
                supabase.table(table_name).select("*").limit(1).execute()
            except Exception:
                missing_tables.append(table_name)

        await asyncio.sleep(1)
        if missing_tables:
            embed.description += "\n\n🆕 Missing tables detected: " + ", ".join(missing_tables)
        else:
            embed.description += "\n\n✅ All required tables exist."

        # ✅ Ensure guild is registered in settings
        try:
            existing = supabase.table("settings").select("guild_id").eq("guild_id", str(guild.id)).execute()
            if not existing.data:
                supabase.table("settings").insert({
                    "guild_id": str(guild.id),
                    "language": "en"
                }).execute()
                embed.description += f"\n\n🏠 Registered guild: `{guild.name}`"
            else:
                embed.description += f"\n\n🔁 Guild `{guild.name}` already registered."
        except Exception as e:
            embed.description += f"\n\n❌ Database error while registering guild:\n`{e}`"

        # ✅ Final visual polish
        embed.color = discord.Color.green()
        embed.title = "✅ Elura Setup Complete!"
        embed.add_field(name="Server", value=guild.name, inline=False)
        embed.add_field(name="Status", value="All systems operational.", inline=False)
        embed.set_footer(text="Elura Utility • Powered by Supabase • Made by r4e")

        await asyncio.sleep(1)
        await msg.edit(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Setup(bot))