import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
import aiohttp
import os

# ✅ Supabase connection
from supabase import create_client, Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class Welcomer(commands.Cog):
    """🎉 Sends a welcome image and logs joins to Supabase."""

    def __init__(self, bot):
        self.bot = bot
        self.ensure_table()

    def ensure_table(self):
        """Auto-create the 'joins' table if missing."""
        try:
            supabase.table("joins").select("*").limit(1).execute()
        except Exception:
            ddl = """
            CREATE TABLE IF NOT EXISTS joins (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                joined_at TEXT NOT NULL
            );
            """
            supabase.postgrest.rpc("exec", {"sql": ddl}).execute()
            print("✅ 'joins' table auto-created in Supabase")

    async def generate_welcome_image(self, member: discord.Member):
        """Creates a simple welcome banner with the member's avatar."""
        base = Image.new("RGBA", (800, 250), (40, 44, 52, 255))
        draw = ImageDraw.Draw(base)

        # Fetch avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(member.display_avatar.url) as resp:
                avatar_bytes = await resp.read()

        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((180, 180))
        base.paste(avatar, (40, 35), avatar)

        # Text setup
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_big = ImageFont.truetype(font_path, 50)
        font_small = ImageFont.truetype(font_path, 30)

        draw.text((250, 80), f"Welcome, {member.name}!", fill=(255, 255, 255), font=font_big)
        draw.text((250, 150), f"You’re member #{len(member.guild.members)}!", fill=(180, 180, 180), font=font_small)

        # Convert to Discord file
        buffer = BytesIO()
        base.save(buffer, "PNG")
        buffer.seek(0)
        return discord.File(buffer, filename="welcome.png")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Triggered when a new member joins the server."""
        # Store join event in Supabase
        try:
            supabase.table("joins").insert({
                "guild_id": str(member.guild.id),
                "user_id": str(member.id),
                "username": str(member),
                "joined_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"[Welcomer] Error logging join: {e}")

        # Fetch welcome channel from settings table
        try:
            result = supabase.table("settings").select("welcome_channel").eq("guild_id", str(member.guild.id)).execute()
            if result.data and result.data[0].get("welcome_channel"):
                channel = member.guild.get_channel(int(result.data[0]["welcome_channel"]))
                if channel:
                    image_file = await self.generate_welcome_image(member)
                    embed = discord.Embed(
                        title=f"🎉 Welcome {member.name}!",
                        description=f"We’re glad you’re here, {member.mention}!",
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"Joined at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    await channel.send(embed=embed, file=image_file)
        except Exception as e:
            print(f"[Welcomer] Error sending welcome message: {e}")

    @app_commands.command(name="setwelcome", description="Set the welcome channel for this server.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        supabase.table("settings").upsert({
            "guild_id": str(interaction.guild.id),
            "welcome_channel": str(channel.id)
        }).execute()
        await interaction.response.send_message(f"✅ Welcome messages will now be sent in {channel.mention}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcomer(bot))