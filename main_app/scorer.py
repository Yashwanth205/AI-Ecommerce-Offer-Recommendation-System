import copy


# ---------------- SAFE FLOAT ----------------
def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


# ---------------- FINAL PRICE ----------------
def compute_final_price(offer):
    price = safe_float(offer.get("price"))
    discount = safe_float(offer.get("discount"))
    extra_offer = safe_float(offer.get("offer"))

    final_price = price - (price * discount / 100) - extra_offer

    # avoid zero / negative price
    if final_price <= 0:
        final_price = 1

    return round(final_price, 2)


# ---------------- RANK OFFERS ----------------
def rank_offers(offers):

    print("OFFERS BEFORE RANK:", offers)

    # deep copy
    offers = [copy.deepcopy(o) for o in offers]

    for offer in offers:

        # 🔥 compute price safely
        offer["final_price"] = compute_final_price(offer)

        # 🔥 FIX NAME
        name = offer.get("name")
        if not name or str(name).strip() == "":
            name = "Unknown Product"

        # 🔥 FIX STORE
        store = offer.get("store")
        if not store or str(store).strip() == "":
            store = "Unknown Store"

        offer["name"] = name
        offer["store"] = store

        # 🔥 SAFE VALUES
        offer["rating"] = safe_float(offer.get("rating"))
        offer["discount"] = safe_float(offer.get("discount"))
        offer["availability"] = bool(offer.get("availability", True))

    # ---------------- SORT ----------------
    ranked_offers = sorted(
        offers,
        key=lambda o: (
            o["final_price"],        # lowest price first
            -o["rating"],            # higher rating better
            not o["availability"],   # available first
            -o["discount"]           # higher discount better
        )
    )

    # ---------------- RANKING ----------------
    for i, offer in enumerate(ranked_offers):
        offer["rank"] = i + 1

        # 🔥 SAFE deal score
        try:
            offer["deal_score"] = round((1 / offer["final_price"]) * 100000, 4)
        except:
            offer["deal_score"] = 0

    print("OFFERS AFTER RANK:", ranked_offers)

    best_offer = ranked_offers[0] if ranked_offers else None

    return ranked_offers, best_offer