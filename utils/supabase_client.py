import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing Supabase credentials (SUPABASE_URL or SUPABASE_KEY) in .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_connection():
    """
    Verifies connection to Supabase.
    Use only for testing or debugging.
    """
    try:
        supabase.table("settings").select("*").limit(1).execute()
        print("✅ Supabase connection successful!")
    except Exception as e:
        print(f"⚠️ Supabase connection failed: {e}")