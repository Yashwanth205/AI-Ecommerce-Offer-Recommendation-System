import time
import schedule

from main_app.emailer import send_price_alert
from main_app.fetcher import fetch_all_offers
from main_app.scorer import rank_offers

from supabase import create_client

# ✅ SUPABASE
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase initialized")


# ---------------- GET USER EMAIL ----------------
def get_user_email(user_id):
    try:
        res = supabase.table("users").select("email").eq("id", user_id).execute()
        if res.data:
            return res.data[0]["email"]
    except Exception as e:
        print("Email fetch error:", e)

    return None


# ---------------- SEND EMAIL ----------------
def notify_user(user_id, product, store, old_price, new_price, alert_type):

    email = get_user_email(user_id)

    if not email:
        print("❌ No email found")
        return

    try:
        send_price_alert(email, product, store, old_price, new_price)
        print(f"📧 Alert sent to {email}")
    except Exception as e:
        print("Email error:", e)


# ---------------- MAIN AGENT ----------------
def check_prices():

    try:
        # 🔹 Fetch watchlist
        try:
            res = supabase.table("watchlist").select("*").execute()
            watchlist = res.data or []
            print("📦 Watchlist:", watchlist)
        except Exception as e:
            print("❌ Supabase error:", e)
            return

        if not watchlist:
            print("⚠️ No products in watchlist")
            return

        print("\n🤖 Checking prices...\n")

        for item in watchlist:

            try:
                user_id = item.get("user_id")
                product = str(item.get("product") or "").strip()

                if not user_id or not product:
                    print("⚠️ Invalid watchlist item")
                    continue

                # 🔹 Fetch offers
                offers = fetch_all_offers(product)

                if not offers:
                    print("⚠️ No offers for:", product)
                    continue

                # 🔹 Rank offers
                ranked_offers, best_offer = rank_offers(offers)

                if not best_offer:
                    continue

                # 🔥 USE final_price (IMPORTANT)
                current_price = best_offer.get("final_price", 0)
                current_store = best_offer.get("store", "Unknown")
                current_offer_id = best_offer.get("offer_id", "")

                old_price = item.get("last_best_price", 0)
                old_store = item.get("last_best_store", "")

                print(f"👉 {product}: ₹{current_price}")

                # ---------------- FIRST TIME ----------------
                if not old_price:
                    print("🆕 First time tracking")

                # ---------------- PRICE DROP ----------------
                elif current_price < old_price:
                    print("🔻 PRICE DROP")

                    notify_user(user_id, product, current_store, old_price, current_price, "drop")

                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "drop"
                    }).execute()

                # ---------------- PRICE INCREASE ----------------
                elif current_price > old_price:
                    print("🔺 PRICE INCREASE")

                    notify_user(user_id, product, current_store, old_price, current_price, "increase")

                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "increase"
                    }).execute()

                # ---------------- STORE CHANGE ----------------
                if old_store and current_store != old_store:
                    print("🔄 STORE CHANGE")

                    notify_user(user_id, product, current_store, old_price, current_price, "store_change")

                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "store_change"
                    }).execute()

                # ---------------- UPDATE WATCHLIST ----------------
                supabase.table("watchlist") \
                    .update({
                        "last_best_price": current_price,
                        "last_best_store": current_store,
                        "last_best_offer_id": current_offer_id
                    }) \
                    .eq("id", item["id"]) \
                    .execute()

            except Exception as e:
                print("❌ Error processing item:", e)

    except Exception as e:
        print("❌ check_prices error:", e)


# ---------------- SCHEDULER (OPTIONAL) ----------------
schedule.every(30).seconds.do(check_prices)


# ---------------- RUN AGENT (FOR /run-agent ROUTE) ----------------
def run_agent():
    print("🧠 Agent triggered manually...")
    check_prices()