from supabase import create_async_client, Client
from dotenv import load_dotenv
import os
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


supabase: Client = None
async def init_supabase():
    global supabase
    supabase = await create_async_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

async def get_by_email(email: str) -> dict | None:
    respone = await supabase.table("user").select("*").eq("email", email).execute()

    if not respone.data:
        return None
    return respone.data[0]

async def get_by_id(user_id: int) -> dict | None:
    response = await supabase.table("user").select("*").eq("id", user_id).execute()
    if not response:
        return None
    return response.data[0]

async def create(email: str, name: str, password_hash: str) -> dict:
    respone = await supabase.table("user").insert({
        "email": email,
        "name": name,
        "password_hash": password_hash
    }).execute()
    return respone.data[0]

async def change(id: int, email: str, name: str, password_hash: str) -> dict:
    response = await supabase.table("user").update({
        "email": email,
        "name": name,
        "password_hash": password_hash
    }).eq("id", id).execute()
    return response.data[0]
