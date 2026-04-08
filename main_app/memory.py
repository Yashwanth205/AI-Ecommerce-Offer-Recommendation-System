from flask import session
from supabase import create_client

# Supabase config
url = "https://hsyiwhuksmnzkpfezvxn.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"
supabase = create_client(url, key)


# -----------------------------
# Add product to watchlist
# -----------------------------
def add_to_watchlist(product_name, best_offer):

    if "user_id" not in session:
        print("❌ User not logged in")
        return

    user_id = session["user_id"]
    product_name = product_name.strip().lower()

    # Check duplicate
    existing = supabase.table("watchlist") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("product", product_name) \
        .execute()

    if existing.data:
        print("⚠️ Already in watchlist")
        return

    # ✅ INSERT FULL DATA
    data = {
        "user_id": user_id,
        "product": product_name,
        "last_best_price": best_offer.get("final_price", 0),
        "last_best_store": best_offer.get("store", "Unknown"),
        "last_best_offer_id": best_offer.get("offer_id", "")
    }

    print("✅ Saving to Supabase:", data)

    supabase.table("watchlist").insert(data).execute()

    print(f"📌 Added to watchlist: {product_name}")


# -----------------------------
# Update price (VERY IMPORTANT FIX)
# -----------------------------
def update_price(product_name, price, store, offer_id):

    if "user_id" not in session:
        return

    user_id = session["user_id"]
    product_name = product_name.strip().lower()

    # 🔍 Get old price first
    existing = supabase.table("watchlist") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("product", product_name) \
        .execute()

    if not existing.data:
        print("❌ Product not found in watchlist")
        return

    old_price = existing.data[0].get("last_best_price", 0)

    # 🚨 PRICE DROP CHECK
    if price < old_price:
        print(f"🔥 PRICE DROP ALERT for {product_name}!")
        print(f"Old: ₹{old_price} → New: ₹{price}")

    # ✅ Update record
    supabase.table("watchlist") \
        .update({
            "last_best_price": price,
            "last_best_store": store,
            "last_best_offer_id": offer_id
        }) \
        .eq("user_id", user_id) \
        .eq("product", product_name) \
        .execute()

    print(f"🔄 Updated price for {product_name}")