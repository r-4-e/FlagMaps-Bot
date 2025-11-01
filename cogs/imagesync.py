# cogs/imagesync.py
"""
Elura Utility — ImageSync Cog
- Provides /copy, /paste, /listimages, /clearimages
- Best-effort auto-creates Supabase storage bucket 'elura-images' and table 'images'
- Stores image files in Supabase Storage when possible; falls back to original URL
- Requires utils/supabase_client.supabase (created earlier)
- NOTE: Some auto-create operations (DDL via the SQL API or bucket creation)
  may require a Supabase Service Role key. If your anon key lacks permissions
  the cog will still run, but will ask you to create the table/bucket manually.
"""
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import io
import os
import asyncio
import json
from datetime import datetime
from utils.supabase_client import supabase, SUPABASE_URL, SUPABASE_KEY  # you exported these in that module

# Configuration
BUCKET_NAME = "elura-images"
TABLE_NAME = "images"
MAX_COPY = 20
ADMIN_ROLE_ID = 1431189241685344348  # role allowed to clear; change as needed

# Color palette
BLURPLE = discord.Color.blurple()
GOLD = discord.Color.gold()
ERROR = discord.Color.red()

# SQL used to attempt table creation (Postgres)
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
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Try to ensure storage bucket and table exist (best-effort, non-blocking)
        bot.loop.create_task(self._ensure_supabase_setup())

    # ---------------------- Supabase helpers ----------------------
    async def _ensure_supabase_setup(self):
        """Best-effort: ensure storage bucket and table exist. Non-blocking."""
        await asyncio.sleep(1)  # slight delay to let other inits finish
        # 1) Ensure storage bucket
        try:
            # supabase.storage.create_bucket may require service role key; attempt it
            try:
                supabase.storage().create_bucket(BUCKET_NAME, public=False)
                print(f"✅ Created storage bucket '{BUCKET_NAME}' (or already exists).")
            except Exception:
                # Some clients expose .from_() only; try to list buckets to check existence
                try:
                    buckets = supabase.storage().list_buckets()
                    names = [b['name'] for b in buckets]
                    if BUCKET_NAME not in names:
                        print(f"⚠️ Could not create bucket '{BUCKET_NAME}'. You may need service-role key.")
                    else:
                        print(f"✅ Bucket '{BUCKET_NAME}' exists.")
                except Exception:
                    print("⚠️ Could not verify/create storage bucket. Continuing — storage might be unavailable.")
        except Exception as e:
            print(f"⚠️ Storage setup check failed: {e}")

        # 2) Ensure table exists (best-effort)
        try:
            resp = supabase.table(TABLE_NAME).select("*").limit(1).execute()
            # if no exception, table exists (or returns empty)
            print(f"✅ Supabase table '{TABLE_NAME}' is accessible.")
        except Exception as e:
            # Attempt to run SQL via the SQL API if we have a key that permits it
            print(f"⚠️ Table '{TABLE_NAME}' not accessible or doesn't exist: {e}")
            created = await self._attempt_create_table_via_sql(CREATE_TABLE_SQL)
            if created:
                print(f"✅ Created table '{TABLE_NAME}' via SQL API.")
            else:
                print(f"❌ Could not auto-create table '{TABLE_NAME}'. Please create it manually with the SQL below:\n{CREATE_TABLE_SQL}")

    async def _attempt_create_table_via_sql(self, sql: str) -> bool:
        """
        Attempt to run SQL via the Supabase SQL endpoint.
        This typically requires the SERVICE_ROLE key; anon keys are often blocked.
        Returns True on success, False otherwise.
        """
        try:
            # SQL API endpoint
            # This endpoint is usually: https://<project>.supabase.co/rest/v1/rpc
            # Supabase provides a SQL API at /rest/v1/rpc/run_sql for some setups, but
            # it can vary. We'll try the SQL function endpoint: /rpc
            url = SUPABASE_URL.rstrip("/") + "/rest/v1/rpc"
            headers = {
                "Content-Type": "application/json",
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            # Many projects will not accept arbitrary SQL via anon key; call will likely fail.
            # We'll attempt to call "sql" RPC with a payload if your project exposes such a function.
            payload = {"sql": sql}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=15) as r:
                    text = await r.text()
                    if r.status in (200, 201, 204):
                        return True
                    else:
                        print(f"[Supabase SQL API] status={r.status} text={text}")
                        return False
        except Exception as e:
            print(f"[Supabase SQL API] exception: {e}")
            return False

    # ---------------------- Utility helpers ----------------------
    async def _download_bytes(self, url: str) -> bytes:
        """Download a URL and return bytes."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception as e:
            print(f"[imagesync] Failed to download {url}: {e}")
        return b""

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat()

    # ---------------------- Image storage ----------------------
    def _storage_path_for(self, user_id: str, filename: str) -> str:
        # create a predictable storage path
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_name = filename.replace(" ", "_")
        return f"{user_id}/{ts}_{safe_name}"

    def _is_admin(self, member: discord.Member) -> bool:
        return any(role.id == ADMIN_ROLE_ID for role in member.roles)

    # ---------------------- Commands ----------------------
    @app_commands.command(name="copy", description="Copy up to 20 image attachments from this channel to your global library.")
    async def copy(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        author = interaction.user
        copied = 0
        examples = []
        errors = 0

        async for msg in channel.history(limit=200):
            if copied >= MAX_COPY:
                break
            for att in msg.attachments:
                if att.content_type and att.content_type.startswith("image/"):
                    # Download bytes
                    data = await self._download_bytes(att.url)
                    storage_path = None
                    try:
                        # Try upload to Supabase Storage
                        try:
                            # supabase.storage().from_(bucket).upload(path, bytes)
                            bucket = supabase.storage().from_(BUCKET_NAME)
                            path = self._storage_path_for(str(author.id), att.filename)
                            # upload expects file-like or bytes depending on client; try bytes
                            bucket.upload(path, data)  # may raise if not allowed
                            storage_path = path
                        except Exception as e:
                            # storage may be unavailable or permission denied; fallback to storing original URL
                            print(f"[imagesync] Supabase storage upload failed: {e}")
                            storage_path = None

                        # Insert metadata into images table
                        record = {
                            "user_id": str(author.id),
                            "server_id": str(channel.guild.id) if channel.guild else None,
                            "channel_id": str(channel.id),
                            "author": str(msg.author),
                            "url": att.url,
                            "storage_path": storage_path,
                            "filename": att.filename,
                            "timestamp": str(msg.created_at.isoformat())
                        }
                        supabase.table(TABLE_NAME).insert(record).execute()
                        copied += 1
                        examples.append(att.filename)
                        if copied >= MAX_COPY:
                            break
                    except Exception as e:
                        print(f"[imagesync] Failed to store image metadata: {e}")
                        errors += 1
                        continue

        # Reply with summary
        embed = discord.Embed(
            title="📥 Copy Complete",
            description=f"Stored **{copied}** image(s) to your global library.",
            color=BLURPLE,
            timestamp=datetime.utcnow()
        )
        if examples:
            embed.add_field(name="Examples", value=", ".join(examples[:6]), inline=False)
        if errors:
            embed.add_field(name="Errors", value=f"{errors} items failed to store.", inline=False)
        embed.set_footer(text="Elura • Images Sync")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="paste", description="Paste images from your global library into this channel.")
    @app_commands.describe(limit="Maximum images to paste (default: all)")
    async def paste(self, interaction: discord.Interaction, limit: int = 20):
        # permission: allow only channel send perms
        if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
            return await interaction.response.send_message("I can't post in this channel.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        # fetch images owned by this user (most recent first)
        try:
            resp = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).order("id", desc=True).limit(limit).execute()
            items = resp.data or []
        except Exception as e:
            print(f"[imagesync] Failed to fetch images: {e}")
            items = []

        if not items:
            return await interaction.followup.send("📭 No images found in your library.", ephemeral=True)

        total = len(items)
        progress_msg = await interaction.followup.send(embed=discord.Embed(
            title="📤 Paste Starting",
            description=f"Pasting {total} image(s)...",
            color=BLURPLE
        ), ephemeral=True)

        sent = 0
        async with aiohttp.ClientSession() as session:
            for rec in items:
                try:
                    file_bytes = None
                    # prefer storage_path
                    storage_path = rec.get("storage_path")
                    filename = rec.get("filename") or "image.png"
                    if storage_path:
                        try:
                            # download from Supabase Storage
                            data = supabase.storage().from_(BUCKET_NAME).download(storage_path)
                            # depending on client this returns bytes or an object; try to handle both
                            if isinstance(data, (bytes, bytearray)):
                                file_bytes = data
                            else:
                                # if it's a requests-like Response, attempt to read content
                                try:
                                    file_bytes = data.content
                                except Exception:
                                    file_bytes = None
                        except Exception as e:
                            print(f"[imagesync] Failed to download from storage: {e}")
                            file_bytes = None

                    if not file_bytes:
                        # fallback to original URL
                        url = rec.get("url")
                        if not url:
                            continue
                        async with session.get(url) as r:
                            if r.status == 200:
                                file_bytes = await r.read()
                            else:
                                print(f"[imagesync] Failed to download from URL {url} status {r.status}")
                                continue

                    discord_file = discord.File(io.BytesIO(file_bytes), filename=filename)
                    caption = f"**{interaction.user.display_name} • from {rec.get('author')} • {rec.get('timestamp')}**"
                    await interaction.channel.send(content=caption, file=discord_file)
                    sent += 1

                    # update progress message (ephemeral followup replaced with new content)
                    await progress_msg.edit(embed=discord.Embed(
                        title="📤 Pasting Images",
                        description=f"Pasted **{sent}/{total}** images...",
                        color=BLURPLE
                    ))
                    # safe rate limit spacing
                    await asyncio.sleep(0.6)
                except Exception as e:
                    print(f"[imagesync] Error pasting item id {rec.get('id')}: {e}")
                    continue

        await progress_msg.edit(embed=discord.Embed(
            title="✅ Paste Complete",
            description=f"Pasted **{sent}/{total}** image(s).",
            color=GOLD
        ))
        await interaction.followup.send(f"🎉 Finished pasting {sent}/{total} images!", ephemeral=True)

    @app_commands.command(name="listimages", description="List stored images in your library (paginated).")
    async def listimages(self, interaction: discord.Interaction, page: int = 1):
        per_page = 8
        user_id = str(interaction.user.id)
        offset = (max(1, page) - 1) * per_page

        try:
            resp = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).order("id", desc=True).range(offset, offset+per_page-1).execute()
            items = resp.data or []
        except Exception as e:
            print(f"[imagesync] Failed to list images: {e}")
            items = []

        if not items:
            return await interaction.response.send_message("📭 No images found on this page.", ephemeral=True)

        embed = discord.Embed(title=f"📚 Your Images — Page {page}", color=BLURPLE)
        for rec in items:
            name = rec.get("filename") or "image"
            ts = rec.get("timestamp") or "unknown"
            storage = "✅" if rec.get("storage_path") else "🔗"
            embed.add_field(name=name, value=f"{storage} {rec.get('author')} • {ts}", inline=False)

        embed.set_footer(text=f"Use /listimages page:<n> to view other pages")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearimages", description="Clear all images in your library (restricted).")
    async def clearimages(self, interaction: discord.Interaction):
        # restricted: owner (user) or ADMIN_ROLE_ID role
        user = interaction.user
        permitted = (str(user.id) == str(os.getenv("DISCORD_OWNER_ID"))) or self._is_admin(user)
        if not permitted:
            return await interaction.response.send_message("🚫 You don't have permission to run this command.", ephemeral=True)

        user_id = str(user.id)
        try:
            # delete rows (and optionally delete storage objects)
            resp = supabase.table(TABLE_NAME).delete().eq("user_id", user_id).execute()
            # Optionally you can attempt to remove storage objects — left out unless service role key is present
            await interaction.response.send_message("🗑️ Your library has been cleared.", ephemeral=True)
        except Exception as e:
            print(f"[imagesync] Failed to clear images: {e}")
            await interaction.response.send_message("⚠️ Failed to clear images. Check logs.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageSync(bot))