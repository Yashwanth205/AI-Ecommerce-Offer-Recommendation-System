import time
import schedule

from main_app.emailer import send_price_alert
from main_app.fetcher import fetch_all_offers
from main_app.scorer import rank_offers

from supabase import create_client

# ✅ SUPABASE
SUPABASE_URL = "https://hsyiwhuksmnzkpfezvxn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"

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
        # ✅ SAFE FETCH
        try:
            res = supabase.table("watchlist").select("*").execute()
            print("📦 Supabase data:", res.data)
        except Exception as e:
            print("❌ Supabase connection error:", e)
            return
        watchlist = res.data or []

        if not watchlist:
            print("No products in watchlist")
            return

        print("\n🤖 Checking prices...")

        for item in watchlist:

            try:
                user_id = item.get("user_id")
                product = str(item.get("product") or "").strip()
                if not product:
                     print("⚠️ Skipping empty product")
                     continue

                if not user_id or not product:
                    continue

                offers = fetch_all_offers(product)

                if not offers:
                    print("⚠️ No offers for:", product)
                    continue

                ranked_offers, best_offer = rank_offers(offers)

                if not best_offer:
                    continue

                current_price = best_offer.get("final_price", 0)
                current_store = best_offer.get("store", "Unknown")
                current_offer_id = best_offer.get("offer_id", "")

                old_price = item.get("last_best_price", 0)
                old_store = item.get("last_best_store", "")

                print(f"👉 {product}: ₹{current_price}")

                # ---------- PRICE DROP ----------
                if old_price and current_price < old_price:

                    print("🔻 PRICE DROP")

                    try:
                        notify_user(user_id, product, current_store, old_price, current_price, "drop")
                    except Exception as e:
                        print("Notify error:", e)

                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "drop"
                    }).execute()

                # ---------- PRICE INCREASE ----------
                elif old_price and current_price > old_price:

                    print("🔺 PRICE INCREASE")

                    try:
                        notify_user(user_id, product, current_store, old_price, current_price, "increase")
                    except Exception as e:
                        print("Notify error:", e)

                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "increase"
                    }).execute()

                # ---------- STORE CHANGE ----------
                if old_store and current_store != old_store:

                    print("🔄 STORE CHANGE")

                    try:
                        notify_user(user_id, product, current_store, old_price, current_price, "store_change")
                    except Exception as e:
                        print("Notify error:", e)

                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "store_change"
                    }).execute()

                # ---------- UPDATE SUPABASE ----------
                supabase.table("watchlist") \
                    .update({
                        "last_best_price": current_price,
                        "last_best_store": current_store,
                        "last_best_offer_id": current_offer_id
                    }) \
                    .eq("id", item["id"]) \
                    .execute()

            except Exception as e:
                print("Error processing item:", e)

    except Exception as e:
        print("❌ check_prices error:", e)


# run every 10 seconds
schedule.every(30).seconds.do(check_prices)


# ---------------- RUN ----------------
def run_agent():
    print("🧠 Agent started...")
    while True:
        schedule.run_pending()
        time.sleep(2)