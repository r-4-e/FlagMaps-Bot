# cogs/message_counter.py
import discord
from discord.ext import commands
from discord import app_commands
from supabase import create_client, Client
from datetime import datetime
import os

# ------------------- Supabase Connection -------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class MessageCounter(commands.Cog):
    """💬 Tracks user messages and provides leaderboards."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ensure_table()

    # ------------------- Auto-create table -------------------
    def ensure_table(self):
        try:
            supabase.table("message_counter").select("*").limit(1).execute()
        except Exception:
            print("⚙️ Creating 'message_counter' table...")
            try:
                ddl = """
                CREATE TABLE IF NOT EXISTS message_counter (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    count BIGINT DEFAULT 0,
                    last_updated TIMESTAMP,
                    UNIQUE (guild_id, user_id)
                );
                """
                supabase.postgrest.rpc("exec", {"sql": ddl}).execute()
                print("✅ message_counter table created successfully.")
            except Exception as e:
                print(f"⚠️ Failed to ensure table: {e}")

    # ------------------- Message Tracking -------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        try:
            existing = supabase.table("message_counter").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()

            if existing.data:
                count = existing.data[0]["count"] + 1
                supabase.table("message_counter").update({
                    "count": count,
                    "last_updated": datetime.utcnow().isoformat()
                }).eq("guild_id", guild_id).eq("user_id", user_id).execute()
            else:
                supabase.table("message_counter").insert({
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "count": 1,
                    "last_updated": datetime.utcnow().isoformat()
                }).execute()

        except Exception as e:
            print(f"[MessageCounter] ⚠️ Error updating count: {e}")

    # ------------------- /messages command -------------------
    @app_commands.command(name="messages", description="Check your total message count in this server.")
    async def messages(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        try:
            data = supabase.table("message_counter").select("*").eq("guild_id", guild_id).eq("user_id", user_id).execute()
            count = data.data[0]["count"] if data.data else 0
        except Exception as e:
            print(f"[MessageCounter] ⚠️ Fetch error: {e}")
            count = 0

        embed = discord.Embed(
            title="💬 Your Message Stats",
            description=f"You’ve sent **{count:,}** messages in **{interaction.guild.name}**!",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Elura • Message Counter System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------- /leaderboard command -------------------
    @app_commands.command(name="leaderboard", description="Show the top 10 most active members in this server.")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        try:
            data = supabase.table("message_counter").select("*").eq("guild_id", guild_id).order("count", desc=True).limit(10).execute()
        except Exception as e:
            print(f"[MessageCounter] ⚠️ Leaderboard fetch error: {e}")
            return await interaction.response.send_message("⚠️ Couldn’t fetch leaderboard.", ephemeral=True)

        if not data.data:
            return await interaction.response.send_message("📭 No message data yet!", ephemeral=True)

        embed = discord.Embed(
            title=f"🏆 Top Chatters – {interaction.guild.name}",
            color=discord.Color.gold()
        )

        desc = ""
        for i, user in enumerate(data.data, start=1):
            member = interaction.guild.get_member(int(user["user_id"]))
            name = member.display_name if member else f"User {user['user_id']}"
            desc += f"**#{i}** – {name}: **{user['count']:,} messages**\n"

        embed.description = desc
        embed.set_footer(text="Elura • Message Leaderboard System")
        await interaction.response.send_message(embed=embed)


# ------------------- Cog Setup -------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCounter(bot))