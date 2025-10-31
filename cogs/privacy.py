# cogs/privacy.py
import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime

BLURPLE = 0x5865F2
GOLD = 0xFFD700

start_time = time.time()

class Privacy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------- /privacy --------------
    @app_commands.command(name="privacy", description="View Elura Utility's privacy and data policy.")
    async def privacy(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔒 Privacy & Data Policy",
            description="Your privacy matters to us. Elura Utility is built to be transparent, secure, and respectful of your data.",
            color=BLURPLE,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="📘 What We Store",
            value="We only store **essential data** for features like counting, moderation, and economy.\nNo message content is permanently stored or shared.",
            inline=False
        )
        embed.add_field(
            name="🧠 Data Protection",
            value="All data is securely handled via **Supabase** with restricted access and encryption.",
            inline=False
        )
        embed.add_field(
            name="⚙️ User Control",
            value="Server admins may reset or remove data anytime using `/setup` or related commands.",
            inline=False
        )
        embed.add_field(
            name="📩 Contact",
            value="For privacy or removal requests, contact the developer: **r4e**",
            inline=False
        )
        embed.set_footer(text="Elura Utility • Trusted by communities worldwide")
        await interaction.response.send_message(embed=embed)

    # -------------- /botinfo --------------
    @app_commands.command(name="botinfo", description="Show details about Elura Utility.")
    async def botinfo(self, interaction: discord.Interaction):
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds)
        latency = round(self.bot.latency * 1000)
        uptime_seconds = int(time.time() - start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="🤖 Elura Utility – Bot Information",
            color=BLURPLE,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🌐 Servers", value=f"{guild_count}", inline=True)
        embed.add_field(name="👥 Users", value=f"{user_count}", inline=True)
        embed.add_field(name="📶 Ping", value=f"{latency}ms", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="👑 Developer", value="r4e", inline=True)
        embed.set_footer(text="Elura Utility • Premium Discord Bot Experience")
        await interaction.response.send_message(embed=embed)

    # -------------- /uptime --------------
    @app_commands.command(name="uptime", description="Check how long Elura Utility has been running.")
    async def uptime(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="🕒 Elura Uptime",
            description=f"Elura Utility has been online for:\n**{days}d {hours}h {minutes}m {seconds}s**",
            color=GOLD,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Always evolving")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Privacy(bot))