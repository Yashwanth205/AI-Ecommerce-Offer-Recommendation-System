import requests
import uuid


# ---------------- SAFE FLOAT ----------------
def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


# ---------------- AVAILABILITY ----------------
def convert_availability(value):
    if isinstance(value, str):
        value = value.lower().strip()
        return value in ["in stock", "available", "yes", "true", "1"]
    return bool(value)


# ---------------- NORMALIZE ----------------
def normalize_item(item, store, product_name):

    try:
        # 🔥 FIX NAME
        name = item.get("name")
        if not name or str(name).strip() == "":
            name = product_name

        price = safe_float(item.get("price"))
        discount = safe_float(item.get("discount"))
        rating = safe_float(item.get("rating"))

        final_price = price - (price * discount / 100)

        return {
            "offer_id": str(uuid.uuid4()),
            "name": name,
            "price": price,
            "discount": discount,
            "rating": rating,
            "final_price": final_price,
            "availability": convert_availability(item.get("availability", True)),
            "store": store
        }

    except Exception as e:
        print("❌ normalize error:", e)
        return None


# ---------------- FETCH ----------------
def fetch_all_offers(product_name):

    product_name = product_name.lower().strip()

    if not product_name:
        return []

    offers = []

    SITE1_URL = "https://ecommerce1-8ycx.onrender.com/api/search"
    SITE2_URL = "https://ecommerce-v0n8.onrender.com/api/search"

    # -------- SITE 1 --------
    try:
        res1 = requests.get(SITE1_URL, params={"q": product_name}, timeout=5)
        data1 = res1.json()

        print("SITE1:", data1)

        for item in data1:
            o = normalize_item(item, "Site 1", product_name)
            if o:
                offers.append(o)

    except Exception as e:
        print("❌ Site1 error:", e)

    # -------- SITE 2 --------
    try:
        res2 = requests.get(SITE2_URL, params={"q": product_name}, timeout=5)
        data2 = res2.json()

        print("SITE2:", data2)

        for item in data2:
            o = normalize_item(item, "Site 2", product_name)
            if o:
                offers.append(o)

    except Exception as e:
        print("❌ Site2 error:", e)

    # ---------------- REMOVE DUPLICATES (FIXED) ----------------
    unique = {}
    for o in offers:
        key = (o["name"], o["store"])  # 🔥 FIX
        if key not in unique:
            unique[key] = o

    return list(unique.values())