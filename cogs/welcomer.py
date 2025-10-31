import discord
from discord.ext import commands
from discord import app_commands
from database.connector import db
from utils.embeds import elura_embed

class Welcomer(commands.Cog):
    """Welcomes new members and announces when someone leaves."""
    def __init__(self, bot):
        self.bot = bot
        self.create_tables()

    def create_tables(self):
        """Creates welcomer table if it doesn’t exist."""
        cur = db.local.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS welcomer (
            guild_id INTEGER PRIMARY KEY,
            welcome_channel INTEGER,
            welcome_message TEXT,
            leave_message TEXT
        )
        """)
        db.local.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cur = db.local.cursor()
        cur.execute("SELECT welcome_channel, welcome_message FROM welcomer WHERE guild_id=?", (member.guild.id,))
        row = cur.fetchone()
        if not row or not row["welcome_channel"]:
            return
        channel = member.guild.get_channel(row["welcome_channel"])
        if channel:
            message = row["welcome_message"] or f"Welcome {member.mention} to **{member.guild.name}**!"
            embed = elura_embed("🎉 Welcome!", message)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{len(member.guild.members)}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        cur = db.local.cursor()
        cur.execute("SELECT welcome_channel, leave_message FROM welcomer WHERE guild_id=?", (member.guild.id,))
        row = cur.fetchone()
        if not row or not row["welcome_channel"]:
            return
        channel = member.guild.get_channel(row["welcome_channel"])
        if channel:
            message = row["leave_message"] or f"{member.name} has left the server. 😢"
            embed = elura_embed("👋 Goodbye!", message, color=discord.Color.dark_gray())
            await channel.send(embed=embed)

    # --- Configuration Commands ---
    @app_commands.command(name="setwelcome", description="Set a channel and message for welcoming new members.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        cur = db.local.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO welcomer (guild_id, welcome_channel, welcome_message) VALUES (?, ?, ?)",
            (interaction.guild.id, channel.id, message)
        )
        db.local.commit()
        embed = elura_embed("✅ Welcome Setup Complete", f"New members will be welcomed in {channel.mention}.\n\n**Message:** {message}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setleave", description="Set a message for when members leave.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setleave(self, interaction: discord.Interaction, message: str):
        cur = db.local.cursor()
        cur.execute(
            "UPDATE welcomer SET leave_message=? WHERE guild_id=?",
            (message, interaction.guild.id)
        )
        db.local.commit()
        embed = elura_embed("✅ Leave Message Set", f"Leave message has been updated:\n\n**{message}**")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcomer(bot))