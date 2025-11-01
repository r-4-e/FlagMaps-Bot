import os
from supabase import create_client, Client

# ------------------- Supabase Connection -------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------- Auto Table Initialization -------------------
def ensure_base_tables():
    """Auto-create all required tables for Elura utilities if missing."""
    try:
        # Quick test query to verify connection
        supabase.table("settings").select("*").limit(1).execute()
    except Exception:
        print("⚙️ Initializing Supabase tables...")

        # Core table creation DDLs
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

        for name, ddl in tables.items():
            supabase.postgrest.rpc("exec", {"sql": ddl}).execute()
            print(f"✅ Created or verified table: {name}")

        print("🎉 Supabase setup complete.")


# Run on import
ensure_base_tables()