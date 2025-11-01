import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# ------------------- Load environment -------------------
load_dotenv()
TOKEN = os.getenv("higa")  # 🔹 Bot token from .env

# ------------------- Bot Setup -------------------
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ------------------- Events -------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print("🔧 Slash commands are synced and bot is ready!")
    print("💾 Connected with Supabase backend and cogs loaded.")

# ------------------- Load All Cogs -------------------
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"🧩 Loaded cog: {filename}")
            except Exception as e:
                print(f"⚠️ Failed to load cog {filename}: {e}")

# ------------------- Start Bot -------------------
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())