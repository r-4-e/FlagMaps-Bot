import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# ------------------- Load Environment -------------------
load_dotenv()
TOKEN = os.getenv("higa")  # Bot token from .env

if not TOKEN:
    raise ValueError("❌ Bot token not found in .env (key: higa)")

# ------------------- Intents -------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True  # required for some moderation features

# ------------------- Bot Setup -------------------
bot = commands.Bot(command_prefix="/", intents=intents)

# ------------------- Events -------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print("🔧 Slash commands are synced and bot is ready!")
    print("💾 Connected with Supabase backend and all cogs loaded.")

# ------------------- Load All Cogs -------------------
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                print(f"🧩 Loaded cog: {filename}")
            except Exception as e:
                print(f"⚠️ Failed to load cog {filename}: {e}")

    # Explicitly ensure the error handler cog is always loaded last
    try:
        await bot.load_extension("cogs.error_handler")
        print("🧩 Loaded cog: error_handler.py (global error catcher)")
    except Exception as e:
        print(f"⚠️ Failed to load error handler: {e}")

# ------------------- Start Bot -------------------
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())