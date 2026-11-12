from supabase import Client,create_client
from app.auth.config import Settings


supabase : Client = create_client(
    supabase_url=Settings.SUPABASE_URL,
    supabase_key=Settings.SUPABASE_KEY
)