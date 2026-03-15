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
def normalize_item(item, store):

    return {
        # UNIQUE PER ROW (VERY IMPORTANT FIX)
        "offer_id": str(uuid.uuid4()),

        "name": str(item.get("name", "unknown")).lower().strip(),

        "price": float(item.get("price", 0)),
        "discount": float(item.get("discount", 0)),
        "rating": float(item.get("rating", 0)),
        "offer": float(item.get("offer", 0)),

        "availability": convert_availability(item.get("availability", True)),
        "store": store
    }


# -------------------------------
# Fetch from both ecommerce sites
# -------------------------------
def fetch_all_offers(product_name):

    product_name = product_name.lower().strip()

    offers = []

    # ----------- Ecommerce Site 1 -----------
    try:
        res1 = requests.get(
            "http://127.0.0.1:5010/api/search",
            params={"q": product_name},
            timeout=5
        )

        res1.raise_for_status()
        data1 = res1.json()

        for item in data1:
            offers.append(normalize_item(item, "EcomSite1"))

        print("EcomSite1 fetched:", len(data1))

    except Exception as e:
        print("EcomSite1 connection error:", e)


    # ----------- Ecommerce Site 2 -----------
    try:
        res2 = requests.get(
            "http://127.0.0.1:5020/api/search",
            params={"q": product_name},
            timeout=5
        )

        res2.raise_for_status()
        data2 = res2.json()

        for item in data2:
            offers.append(normalize_item(item, "EcomSite2"))

        print("EcomSite2 fetched:", len(data2))

    except Exception as e:
        print("EcomSite2 connection error:", e)


    print("TOTAL OFFERS FETCHED:", len(offers))

    return offers