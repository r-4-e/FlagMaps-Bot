import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sqlite3

# Load environment variables (.env)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client | None = None
local = None

# Initialize Supabase or fallback to SQLite
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase successfully!")
    else:
        raise ValueError("Supabase credentials not found.")
except Exception as e:
    print(f"⚠️ Supabase unavailable: {e}")
    print("💾 Using local SQLite fallback (data.db)")
    local = sqlite3.connect("data.db")
    local.row_factory = sqlite3.Row


class Database:
    """Centralized database helper for Supabase + SQLite fallback."""

    def __init__(self):
        self.supabase = supabase
        self.local = local

        if self.local:
            self.create_local_tables()

        if self.supabase:
            self.ensure_remote_tables()

    # === Supabase Setup ===
    def ensure_remote_tables(self):
        """Ensure Supabase has all required tables."""
        try:
            ddl = """
            CREATE TABLE IF NOT EXISTS economy (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                balance BIGINT DEFAULT 0,
                UNIQUE (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                guild_id TEXT PRIMARY KEY,
                welcome_channel TEXT,
                modlog_channel TEXT
            );

            CREATE TABLE IF NOT EXISTS cases (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                case_id BIGINT NOT NULL,
                case_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                moderator_id TEXT NOT NULL,
                reason TEXT,
                timestamp TEXT,
                UNIQUE (guild_id, case_id)
            );
            """
            self.supabase.postgrest.rpc("exec", {"sql": ddl}).execute()
            print("✅ Verified Supabase schema for economy + punishments.")
        except Exception as e:
            print(f"⚠️ Could not verify Supabase tables: {e}")

    # === SQLite Setup ===
    def create_local_tables(self):
        """Fallback local tables."""
        cur = self.local.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS economy (
            guild_id TEXT,
            user_id TEXT,
            balance INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            guild_id TEXT PRIMARY KEY,
            welcome_channel TEXT,
            modlog_channel TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            case_id INTEGER,
            case_type TEXT,
            user_id TEXT,
            moderator_id TEXT,
            reason TEXT,
            timestamp TEXT
        )
        """)
        self.local.commit()
        print("💾 Local SQLite tables verified.")

    # === Economy methods ===
    async def fetch_economy(self, guild_id, user_id):
        if self.supabase:
            data = self.supabase.table("economy").select("*").eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute().data
            return data[0] if data else None
        cur = self.local.cursor()
        cur.execute("SELECT * FROM economy WHERE guild_id=? AND user_id=?", (str(guild_id), str(user_id)))
        return cur.fetchone()

    async def update_economy(self, guild_id, user_id, balance):
        if self.supabase:
            self.supabase.table("economy").upsert({
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "balance": balance
            }).execute()
        else:
            cur = self.local.cursor()
            cur.execute("INSERT OR REPLACE INTO economy (guild_id, user_id, balance) VALUES (?, ?, ?)",
                        (str(guild_id), str(user_id), balance))
            self.local.commit()


# Global db object (import this in cogs)
db = Database()