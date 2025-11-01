# cogs/imagesync.py
"""
Elura Utility — ImageSync Cog
- Provides /copy, /paste, /listimages, /clearimages
- Auto-creates Supabase storage bucket 'elura-images' and table 'images' (best effort)
- Works without proxy; fully async-safe
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import io
import os
import asyncio
from datetime import datetime
from utils.supabase_client import supabase, SUPABASE_URL, SUPABASE_KEY

# ------------------- Configuration -------------------
BUCKET_NAME = "elura-images"
TABLE_NAME = "images"
MAX_COPY = 20
ADMIN_ROLE_ID = 1431189241685344348  # adjust if needed

# Colors
BLURPLE = discord.Color.blurple()
GOLD = discord.Color.gold()
ERROR = discord.Color.red()

# Table creation SQL
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id TEXT,
  server_id TEXT,
  channel_id TEXT,
  author TEXT,
  url TEXT,
  storage_path TEXT,
  filename TEXT,
  timestamp TEXT
);
"""

class ImageSync(commands.Cog):
    """📸 Image Synchronization system using Supabase."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        bot.loop.create_task(self._ensure_supabase_setup())

    def cog_unload(self):
        """Ensure aiohttp session closes properly."""
        self.bot.loop.create_task(self.session.close())

    # ------------------- Supabase Setup -------------------
    async def _ensure_supabase_setup(self):
        await asyncio.sleep(1)
        print("⚙️ Checking Supabase setup...")

        # 1. Ensure bucket exists
        try:
            buckets = supabase.storage.list_buckets()
            names = [b["name"] for b in buckets]
            if BUCKET_NAME not in names:
                supabase.storage.create_bucket(BUCKET_NAME, public=False)
                print(f"✅ Created storage bucket '{BUCKET_NAME}'.")
            else:
                print(f"✅ Bucket '{BUCKET_NAME}' already exists.")
        except Exception as e:
            print(f"⚠️ Could not verify/create bucket: {e}")

        # 2. Ensure table exists
        try:
            supabase.table(TABLE_NAME).select("*").limit(1).execute()
            print(f"✅ Supabase table '{TABLE_NAME}' is accessible.")
        except Exception as e:
            print(f"⚠️ Table check failed: {e}")
            await self._attempt_create_table_via_sql(CREATE_TABLE_SQL)

    async def _attempt_create_table_via_sql(self, sql: str):
        """Try creating table via Supabase SQL API (requires service role key)."""
        try:
            url = SUPABASE_URL.rstrip("/") + "/rest/v1/rpc"
            headers = {
                "Content-Type": "application/json",
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            payload = {"sql": sql}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as r:
                    text = await r.text()
                    print(f"[SQL API] status={r.status} text={text}")
        except Exception as e:
            print(f"[imagesync] SQL create failed: {e}")

    # ------------------- Utility Helpers -------------------
    async def _download_bytes(self, url: str) -> bytes:
        """Download bytes from a URL safely."""
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as e:
            print(f"[imagesync] Download failed for {url}: {e}")
        return b""

    def _storage_path(self, user_id: str, filename: str) -> str:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return f"{user_id}/{ts}_{filename.replace(' ', '_')}"

    def _is_admin(self, member: discord.Member) -> bool:
        return any(role.id == ADMIN_ROLE_ID for role in member.roles)

    # ------------------- Commands -------------------
    @app_commands.command(name="copy", description="Copy recent image attachments to your library.")
    async def copy(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        copied, errors = 0, 0
        examples = []

        async for msg in interaction.channel.history(limit=200):
            if copied >= MAX_COPY:
                break
            for att in msg.attachments:
                if att.content_type and att.content_type.startswith("image/"):
                    data = await self._download_bytes(att.url)
                    storage_path = self._storage_path(str(interaction.user.id), att.filename)
                    try:
                        supabase.storage.from_(BUCKET_NAME).upload(storage_path, data)
                        supabase.table(TABLE_NAME).insert({
                            "user_id": str(interaction.user.id),
                            "server_id": str(interaction.guild.id),
                            "channel_id": str(interaction.channel.id),
                            "author": str(msg.author),
                            "url": att.url,
                            "storage_path": storage_path,
                            "filename": att.filename,
                            "timestamp": msg.created_at.isoformat()
                        }).execute()
                        copied += 1
                        examples.append(att.filename)
                        if copied >= MAX_COPY:
                            break
                    except Exception as e:
                        print(f"[imagesync] Copy failed: {e}")
                        errors += 1

        embed = discord.Embed(
            title="📥 Copy Complete",
            description=f"Stored **{copied}** image(s) to your library.",
            color=BLURPLE
        )
        if examples:
            embed.add_field(name="Examples", value=", ".join(examples[:6]), inline=False)
        if errors:
            embed.add_field(name="Errors", value=f"{errors} image(s) failed.", inline=False)
        embed.set_footer(text="Elura • Image Sync")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="paste", description="Paste your saved images here.")
    async def paste(self, interaction: discord.Interaction, limit: int = 10):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        try:
            data = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).order("id", desc=True).limit(limit).execute()
        except Exception as e:
            print(f"[imagesync] Fetch failed: {e}")
            return await interaction.followup.send("⚠️ Could not fetch your images.", ephemeral=True)

        if not data.data:
            return await interaction.followup.send("📭 No images found.", ephemeral=True)

        sent = 0
        for rec in data.data:
            try:
                file_bytes = supabase.storage.from_(BUCKET_NAME).download(rec["storage_path"])
                if not isinstance(file_bytes, (bytes, bytearray)):
                    file_bytes = getattr(file_bytes, "content", b"")
                await interaction.channel.send(file=discord.File(io.BytesIO(file_bytes), filename=rec["filename"]))
                sent += 1
                await asyncio.sleep(0.6)
            except Exception as e:
                print(f"[imagesync] Paste failed: {e}")
                continue

        await interaction.followup.send(f"✅ Pasted {sent}/{len(data.data)} image(s).", ephemeral=True)

    @app_commands.command(name="listimages", description="List your stored images.")
    async def listimages(self, interaction: discord.Interaction, page: int = 1):
        per_page = 8
        offset = (page - 1) * per_page
        user_id = str(interaction.user.id)
        try:
            resp = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).order("id", desc=True).range(offset, offset + per_page - 1).execute()
        except Exception as e:
            print(f"[imagesync] List failed: {e}")
            return await interaction.response.send_message("⚠️ Error fetching images.", ephemeral=True)

        items = resp.data or []
        if not items:
            return await interaction.response.send_message("📭 No images on this page.", ephemeral=True)

        embed = discord.Embed(title=f"📚 Your Images — Page {page}", color=BLURPLE)
        for rec in items:
            embed.add_field(name=rec.get("filename", "image"), value=f"From {rec.get('author', 'unknown')} • {rec.get('timestamp', '')}", inline=False)
        embed.set_footer(text="Use /listimages page:<n> for more pages.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearimages", description="Clear all your saved images (admin only).")
    async def clearimages(self, interaction: discord.Interaction):
        user = interaction.user
        if not self._is_admin(user):
            return await interaction.response.send_message("🚫 You don't have permission.", ephemeral=True)

        try:
            supabase.table(TABLE_NAME).delete().eq("user_id", str(user.id)).execute()
            await interaction.response.send_message("🗑️ Your image library has been cleared.", ephemeral=True)
        except Exception as e:
            print(f"[imagesync] Clear failed: {e}")
            await interaction.response.send_message("⚠️ Failed to clear images.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ImageSync(bot))