import json
import os
from flask import session

# absolute safe path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_PATH = os.path.join(BASE_DIR, "../database/watchlist.json")


# -----------------------------
# Create file if not exists
# -----------------------------
def ensure_file():
    if not os.path.exists(WATCHLIST_PATH):
        with open(WATCHLIST_PATH, "w") as f:
            json.dump([], f)


# -----------------------------
# Load watchlist safely
# -----------------------------
def load_watchlist():
    ensure_file()

    try:
        with open(WATCHLIST_PATH, "r") as f:
            data = json.load(f)

            # file corrupted protection
            if not isinstance(data, list):
                return []

            return data

    except Exception as e:
        print("Watchlist read error:", e)
        return []


# -----------------------------
# Save watchlist
# -----------------------------
def save_watchlist(data):
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# Add product to watchlist (PER USER)
# -----------------------------
def add_to_watchlist(product):

    # If not logged in → do nothing
    if "user_id" not in session:
        return

    user_id = session["user_id"]

    # normalize product name
    product = product.strip().lower()

    watchlist = load_watchlist()

    # prevent duplicate FOR SAME USER ONLY
    for item in watchlist:
        if item["product"] == product and item["user_id"] == user_id:
            return

    # add new tracking item
    watchlist.append({
        "user_id": user_id,
        "product": product,
        "last_best_price": None,
        "last_best_store": None,
        "last_best_offer_id": None
    })

    save_watchlist(watchlist)
    print(f"📌 Added to watchlist: {product} (User {user_id})")


# -----------------------------
# Update best price (AGENT USE)
# -----------------------------
def update_price(product_name, price, store, offer_id):

    product_name = product_name.strip().lower()
    watchlist = load_watchlist()

    updated = False

    for item in watchlist:

        if item["product"] == product_name:
            item["last_best_price"] = price
            item["last_best_store"] = store
            item["last_best_offer_id"] = offer_id
            updated = True

    if updated:
        save_watchlist(watchlist)