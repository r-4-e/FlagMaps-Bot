import discord
from discord.ext import commands
from discord import app_commands
from cogs.database import supabase  # ✅ Shared Supabase client only
from utils.embeds import elura_embed
import datetime
import random


class Punishments(commands.Cog):
    """Handles moderation commands with Supabase logging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ensure_tables()

    def ensure_tables(self):
        """Ensures the required tables exist in Supabase (auto-create if missing)."""
        for table_name in ("cases", "settings"):
            try:
                supabase.table(table_name).select("*").limit(1).execute()
            except Exception:
                print(f"⚠️ Warning: Could not verify '{table_name}' table in Supabase.")

    async def log_case(self, guild: discord.Guild, case_type: str, target, moderator, reason: str):
        """Logs moderation actions to Supabase and sends mod log."""
        case_id = random.randint(1000, 9999)
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Insert case record
        supabase.table("cases").insert({
            "guild_id": str(guild.id),
            "case_id": case_id,
            "case_type": case_type,
            "user_id": str(target.id),
            "moderator_id": str(moderator.id),
            "reason": reason,
            "timestamp": timestamp
        }).execute()

        # Fetch modlog channel
        result = supabase.table("settings").select("modlog_channel").eq("guild_id", str(guild.id)).execute()
        data = result.data

        if data and data[0].get("modlog_channel"):
            channel_id = int(data[0]["modlog_channel"])
            channel = guild.get_channel(channel_id)
            if channel:
                embed = elura_embed(
                    f"🧾 Case #{case_id} | {case_type}",
                    f"**User:** {target.mention}\n"
                    f"**Moderator:** {moderator.mention}\n"
                    f"**Reason:** {reason or 'No reason provided.'}"
                )
                embed.set_footer(text=f"Timestamp: {timestamp}")
                await channel.send(embed=embed)

        return case_id

    # ================== MODERATION COMMANDS ==================

    @app_commands.command(name="warn", description="Warn a user for breaking server rules.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        case_id = await self.log_case(interaction.guild, "Warning", member, interaction.user, reason)
        embed = elura_embed("⚠️ User Warned", f"{member.mention} has been warned.\nCase ID: **#{case_id}**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        case_id = await self.log_case(interaction.guild, "Kick", member, interaction.user, reason)
        embed = elura_embed("👢 User Kicked", f"{member.mention} has been kicked.\nCase ID: **#{case_id}**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        case_id = await self.log_case(interaction.guild, "Ban", member, interaction.user, reason)
        embed = elura_embed("🔨 User Banned", f"{member.mention} has been banned.\nCase ID: **#{case_id}**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timeout", description="Timeout a member for a specified duration (in minutes).")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        until = datetime.timedelta(minutes=minutes)
        await member.timeout(until, reason=reason)
        case_id = await self.log_case(interaction.guild, f"Timeout ({minutes}m)", member, interaction.user, reason)
        embed = elura_embed("⏱️ User Timed Out", f"{member.mention} was timed out for {minutes} minutes.\nCase ID: **#{case_id}**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="Unban a previously banned user.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        user = await self.bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        case_id = await self.log_case(interaction.guild, "Unban", user, interaction.user, reason)
        embed = elura_embed("✅ User Unbanned", f"{user.mention} has been unbanned.\nCase ID: **#{case_id}**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setmodlog", description="Set the moderation log channel.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setmodlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        supabase.table("settings").upsert({
            "guild_id": str(interaction.guild.id),
            "modlog_channel": str(channel.id)
        }).execute()

        embed = elura_embed("✅ Mod Log Set", f"Moderation cases will be logged in {channel.mention}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Punishments(bot))