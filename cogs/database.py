# utils/database.py
"""
Database utility layer for FlagMaps Bot.
Automatically creates required Supabase tables if missing.
"""

from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =======================================================
# 🔧 Automatic Table Setup
# =======================================================

def ensure_tables():
    """
    Automatically create necessary tables if they don't exist.
    Uses Supabase SQL RPC.
    """
    try:
        sql = """
        create table if not exists economy (
            id bigint generated always as identity primary key,
            user_id text unique,
            balance integer default 0,
            created_at timestamp default now()
        );

        create table if not exists punishments (
            id bigint generated always as identity primary key,
            user_id text,
            reason text,
            moderator text,
            timestamp timestamp default now()
        );
        """
        # Use Supabase SQL interface
        supabase.postgrest.rpc("sql", {"query": sql}).execute()
        print("[DB] ✅ Tables ensured successfully.")
    except Exception as e:
        print(f"[DB] ⚠️ Table ensure failed: {e}")


# Call this on import
ensure_tables()

# =======================================================
# 🪙 Economy Functions
# =======================================================

def get_balance(user_id: str) -> int:
    try:
        res = supabase.table("economy").select("balance").eq("user_id", user_id).execute()
        if res.data:
            return int(res.data[0]["balance"])
        else:
            create_user(user_id)
            return 0
    except Exception as e:
        print(f"[DB] get_balance error: {e}")
        return 0


def create_user(user_id: str):
    try:
        supabase.table("economy").insert({
            "user_id": user_id,
            "balance": 0,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"[DB] create_user error: {e}")


def update_balance(user_id: str, amount: int):
    try:
        current = get_balance(user_id)
        new_balance = max(0, current + amount)
        supabase.table("economy").upsert({
            "user_id": user_id,
            "balance": new_balance
        }).execute()
        return new_balance
    except Exception as e:
        print(f"[DB] update_balance error: {e}")
        return current


# =======================================================
# ⚖️ Punishments
# =======================================================

def add_punishment(user_id: str, reason: str, moderator: str):
    try:
        supabase.table("punishments").insert({
            "user_id": user_id,
            "reason": reason,
            "moderator": moderator,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"[DB] add_punishment error: {e}")


def get_punishments(user_id: str):
    try:
        res = supabase.table("punishments").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"[DB] get_punishments error: {e}")
        return []


def clear_punishments(user_id: str):
    try:
        supabase.table("punishments").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"[DB] clear_punishments error: {e}")
        return False