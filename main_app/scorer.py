import copy


def compute_final_price(offer):
    price = float(offer["price"])
    discount = float(offer.get("discount", 0))
    extra_offer = float(offer.get("offer", 0))

    final_price = price - (price * discount / 100) - extra_offer

    if final_price < 1:
        final_price = 1

    return round(final_price, 2)


def rank_offers(offers):

    offers = [copy.deepcopy(o) for o in offers]

    for offer in offers:
        offer["final_price"] = compute_final_price(offer)

   
    ranked_offers = sorted(
        offers,
        key=lambda o: (
            o["final_price"],              
            -o.get("rating", 0),           
            not o.get("availability", True),  
            -o.get("discount", 0)         
        )
    )

    # ------------------------------
    # STEP 3: Assign ranks + score
    # ------------------------------
    for i, offer in enumerate(ranked_offers):
        offer["rank"] = i + 1

        # create readable deal score for UI
        offer["deal_score"] = round(
            (1 / offer["final_price"]) * 100000, 4
        )

    best_offer = ranked_offers[0]

    return ranked_offers, best_offer