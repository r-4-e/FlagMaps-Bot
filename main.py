import discord
from discord import app_commands
from discord.ext import commands
import sqlite3, aiohttp, io, asyncio, os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("higa")   # 🔹 Load token securely
DISPLAY_NAME = "r4e"                 # 🔹 Name shown when reuploading

# ------------------- Discord Setup -------------------
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ------------------- SQLite Setup -------------------
conn = sqlite3.connect("images.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS images(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT, url TEXT, filename TEXT, timestamp TEXT
)
""")
conn.commit()

# Flag to manage cancellation
active_tasks = {}

# -----------------------------------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")
    print("Slash commands `/copy`, `/paste`, `/status`, `/cancel` are ready!")

# -----------------------------------------------------
@bot.tree.command(name="copy", description="Copy up to 20 latest image attachments from this channel.")
async def copy(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Copying up to 20 images...", ephemeral=True)
    cur.execute("DELETE FROM images")  # Clear previous run
    channel = interaction.channel
    count = 0

    async for msg in channel.history(limit=200):
        if count >= 20:
            break
        for att in msg.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                cur.execute(
                    "INSERT INTO images(author,url,filename,timestamp) VALUES(?,?,?,?)",
                    (str(msg.author), att.url, att.filename, str(msg.created_at))
                )
                count += 1
                if count >= 20:
                    break
    conn.commit()
    await interaction.followup.send(f"✅ Stored `{count}` image(s)` in the database.", ephemeral=True)

# -----------------------------------------------------
@bot.tree.command(name="paste", description="Paste stored images into this channel (progress bar).")
async def paste(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in active_tasks:
        await interaction.response.send_message("⚠️ Paste already running! Use `/cancel` to stop it first.", ephemeral=True)
        return

    await interaction.response.send_message("📤 Uploading stored images...", ephemeral=True)
    cur.execute("SELECT author,url,filename,timestamp FROM images ORDER BY id ASC")
    rows = cur.fetchall()
    if not rows:
        await interaction.followup.send("⚠️ No images found in the database.", ephemeral=True)
        return

    total = len(rows)
    sent = 0
    embed = discord.Embed(
        title="📊 Upload Progress",
        description=f"Starting upload of {total} image(s)...",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Progress", value="0%", inline=False)
    progress_msg = await interaction.channel.send(embed=embed)

    active_tasks[user_id] = True  # mark active

    async with aiohttp.ClientSession() as session:
        for author, url, filename, timestamp in rows:
            if not active_tasks.get(user_id):
                await interaction.followup.send("⛔ Paste cancelled.", ephemeral=True)
                break
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        file = discord.File(io.BytesIO(data), filename=filename)
                        caption = f"**{DISPLAY_NAME} (from {author} at {timestamp})**"
                        await interaction.channel.send(content=caption, file=file)
                        sent += 1

                        if sent % 5 == 0 or sent == total:
                            percent = int((sent / total) * 100)
                            embed.set_field_at(0, name="Progress", value=f"{percent}% ({sent}/{total})", inline=False)
                            await progress_msg.edit(embed=embed)
                        await asyncio.sleep(0.5)  # safe rate-limit
            except Exception as e:
                print(f"⚠️ Error uploading {filename}: {e}")

    # 🟢 Keep images stored (no delete)
    del active_tasks[user_id]

    embed.color = discord.Color.green()
    embed.description = f"✅ Uploaded {sent}/{total} image(s). Images remain stored in the database."
    embed.set_field_at(0, name="Progress", value="100%", inline=False)
    await progress_msg.edit(embed=embed)
    await interaction.followup.send(f"🎉 Finished uploading {sent} image(s)!", ephemeral=True)

# -----------------------------------------------------
@bot.tree.command(name="status", description="Check stored image count and details.")
async def status(interaction: discord.Interaction):
    cur.execute("SELECT id, filename, author FROM images ORDER BY id ASC")
    rows = cur.fetchall()
    if not rows:
        await interaction.response.send_message("📂 Database is empty.", ephemeral=True)
        return

    total = len(rows)
    names = "\n".join([f"{i+1}. {r[1]} (by {r[2]})" for i, r in enumerate(rows[:10])])
    if total > 10:
        names += f"\n...and {total - 10} more"
    embed = discord.Embed(
        title="🗂️ Stored Images",
        description=f"Currently stored: **{total}** image(s)",
        color=discord.Color.gold()
    )
    embed.add_field(name="Preview", value=names or "No files", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -----------------------------------------------------
@bot.tree.command(name="cancel", description="Cancel an ongoing /paste upload.")
async def cancel(interaction: discord.Interaction):
    user_id = interaction.user.id
    if active_tasks.get(user_id):
        active_tasks[user_id] = False
        await interaction.response.send_message("🛑 Paste process cancelled.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ No active paste process found.", ephemeral=True)

# -----------------------------------------------------
bot.run(TOKEN)
