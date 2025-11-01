import os
from discord.ext import commands
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def ensure_tables_exist():
    """
    Automatically ensures that all required tables exist in Supabase.
    Safe to call multiple times — won't duplicate tables.
    """
    required_tables = {
        "images": """
            CREATE TABLE IF NOT EXISTS images (
                id BIGSERIAL PRIMARY KEY,
                author TEXT,
                url TEXT,
                filename TEXT,
                timestamp TEXT
            );
        """,
        "economy": """
            CREATE TABLE IF NOT EXISTS economy (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT,
                balance BIGINT DEFAULT 0,
                last_daily TIMESTAMP
            );
        """,
        "punishments": """
            CREATE TABLE IF NOT EXISTS punishments (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT,
                moderator_id TEXT,
                type TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            );
        """
    }

    for name, query in required_tables.items():
        try:
            # Check if table exists by attempting a select
            supabase.table(name).select("*").limit(1).execute()
            print(f"🗄️ Verified table: {name}")
        except Exception:
            print(f"⚙️ Creating missing table: {name}")
            try:
                # Run SQL command safely via RPC
                supabase.postgrest.rpc("sql", {"query": query})
                print(f"✅ Table '{name}' created successfully.")
            except Exception as e:
                print(f"❌ Failed to ensure table '{name}': {e}")


class Database(commands.Cog):
    """Auto-handles Supabase setup and connection"""

    def __init__(self, bot):
        self.bot = bot
        ensure_tables_exist()

    @commands.Cog.listener()
    async def on_ready(self):
        print("🧩 Database Cog ready and tables ensured.")


async def setup(bot):
    await bot.add_cog(Database(bot))