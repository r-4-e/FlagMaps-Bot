import discord
from discord import app_commands
from discord.ext import commands
from database.connector import db
from utils.embeds import elura_embed

class Economy(commands.Cog):
    """Economy system — earn and manage virtual credits."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your current balance.")
    async def balance(self, interaction: discord.Interaction):
        data = await db.fetch_economy(interaction.guild.id, interaction.user.id)
        balance = data["balance"] if data else 0
        embed = elura_embed("💰 Balance", f"**{interaction.user.display_name}**, you currently have **{balance:,} credits.**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="work", description="Work to earn credits (cooldown 1h).")
    @app_commands.checks.cooldown(1, 3600.0, key=lambda i: i.user.id)
    async def work(self, interaction: discord.Interaction):
        data = await db.fetch_economy(interaction.guild.id, interaction.user.id)
        current = data["balance"] if data else 0
        earned = 150
        new_balance = current + earned
        await db.update_economy(interaction.guild.id, interaction.user.id, new_balance)
        embed = elura_embed("🧰 Work Complete", f"You worked hard and earned **{earned} credits!**\nNew balance: **{new_balance:,}**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="Show the richest members in this server.")
    async def leaderboard(self, interaction: discord.Interaction):
        if db.supabase:
            data = db.supabase.table("economy").select("*").eq("guild_id", interaction.guild.id).execute().data
        else:
            cur = db.local.cursor()
            cur.execute("SELECT * FROM economy WHERE guild_id=? ORDER BY balance DESC LIMIT 10", (interaction.guild.id,))
            data = cur.fetchall()

        if not data:
            await interaction.response.send_message("No economy data found yet.", ephemeral=True)
            return

        desc = "\n".join(
            [f"**{i+1}.** <@{r['user_id']}> — **{r['balance']:,} credits**" for i, r in enumerate(data)]
        )
        embed = elura_embed("🏆 Server Leaderboard", desc)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))