import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os
from supabase import create_client, Client
from cogs.database import supabase  # ✅ This uses the existing shared client

# ------------------- Role Restriction -------------------
RESTRICTED_ROLE_ID = 1431189237687914550  # Counting Manager Role ID

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_count_data(self, guild_id: int):
        """Fetch or create count data for a guild."""
        response = supabase.table("counting").select("*").eq("guild_id", str(guild_id)).execute()
        if response.data:
            return response.data[0]

        # Auto-create if missing
        supabase.table("counting").insert({
            "guild_id": str(guild_id),
            "channel_id": None,
            "count": 0,
            "last_user": None,
            "leaderboard": {}
        }).execute()
        return {"guild_id": str(guild_id), "channel_id": None, "count": 0, "last_user": None, "leaderboard": {}}

    async def update_count_data(self, guild_id: int, data: dict):
        """Update counting table in Supabase."""
        supabase.table("counting").update(data).eq("guild_id", str(guild_id)).execute()

    # ------------------- Slash Commands -------------------
    @app_commands.command(name="setcountingchannel", description="Set or update this server’s counting channel.")
    async def set_counting_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        member = interaction.user
        if not any(role.id == RESTRICTED_ROLE_ID for role in member.roles):
            return await interaction.response.send_message("🚫 You don’t have permission to run this command.", ephemeral=True)

        guild_id = str(interaction.guild.id)
        await self.update_count_data(guild_id, {"channel_id": str(channel.id)})

        embed = discord.Embed(
            title="🔢 Counting Channel Set",
            description=f"Counting channel has been set to {channel.mention}.",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Counting System")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetcount", description="Reset the server’s counting progress.")
    async def reset_count(self, interaction: discord.Interaction):
        member = interaction.user
        if not any(role.id == RESTRICTED_ROLE_ID for role in member.roles):
            return await interaction.response.send_message("🚫 You don’t have permission to run this command.", ephemeral=True)

        guild_id = str(interaction.guild.id)
        await self.update_count_data(guild_id, {"count": 0, "last_user": None})

        embed = discord.Embed(
            title="♻️ Count Reset",
            description="The counting sequence has been reset to **0**.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Counting System")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the counting leaderboard for this server.")
    async def leaderboard(self, interaction: discord.Interaction):
        data = await self.get_count_data(interaction.guild.id)
        leaderboard = data.get("leaderboard", {}) or {}

        if not leaderboard:
            return await interaction.response.send_message("📊 No leaderboard data yet. Start counting first!", ephemeral=True)

        sorted_board = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
        embed = discord.Embed(
            title="🏆 Counting Leaderboard",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        desc = ""
        for i, (user_id, score) in enumerate(sorted_board[:10], start=1):
            user = interaction.guild.get_member(int(user_id))
            username = user.name if user else f"User {user_id}"
            desc += f"**#{i}** {username} — `{score}` counts\n"
        embed.description = desc
        embed.set_footer(text="Elura Utility • Counting System")
        await interaction.response.send_message(embed=embed)

    # ------------------- Listener -------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        data = await self.get_count_data(message.guild.id)

        channel_id = data.get("channel_id")
        if not channel_id or int(channel_id) != message.channel.id:
            return

        current_count = data.get("count", 0)
        last_user = data.get("last_user")

        try:
            number = int(message.content.strip())
        except ValueError:
            return

        if str(message.author.id) == str(last_user):
            await message.add_reaction("❌")
            await message.channel.send(f"{message.author.mention} ruined it! Next number is **1**.")
            await self.update_count_data(guild_id, {"count": 0, "last_user": None})
            return

        if number == current_count + 1:
            await message.add_reaction("✅")
            new_leaderboard = data.get("leaderboard", {}) or {}
            new_leaderboard[str(message.author.id)] = new_leaderboard.get(str(message.author.id), 0) + 1
            await self.update_count_data(guild_id, {
                "count": number,
                "last_user": str(message.author.id),
                "leaderboard": new_leaderboard
            })
        else:
            await message.add_reaction("❌")
            await message.channel.send(f"{message.author.mention} ruined it! Next number is **1**.")
            await self.update_count_data(guild_id, {"count": 0, "last_user": None})

async def setup(bot):
    await bot.add_cog(Counting(bot))