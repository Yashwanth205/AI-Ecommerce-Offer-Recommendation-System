import os
from supabase import create_client

# Load env variables
SUPABASE_URL = os.getenv("https://hsyiwhuksmnzkpfezvxn.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ✅ Get all products
def get_all_products():
    response = supabase.table("products").select("*").execute()
    return response.data


# ✅ Add product
def add_product(name, price, discount, availability, rating):
    supabase.table("products").insert({
        "name": name,
        "price": price,
        "discount": discount,
        "availability": availability,
        "rating": rating
    }).execute()