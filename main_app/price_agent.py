import time
import schedule
try:
    from .emailer import send_price_alert
    from .fetcher import fetch_all_offers
    from .scorer import rank_offers
except ImportError:
    from emailer import send_price_alert
    from fetcher import fetch_all_offers
    from scorer import rank_offers
from supabase import create_client
import os

supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
PRICE_CHECK_INTERVAL_SECONDS = max(15, int(os.environ.get("PRICE_CHECK_INTERVAL_SECONDS", "60")))


def get_user_email(user_id):
    try:
        res = supabase.table("users").select("email").eq("id", user_id).execute()
        if res.data:
            return res.data[0]["email"]
    except Exception as e:
        print("Email fetch error:", e)
    return None


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


def check_prices():
    try:
        res = supabase.table("watchlist").select("*").execute()
        watchlist = res.data or []

        if not watchlist:
            print("No products in watchlist")
            return

        print("\n🤖 Checking prices...")

        for item in watchlist:
            try:
                user_id = item.get("user_id")
                product = item.get("product")

                if not user_id or not product:
                    continue

                offers = fetch_all_offers(product)
                if not offers:
                    continue

                ranked_offers, best_offer = rank_offers(offers)
                if not best_offer:
                    continue

                current_price = best_offer.get("final_price", 0)
                current_store = best_offer.get("store", "Unknown")
                current_offer_id = best_offer.get("offer_id", "")
                old_price = item.get("last_best_price", 0)
                old_store = item.get("last_best_store", "")

                if old_price and current_price < old_price:
                    notify_user(user_id, product, current_store, old_price, current_price, "drop")
                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "drop"
                    }).execute()

                elif old_price and current_price > old_price:
                    notify_user(user_id, product, current_store, old_price, current_price, "increase")
                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "increase"
                    }).execute()

                if old_store and current_store != old_store:
                    notify_user(user_id, product, current_store, old_price, current_price, "store_change")
                    supabase.table("alerts").insert({
                        "user_id": user_id,
                        "product": product,
                        "old_price": old_price,
                        "new_price": current_price,
                        "type": "store_change"
                    }).execute()

                supabase.table("watchlist").update({
                    "last_best_price": current_price,
                    "last_best_store": current_store,
                    "last_best_offer_id": current_offer_id
                }).eq("id", item["id"]).execute()

            except Exception as e:
                print("Error processing item:", e)

    except Exception as e:
        print("❌ check_prices error:", e)


schedule.every(PRICE_CHECK_INTERVAL_SECONDS).seconds.do(check_prices)


def run_agent():
    print("🧠 Agent started...")
    check_prices()  # run once immediately

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print("Agent loop error:", e)
            time.sleep(5)