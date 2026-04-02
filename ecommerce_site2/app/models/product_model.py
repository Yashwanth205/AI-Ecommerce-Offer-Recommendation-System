import os
from supabase import create_client

# ✅ Correct way
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_all_products():
    response = supabase.table("products2").select("*").execute()
    return response.data


def add_product(name, price, discount, availability, rating):
    supabase.table("products2").insert({
        "name": name,
        "price": price,
        "discount": discount,
        "availability": availability,
        "rating": rating
    }).execute()