import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import elura_embed
from cogs.database import supabase  # shared Supabase client

class Economy(commands.Cog):
    """Economy system — earn and manage virtual credits."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ensure_table()

    def ensure_table(self):
        """Auto-create the economy table if it doesn't exist."""
        try:
            supabase.query("SELECT 1 FROM economy LIMIT 1").execute()
        except Exception:
            # Create the table automatically
            supabase.table("economy").insert([]).execute()  # ensure connection works
            ddl = """
            CREATE TABLE IF NOT EXISTS economy (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                balance BIGINT DEFAULT 0,
                UNIQUE (guild_id, user_id)
            );
            """
            supabase.postgrest.rpc("exec", {"sql": ddl}).execute()
            print("✅ Economy table auto-created in Supabase")

    async def fetch_balance(self, guild_id: int, user_id: int) -> int:
        """Fetch or initialize a user's balance."""
        result = supabase.table("economy").select("*").eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
        data = result.data
        if not data:
            supabase.table("economy").insert({
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "balance": 0
            }).execute()
            return 0
        return data[0]["balance"]

    async def update_balance(self, guild_id: int, user_id: int, new_balance: int):
        """Update or insert balance safely."""
        result = supabase.table("economy").select("*").eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
        if result.data:
            supabase.table("economy").update({"balance": new_balance}).eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
        else:
            supabase.table("economy").insert({
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "balance": new_balance
            }).execute()

    @app_commands.command(name="balance", description="Check your current balance.")
    async def balance(self, interaction: discord.Interaction):
        balance = await self.fetch_balance(interaction.guild.id, interaction.user.id)
        embed = elura_embed("💰 Balance", f"**{interaction.user.display_name}**, you currently have **{balance:,} credits.**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="work", description="Work to earn credits (1h cooldown).")
    @app_commands.checks.cooldown(1, 3600.0, key=lambda i: i.user.id)
    async def work(self, interaction: discord.Interaction):
        balance = await self.fetch_balance(interaction.guild.id, interaction.user.id)
        earned = 150
        new_balance = balance + earned
        await self.update_balance(interaction.guild.id, interaction.user.id, new_balance)
        embed = elura_embed("🧰 Work Complete", f"You worked hard and earned **{earned} credits!**\nNew balance: **{new_balance:,}**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="Show the richest members in this server.")
    async def leaderboard(self, interaction: discord.Interaction):
        result = supabase.table("economy").select("*").eq("guild_id", str(interaction.guild.id)).order("balance", desc=True).limit(10).execute()
        data = result.data

        if not data:
            return await interaction.response.send_message("No economy data found yet.", ephemeral=True)

        desc = "\n".join(
            [f"**{i+1}.** <@{r['user_id']}> — **{r['balance']:,} credits**" for i, r in enumerate(data)]
        )
        embed = elura_embed("🏆 Server Leaderboard", desc)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))