import time
import json
import schedule
import sqlite3
import os

from emailer import send_price_alert
from fetcher import fetch_all_offers
from scorer import rank_offers

# ✅ SUPABASE IMPORT
from supabase import create_client

# ✅ SUPABASE CONFIG
url = "https://hsyiwhuksmnzkpfezvxn.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"
supabase = create_client(url, key)


# ---------- SAFE PATHS ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_PATH = os.path.join(BASE_DIR, "../database/watchlist.json")
ALERTS_PATH = os.path.join(BASE_DIR, "../database/alerts.json")
USERS_DB_PATH = os.path.join(BASE_DIR, "../database/users.db")


# ---------------- LOAD WATCHLIST ----------------
def load_watchlist():
    try:
        with open(WATCHLIST_PATH, "r") as f:
            return json.load(f)
    except:
        return []


# ---------------- SAVE WATCHLIST ----------------
def save_watchlist(data):
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ---------------- SAVE ALERT ----------------
def save_alert(product, store, old_price, new_price, alert_type):

    try:
        with open(ALERTS_PATH, "r") as f:
            alerts = json.load(f)
    except:
        alerts = []

    alerts.append({
        "product": product,
        "store": store,
        "old_price": old_price,
        "new_price": new_price,
        "type": alert_type,
        "timestamp": time.time()
    })

    with open(ALERTS_PATH, "w") as f:
        json.dump(alerts, f, indent=4)


# ---------------- GET USER EMAIL ----------------
def get_user_email(user_id):
    try:
        conn = sqlite3.connect(USERS_DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT email FROM users WHERE id=?", (user_id,))
        user = cur.fetchone()

        conn.close()

        if user:
            return user[0]

    except Exception as e:
        print("Email fetch error:", e)

    return None


# ---------------- SEND EMAIL ALERT ----------------
def notify_user(user_id, product, store, old_price, new_price, alert_type):

    email = get_user_email(user_id)

    if not email:
        print("No email found for user:", user_id)
        return

    try:
        send_price_alert(
            email,
            product,
            store,
            old_price,
            new_price
        )

        print(f"📧 Alert sent to {email}")

    except Exception as e:
        print("Email sending error:", e)


# ---------------- MAIN AGENT LOGIC ----------------
def check_prices():

    watchlist = load_watchlist()

    if not watchlist:
        print("No products in watchlist")
        return

    print("\n🤖 Agent checking prices...")

    updated = False

    for item in watchlist:

        if "user_id" not in item:
            continue

        user_id = item["user_id"]
        product = item["product"]

        offers = fetch_all_offers(product)
        if not offers:
            continue

        ranked_offers, best_offer = rank_offers(offers)

        if not best_offer:
            continue

        current_price = best_offer["final_price"]
        current_store = best_offer["store"]
        current_offer_id = best_offer["offer_id"]

        # ---------- FIRST TIME MEMORY ----------
        if item.get("last_best_price") is None:
            item["last_best_price"] = current_price
            item["last_best_store"] = current_store
            item["last_best_offer_id"] = current_offer_id
            updated = True
            continue

        old_price = item["last_best_price"]
        old_store = item.get("last_best_store")

        # ---------- PRICE DROP ----------
        if current_price < old_price:

            print("\n🔻 PRICE DROP DETECTED")
            print(product, old_price, "→", current_price)

            save_alert(product, current_store, old_price, current_price, "drop")
            notify_user(user_id, product, current_store, old_price, current_price, "drop")

            # ✅ SUPABASE INSERT
            supabase.table("alerts").insert({
                "user_id": user_id,
                "product": product,
                "old_price": old_price,
                "new_price": current_price,
                "type": "drop"
            }).execute()

        # ---------- PRICE INCREASE ----------
        elif current_price > old_price:

            print("\n🔺 PRICE INCREASE DETECTED")
            print(product, old_price, "→", current_price)

            save_alert(product, current_store, old_price, current_price, "increase")
            notify_user(user_id, product, current_store, old_price, current_price, "increase")

            # ✅ SUPABASE INSERT
            supabase.table("alerts").insert({
                "user_id": user_id,
                "product": product,
                "old_price": old_price,
                "new_price": current_price,
                "type": "increase"
            }).execute()

        # ---------- STORE CHANGE ----------
        if current_store != old_store:

            print("\n🔄 BETTER STORE FOUND")
            print(old_store, "→", current_store)

            save_alert(product, current_store, old_price, current_price, "store_change")
            notify_user(user_id, product, current_store, old_price, current_price, "store_change")

            # ✅ SUPABASE INSERT
            supabase.table("alerts").insert({
                "user_id": user_id,
                "product": product,
                "old_price": old_price,
                "new_price": current_price,
                "type": "store_change"
            }).execute()

        # ---------- UPDATE MEMORY ----------
        if current_price != old_price or current_store != old_store:
            item["last_best_price"] = current_price
            item["last_best_store"] = current_store
            item["last_best_offer_id"] = current_offer_id
            updated = True

    if updated:
        save_watchlist(watchlist)


# run every 10 seconds
schedule.every(10).seconds.do(check_prices)


# ---------------- AGENT RUNNER ----------------
def run_agent():
    print("🧠 Price Monitoring Agent Started...")
    while True:
        schedule.run_pending()
        time.sleep(2)