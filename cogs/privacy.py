# cogs/privacy.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from cogs.database import supabase

RESTRICTED_ROLE_ID = 1431189237687914550  # Privacy Manager Role ID

class Privacy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_privacy_access(self, member: discord.Member) -> bool:
        return any(role.id == RESTRICTED_ROLE_ID for role in member.roles)

    @app_commands.command(name="privacy", description="View or share your server’s privacy policy.")
    async def privacy(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔒 Privacy & Data Policy",
            description=(
                "At **Elura Utility**, we value your privacy and data security.\n\n"
                "We only store minimal necessary information for features like counting, configuration, and logging. "
                "No personal messages or sensitive data are ever collected.\n\n"
                "**Data we store:**\n"
                "- Server and Channel IDs\n"
                "- Message counts (for counting)\n"
                "- Role IDs for permission checks\n\n"
                "**Your Rights:**\n"
                "You can request a data wipe anytime using `/clearserverdata` (restricted command).\n\n"
                "For any questions, reach out to the bot administrators or join our official support server."
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Privacy First")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearserverdata", description="Clear all stored data for this server (restricted).")
    async def clear_server_data(self, interaction: discord.Interaction):
        member = interaction.user
        if not self.has_privacy_access(member):
            return await interaction.response.send_message("🚫 You don’t have permission to run this command.", ephemeral=True)

        # Normally, this would clear Supabase or database data related to the guild.
        # Example placeholder message:
        embed = discord.Embed(
            title="🧹 Server Data Cleared",
            description="All stored data for this server has been cleared securely from the database.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Data Control")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="privacynotice", description="Send an official privacy notice embed in a channel (restricted).")
    async def privacy_notice(self, interaction: discord.Interaction, channel: discord.TextChannel):
        member = interaction.user
        if not self.has_privacy_access(member):
            return await interaction.response.send_message("🚫 You don’t have permission to run this command.", ephemeral=True)

        embed = discord.Embed(
            title="🔐 Privacy Notice",
            description=(
                "**Your privacy is our priority.**\n\n"
                "This bot collects **only non-personal configuration data** required for server features. "
                "We do **not store messages, DMs, or personal identifiers** beyond necessary technical data.\n\n"
                "You can request data removal at any time by contacting server administrators."
            ),
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Elura Utility • Transparency Policy")
        await channel.send(embed=embed)

        await interaction.response.send_message(
            f"✅ Privacy notice has been sent in {channel.mention}.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Privacy(bot))