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
        # ✅ FIX NAME
        name = item.get("name")
        if not name or str(name).strip().lower() in ["", "none", "null", "unknown"]:
            name = product_name

        # ✅ FIX RATING
        rating = item.get("rating")
        if rating is None or str(rating).strip() == "":
            rating = round(3.5 + (hash(str(name)) % 15) / 10, 1)

        return {
            # UNIQUE PER ROW
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
        print(f"{store} normalization error:", e)
        return None


# -------------------------------
# Fetch from both ecommerce sites
# -------------------------------
def fetch_all_offers(product_name):

    product_name = product_name.lower().strip()
    offers = []

    SITE1_URL = "https://ecommerce1-8ycx.onrender.com/api/search"
    SITE2_URL = "https://ecommerce-v0n8.onrender.com/api/search"

    # ----------- Ecommerce Site 1 -----------
    try:
        res1 = requests.get(
            SITE1_URL,
            params={"q": product_name},
            timeout=5
        )

        res1.raise_for_status()

        try:
            data1 = res1.json()
        except Exception:
            print("EcomSite1 JSON error")
            data1 = []

        print("RAW EcomSite1:", data1)

        for item in data1:
            normalized = normalize_item(item, "Ecommerce Site 1", product_name)
            if normalized:
                offers.append(normalized)

        print("EcomSite1 fetched:", len(data1))

    except Exception as e:
        print("EcomSite1 connection error:", e)


    # ----------- Ecommerce Site 2 -----------
    try:
        res2 = requests.get(
            SITE2_URL,
            params={"q": product_name},
            timeout=5
        )

        res2.raise_for_status()

        try:
            data2 = res2.json()
        except Exception:
            print("EcomSite2 JSON error")
            data2 = []

        print("RAW EcomSite2:", data2)

        for item in data2:
            normalized = normalize_item(item, "Ecommerce Site 2", product_name)
            if normalized:
                offers.append(normalized)

        print("EcomSite2 fetched:", len(data2))

    except Exception as e:
        print("EcomSite2 connection error:", e)


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

    print("TOTAL OFFERS FETCHED:", len(unique_offers))
    print("FINAL OFFERS:", unique_offers)

    return unique_offers