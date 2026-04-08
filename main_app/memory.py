from flask import session
from supabase import create_client
import os

try:
    from .emailer import send_price_alert
except ImportError:
    from emailer import send_price_alert

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)


def add_to_watchlist(product_name, best_offer):
    if "user_id" not in session:
        print("❌ User not logged in")
        return

    user_id = session["user_id"]
    product_name = product_name.strip().lower()

    existing = supabase.table("watchlist").select("*").eq("user_id", user_id).eq("product", product_name).execute()

    if existing.data:
        print("⚠️ Already in watchlist")
        return

    data = {
        "user_id": user_id,
        "product": product_name,
        "last_best_price": best_offer.get("final_price", 0),
        "last_best_store": best_offer.get("store", "Unknown"),
        "last_best_offer_id": best_offer.get("offer_id", "")
    }

    supabase.table("watchlist").insert(data).execute()
    print(f"📌 Added to watchlist: {product_name}")


def update_price(product_name, price, store, offer_id):
    if "user_id" not in session:
        return

    user_id = session["user_id"]
    product_name = product_name.strip().lower()

    existing = supabase.table("watchlist").select("*").eq("user_id", user_id).eq("product", product_name).execute()

    if not existing.data:
        print("❌ Product not found in watchlist")
        return

    old_price = existing.data[0].get("last_best_price", 0)

    user_email = session.get("username")

    # ✅ INSERT ALERT if price changed
    if old_price and price < old_price:
        supabase.table("alerts").insert({
            "user_id": user_id,
            "product": product_name,
            "old_price": old_price,
            "new_price": price,
            "type": "drop"
        }).execute()
        print(f"🔥 PRICE DROP ALERT inserted for {product_name}")

        if user_email:
            try:
                send_price_alert(user_email, product_name, store, old_price, price)
                print(f"📧 Price drop email sent to {user_email}")
            except Exception as e:
                print(f"❌ Price drop email failed for {user_email}:", e)

    elif old_price and price > old_price:
        supabase.table("alerts").insert({
            "user_id": user_id,
            "product": product_name,
            "old_price": old_price,
            "new_price": price,
            "type": "increase"
        }).execute()

        if user_email:
            try:
                send_price_alert(user_email, product_name, store, old_price, price)
                print(f"📧 Price increase email sent to {user_email}")
            except Exception as e:
                print(f"❌ Price increase email failed for {user_email}:", e)

    supabase.table("watchlist").update({
        "last_best_price": price,
        "last_best_store": store,
        "last_best_offer_id": offer_id
    }).eq("user_id", user_id).eq("product", product_name).execute()

    print(f"🔄 Updated price for {product_name}")