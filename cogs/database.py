# cogs/database.py
import os
from supabase import create_client, Client

# ------------------- Supabase Connection -------------------
def init_supabase() -> Client:
    """Initialize and return a Supabase client connection."""
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase database.")
    return client

supabase: Client = init_supabase()

# ------------------- Auto Table Initialization -------------------
def ensure_base_tables():
    """Automatically create all required Elura tables if they don't exist."""
    print("⚙️ Verifying Supabase tables...")

    tables = {
        "settings": """
            CREATE TABLE IF NOT EXISTS settings (
                guild_id TEXT PRIMARY KEY,
                language TEXT DEFAULT 'en',
                welcome_channel TEXT,
                welcome_image TEXT,
                modlog_channel TEXT
            );
        """,
        "economy": """
            CREATE TABLE IF NOT EXISTS economy (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                balance BIGINT DEFAULT 0,
                last_daily TEXT,
                UNIQUE (guild_id, user_id)
            );
        """,
        "cases": """
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
        """,
        "message_counter": """
            CREATE TABLE IF NOT EXISTS message_counter (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                count BIGINT DEFAULT 0,
                last_updated TEXT,
                UNIQUE (guild_id, user_id)
            );
        """,
        "welcomes": """
            CREATE TABLE IF NOT EXISTS welcomes (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                join_date TEXT,
                welcome_image TEXT,
                UNIQUE (guild_id, user_id)
            );
        """
    }

    try:
        # Test a simple query first
        supabase.table("settings").select("*").limit(1).execute()
    except Exception:
        print("🧩 Creating tables (first-time setup)...")
        for name, ddl in tables.items():
            try:
                supabase.postgrest.rpc("exec", {"sql": ddl}).execute()
                print(f"✅ Table ready: {name}")
            except Exception as e:
                print(f"⚠️ Failed creating {name}: {e}")
        print("🎉 Supabase setup complete.")
    else:
        print("✅ All Supabase tables verified.")

# Run verification automatically
ensure_base_tables()