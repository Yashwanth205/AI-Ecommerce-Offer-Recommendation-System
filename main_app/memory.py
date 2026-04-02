import os
from supabase import create_client
from flask import session

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# Add product to watchlist
# -----------------------------
def add_to_watchlist(product_name, best_offer):

    if "user_id" not in session:
        print("❌ User not logged in")
        return

    if not best_offer:
        print("❌ No best offer found")
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

    data = {
        "user_id": user_id,
        "product": product_name,
        "last_best_price": float(best_offer.get("final_price", 0)),
        "last_best_store": best_offer.get("store", "Unknown"),
        "last_best_offer_id": best_offer.get("offer_id", "")
    }

    print("✅ Saving to Supabase:", data)

    supabase.table("watchlist").insert(data).execute()

    print(f"📌 Added to watchlist: {product_name}")


# -----------------------------
# Update price (FIXED)
# -----------------------------
def update_price(product_name, price, store, offer_id):

    if "user_id" not in session:
        return

    user_id = session["user_id"]
    product_name = product_name.strip().lower()

    # 🔍 Get old price
    existing = supabase.table("watchlist") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("product", product_name) \
        .execute()

    if not existing.data:
        print("❌ Product not found in watchlist")
        return

    old_price = float(existing.data[0].get("last_best_price", 0))

    # ---------------- PRICE DROP ----------------
    if price < old_price:
        print(f"🔥 PRICE DROP ALERT for {product_name}!")

        # ✅ SAVE ALERT (IMPORTANT FIX)
        supabase.table("alerts").insert({
            "user_id": user_id,
            "product": product_name,
            "old_price": old_price,
            "new_price": price,
            "type": "drop"
        }).execute()

    # ---------------- PRICE INCREASE ----------------
    elif price > old_price:
        print(f"🔺 PRICE INCREASE for {product_name}")

        supabase.table("alerts").insert({
            "user_id": user_id,
            "product": product_name,
            "old_price": old_price,
            "new_price": price,
            "type": "increase"
        }).execute()

    # ---------------- UPDATE WATCHLIST ----------------
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