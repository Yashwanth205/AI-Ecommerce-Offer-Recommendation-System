import requests
import uuid


# -------------------------------
# Convert availability to BOOLEAN
# -------------------------------
def convert_availability(value):

    if isinstance(value, str):
        value = value.lower().strip()
        return value in ["in stock", "available", "yes", "true", "1"]

    return bool(value)


# -------------------------------
# Normalize API → AI format
# -------------------------------
def normalize_item(item, store, product_name):

    try:
        name = item.get("name") or product_name

        return {
            "offer_id": str(uuid.uuid4()),
            "name": name,
            "price": float(item.get("price", 0)),
            "discount": float(item.get("discount", 0)),
            "rating": float(item.get("rating", 0)),
            "offer": 0,  # you are not using this in DB
            "availability": convert_availability(item.get("availability", True)),
            "store": store
        }

    except Exception as e:
        print("ERROR:", e)
        return None


# -------------------------------
# Fetch from both ecommerce sites
# -------------------------------
def fetch_all_offers(product_name):

    product_name = product_name.lower().strip()

    if not product_name:
        return []

    offers = []

    SITE1_URL = "https://ecommerce1-8ycx.onrender.com"
    SITE2_URL = "https://ecommerce-v0n8.onrender.com"

    # ----------- Ecommerce Site 1 -----------
    try:
        res1 = requests.get(f"{SITE1_URL}/api/search", params={"q": product_name})
        res1.raise_for_status()

        data1 = res1.json()

        for item in data1:
            normalized = normalize_item(item, "Ecommerce Site 1", product_name)
            if normalized:
                offers.append(normalized)

    except Exception as e:
        print("❌ EcomSite1 error:", e)


    # ----------- Ecommerce Site 2 -----------
    try:
        res2 = requests.get(f"{SITE2_URL}/api/search", params={"q": product_name})
        res2.raise_for_status()

        data2 = res2.json()

        for item in data2:
            normalized = normalize_item(item, "Ecommerce Site 2", product_name)
            if normalized:
                offers.append(normalized)

    except Exception as e:
        print("❌ EcomSite2 error:", e)


    # -------------------------------
    # REMOVE DUPLICATES
    # -------------------------------
    unique_offers = []
    seen = set()

    for o in offers:
        key = o["offer_id"]
        if key not in seen:
            seen.add(key)
            unique_offers.append(o)

    return unique_offers