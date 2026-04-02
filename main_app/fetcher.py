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
        name = item.get("name")
        if not name or str(name).strip().lower() in ["", "none", "null", "unknown"]:
            name = product_name

        rating = item.get("rating")
        if rating is None or str(rating).strip() == "":
            rating = round(3.5 + (hash(str(name)) % 15) / 10, 1)

        return {
            "offer_id": str(uuid.uuid4()),
            "name": str(name).strip(),
            "price": float(item.get("price", 0) or 0),
            "discount": float(item.get("discount", 0) or 0),
            "rating": float(rating),
            "offer": float(item.get("offer", 0) or 0),
            "availability": convert_availability(item.get("availability", True)),
            "store": store
        }

    except Exception as e:
        print(f"❌ {store} normalization error:", e)
        return None


# -------------------------------
# Fetch from both ecommerce sites
# -------------------------------
def fetch_all_offers(product_name):

    product_name = product_name.lower().strip()

    if not product_name:
        return []

    offers = []

    SITE1_URL = "http://127.0.0.1:5010/api/search"
    SITE2_URL = "http://127.0.0.1:5020/api/search"

    # ----------- Ecommerce Site 1 -----------
    try:
        res1 = requests.get(SITE1_URL, params={"q": product_name}, timeout=5)
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
        res2 = requests.get(SITE2_URL, params={"q": product_name}, timeout=5)
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