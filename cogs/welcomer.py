import discord
from discord.ext import commands
from discord import app_commands
from database.connector import db
from utils.embeds import elura_embed

class Welcomer(commands.Cog):
    """Manages welcome and leave messages for each guild."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        try:
            cur = db.local.cursor()
            cur.execute("SELECT welcome_channel FROM settings WHERE guild_id=?", (member.guild.id,))
            row = cur.fetchone()
            if not row or not row["welcome_channel"]:
                return
            channel = member.guild.get_channel(row["welcome_channel"])
            if channel:
                embed = elura_embed(
                    "🎉 Welcome!",
                    f"Hey {member.mention}, welcome to **{member.guild.name}**!\nWe’re glad you joined us 💫"
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)
        except Exception as e:
            print(f"[Welcomer] Error: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        try:
            cur = db.local.cursor()
            cur.execute("SELECT welcome_channel FROM settings WHERE guild_id=?", (member.guild.id,))
            row = cur.fetchone()
            if not row or not row["welcome_channel"]:
                return
            channel = member.guild.get_channel(row["welcome_channel"])
            if channel:
                embed = elura_embed(
                    "👋 Farewell",
                    f"**{member.display_name}** has left **{member.guild.name}**. We hope to see you again someday 💭"
                )
                await channel.send(embed=embed)
        except Exception as e:
            print(f"[Welcomer] Error: {e}")

    @app_commands.command(name="setwelcome", description="Set the channel for welcome and leave messages.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cur = db.local.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO settings (guild_id, welcome_channel) VALUES (?, ?)",
            (interaction.guild.id, channel.id)
        )
        db.local.commit()
        embed = elura_embed("✅ Welcome Channel Set", f"Messages will now appear in {channel.mention}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcomer(bot))