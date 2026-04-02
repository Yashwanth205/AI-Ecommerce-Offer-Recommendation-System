import copy


def compute_final_price(offer):
    price = float(offer.get("price", 0))
    discount = float(offer.get("discount", 0))
    extra_offer = float(offer.get("offer", 0))

    final_price = price - (price * discount / 100) - extra_offer

    if final_price < 1:
        final_price = 1

    return round(final_price, 2)


def rank_offers(offers):

    # ✅ DEBUG BEFORE
    print("OFFERS BEFORE RANK:", offers)

    # deep copy to avoid modifying original
    offers = [copy.deepcopy(o) for o in offers]

    for offer in offers:
        offer["final_price"] = compute_final_price(offer)

        # ✅ ENSURE IMPORTANT FIELDS EXIST
        offer["name"] = offer.get("name", "Unknown Product")
        offer["store"] = offer.get("store", "Unknown Store")
        offer["rating"] = float(offer.get("rating", 0))
        offer["availability"] = offer.get("availability", True)
        offer["discount"] = float(offer.get("discount", 0))

    # ------------------------------
    # SORTING (BEST FIRST)
    # ------------------------------
    ranked_offers = sorted(
        offers,
        key=lambda o: (
            o["final_price"],                 
            -o["rating"],                    
            not o["availability"],           
            -o["discount"]                   
        )
    )

    # ------------------------------
    # ASSIGN RANKS
    # ------------------------------
    for i, offer in enumerate(ranked_offers):
        offer["rank"] = i + 1

        # deal score for UI
        offer["deal_score"] = round(
            (1 / offer["final_price"]) * 100000, 4
        )

    # ✅ DEBUG AFTER
    print("OFFERS AFTER RANK:", ranked_offers)

    best_offer = ranked_offers[0] if ranked_offers else None

    return ranked_offers, best_offer