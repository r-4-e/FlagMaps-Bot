# cogs/help.py
import discord
from discord import app_commands
from discord.ext import commands

RESTRICTED_ROLE_ID = 1431189241685344348  # restricted role id

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all Elura Utility commands with categories.")
    async def help(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        is_dev = False

        if guild:
            member = guild.get_member(user.id)
            if member:
                is_dev = any(role.id == RESTRICTED_ROLE_ID for role in member.roles)

        embed = discord.Embed(
            title="💠 Elura Utility – Command Directory",
            description="Your ultimate all-in-one utility system.\n\n**Select a category below to explore.**",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Elura Utility • Made by r4e")

        # --- Main categories ---
        embed.add_field(
            name="🪙 Economy",
            value="`/balance`, `/work`, `/daily`, `/shop`, `/inventory`",
            inline=False
        )
        embed.add_field(
            name="🎉 Fun",
            value="`/meme`, `/ryder`, `/8ball`, `/joke`",
            inline=False
        )
        embed.add_field(
            name="🌐 Translate",
            value="`/translate`, `/language`, `/autotranslate`",
            inline=False
        )
        embed.add_field(
            name="👋 Welcomer",
            value="`/setwelcome`, `/testwelcome`, `/clearwelcome`",
            inline=False
        )
        embed.add_field(
            name="🛡️ Punishments",
            value="`/warn`, `/mute`, `/kick`, `/ban`, `/unban`",
            inline=False
        )
        embed.add_field(
            name="💬 Counting",
            value="`/setcountingchannel`, `/leaderboard`, `/resetcount`",
            inline=False
        )
        embed.add_field(
            name="⚙️ Setup",
            value="`/setup`, `/config`, `/prefix`",
            inline=False
        )
        embed.add_field(
            name="🔐 Privacy",
            value="`/privacy`, `/policy`, `/data`",
            inline=False
        )

        # --- Restricted commands only visible to role ---
        if is_dev:
            restricted = discord.Embed(
                title="🔒 Restricted & Developer Commands",
                description="Exclusive utilities for internal management and diagnostics.",
                color=discord.Color.red()
            )
            restricted.add_field(name="🧩 /adminreport", value="Check system logs & status.", inline=False)
            restricted.add_field(name="⚙️ /reset", value="Reset bot databases or configurations.", inline=False)
            restricted.add_field(name="🧠 /eval", value="Developer debugging tool (use with caution).", inline=False)
            restricted.set_footer(text="Restricted Access • Authorized Role Only")

            await interaction.response.send_message(embeds=[embed, restricted], ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Help(bot))