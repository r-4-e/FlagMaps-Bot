import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing Supabase credentials in .env")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------------
# Utility functions for image sync storage
# -------------------------------------------------------

async def ensure_table_exists():
    """
    Ensures that the 'images' table exists in Supabase.
    If not found, it auto-creates the table.
    """
    try:
        # Supabase doesn't provide a native table creation API,
        # so we rely on an insert test to check table existence.
        test = supabase.table("images").select("*").limit(1).execute()
        if test.data is not None:
            print("🗂️ Supabase table 'images' found and ready.")
    except Exception as e:
        print("⚠️ Table 'images' may not exist. Please ensure schema:")
        print("""
        CREATE TABLE IF NOT EXISTS images (
            id bigint generated always as identity primary key,
            user_id text,
            author text,
            url text,
            filename text,
            timestamp text
        );
        """)
        print(f"Error: {e}")

# -------------------------------------------------------
# CRUD Functions
# -------------------------------------------------------

def insert_image(user_id: str, author: str, url: str, filename: str, timestamp: str):
    """Insert a new image record into Supabase."""
    try:
        supabase.table("images").insert({
            "user_id": user_id,
            "author": author,
            "url": url,
            "filename": filename,
            "timestamp": timestamp
        }).execute()
        return True
    except Exception as e:
        print(f"⚠️ Insert failed for {filename}: {e}")
        return False


def fetch_images(user_id: str):
    """Fetch all images saved by a specific user."""
    try:
        res = supabase.table("images").select("*").eq("user_id", user_id).order("id").execute()
        return res.data or []
    except Exception as e:
        print(f"⚠️ Fetch failed: {e}")
        return []


def clear_images(user_id: str):
    """Clear all stored images for a user."""
    try:
        supabase.table("images").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"⚠️ Clear failed: {e}")
        return False