# cogs/counting.py
import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client, Client
import os
from datetime import datetime

# ---------------- SUPABASE SETUP ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- COLORS ----------------
BLURPLE = 0x5865F2
GOLD = 0xFFD700
RED = 0xED4245
GREEN = 0x57F287


class Counting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- HELPERS ----------------
    async def reset_count(self, guild_id: str):
        """Reset the counting state for a guild."""
        supabase.table("counting").update(
            {"current_number": 0, "last_user": None}
        ).eq("guild_id", guild_id).execute()

    async def add_score(self, guild_id: str, user_id: int):
        """Increment the leaderboard score for a user."""
        # Fetch current score
        data = supabase.table("leaderboard").select("*").eq("guild_id", guild_id).eq("user_id", str(user_id)).execute()
        if data.data:
            current = data.data[0]["count"]
            supabase.table("leaderboard").update({"count": current + 1}).eq("guild_id", guild_id).eq("user_id", str(user_id)).execute()
        else:
            supabase.table("leaderboard").insert({
                "guild_id": guild_id,
                "user_id": str(user_id),
                "count": 1
            }).execute()

    # ---------------- COMMANDS ----------------
    @app_commands.command(name="setcountingchannel", description="Set this channel as the counting channel.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setcountingchannel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        channel_id = str(interaction.channel.id)

        supabase.table("counting").upsert({
            "guild_id": guild_id,
            "channel_id": channel_id,
            "current_number": 0,
            "last_user": None
        }).execute()

        embed = discord.Embed(
            title="📊 Counting Channel Set!",
            description=f"This channel is now the counting hub for **{interaction.guild.name}**.",
            color=BLURPLE,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Powered by r4e")
        await interaction.response.send_message(embed=embed)

    # ---------------- MESSAGE HANDLER ----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        data = supabase.table("counting").select("*").eq("guild_id", guild_id).execute()
        if not data.data:
            return  # counting not set up for this guild

        record = data.data[0]
        if message.channel.id != int(record["channel_id"]):
            return  # message not in counting channel

        content = message.content.strip()
        if not content.isdigit():
            return  # ignore non-numeric messages

        num = int(content)
        expected = record["current_number"] + 1
        last_user = record["last_user"]

        # --- Rule: same user cannot count twice ---
        if last_user and message.author.id == last_user:
            await message.add_reaction("❌")
            await message.channel.send(
                f"❌ {message.author.mention} RUINED IT!! Next number is **1**.",
                delete_after=6
            )
            await self.reset_count(guild_id)
            return

        # --- Correct number ---
        if num == expected:
            await message.add_reaction("✅")
            supabase.table("counting").update({
                "current_number": num,
                "last_user": message.author.id
            }).eq("guild_id", guild_id).execute()

            await self.add_score(guild_id, message.author.id)

            # --- Milestone Check ---
            if num in [100, 500, 1000, 5000, 10000]:
                embed = discord.Embed(
                    title="🏆 Milestone Reached!",
                    description=f"**{message.author.mention}** helped reach **{num}**!",
                    color=GOLD,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text="Elura Utility • r4e")
                await message.channel.send(embed=embed)

        # --- Wrong number ---
        else:
            await message.add_reaction("❌")
            await message.channel.send(
                f"{message.author.mention} RUINED IT!! Next number is **1**.",
                delete_after=6
            )
            await self.reset_count(guild_id)

    # ---------------- LEADERBOARD ----------------
    @app_commands.command(name="countingleaderboard", description="View the top counters in this server.")
    async def countingleaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        result = supabase.table("leaderboard").select("*").eq("guild_id", guild_id).execute()
        data = result.data

        if not data:
            await interaction.response.send_message("📊 No leaderboard data yet. Start counting!", ephemeral=True)
            return

        sorted_data = sorted(data, key=lambda x: x["count"], reverse=True)
        embed = discord.Embed(
            title=f"🏆 Counting Leaderboard – {interaction.guild.name}",
            color=BLURPLE,
            timestamp=datetime.utcnow()
        )

        medals = ["🥇", "🥈", "🥉"]
        for i, entry in enumerate(sorted_data[:10]):
            user = interaction.guild.get_member(int(entry["user_id"]))
            medal = medals[i] if i < 3 else "🔹"
            name = user.display_name if user else f"User {entry['user_id']}"
            embed.add_field(name=f"{medal} {name}", value=f"**{entry['count']}** correct counts", inline=False)

        embed.set_footer(text="Elura Utility • Powered by r4e")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Counting(bot))