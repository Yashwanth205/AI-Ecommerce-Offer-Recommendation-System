import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


# ---------------------------------
# Safe final price calculation
# ---------------------------------
def get_final_price(offer):
    return float(offer.get("final_price") or (
        float(offer.get("price", 0)) -
        (float(offer.get("price", 0)) * float(offer.get("discount", 0)) / 100) -
        float(offer.get("offer", 0))
    ))


# ---------------------------------
# Format offer for LLM
# ---------------------------------
def format_offer(offer):

    final_price = get_final_price(offer)

    return f"""
Store: {offer.get('store')}
Product: {offer.get('name')}
Original Price: ₹{offer.get('price')}
Final Payable Price: ₹{final_price}
Discount: {offer.get('discount')}%
Extra Offer: ₹{offer.get('offer', 0)}
Rating: {offer.get('rating')}⭐
Availability: {"In Stock" if offer.get('availability', True) else "Out of Stock"}
"""


# ---------------------------------
# Generate explanation
# ---------------------------------
def generate_explanation(product, offers, best_offer):

    try:
        competitors = [o for o in offers if o.get("rank") != 1]

        best_text = format_offer(best_offer)
        others_text = "\n\n".join([format_offer(o) for o in competitors])

        comparisons = ""
        best_price = get_final_price(best_offer)

        for o in competitors:
            other_price = get_final_price(o)
            diff = round(other_price - best_price, 2)

            if diff > 0:
                comparisons += f"\nCompared to {o.get('store')}, this deal saves ₹{diff}."
            elif diff < 0:
                comparisons += f"\nThis deal is ₹{abs(diff)} costlier than {o.get('store')}."
            else:
                comparisons += f"\nThis deal has the same price as {o.get('store')}."

        prompt = f"""
You are an AI shopping assistant.

User searched: {product}

BEST DEAL:
{best_text}

OTHER DEALS:
{others_text}

PRICE COMPARISON:
{comparisons}

Explain why the best deal is ranked first.

Rules:
- Focus mainly on FINAL PAYABLE PRICE.
- Also compare discount, rating, and availability.
- Use the given numbers only.
- Do not invent data.
- Write 120-150 words in simple English.
"""

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=40)

        if response.status_code != 200:
            return fallback_explanation(best_offer)

        data = response.json()

        if "response" not in data:
            return fallback_explanation(best_offer)

        return data["response"].strip()

    except Exception as e:
        print("AI explanation error:", e)
        return fallback_explanation(best_offer)


# ---------------------------------
# Backup explanation (VERY IMPORTANT)
# ---------------------------------
def fallback_explanation(best_offer):

    final_price = get_final_price(best_offer)

    return (
        f"The system recommends {best_offer.get('name')} from {best_offer.get('store')} "
        f"because it has the lowest final payable price of ₹{final_price}. "
        f"It also offers a {best_offer.get('discount')}% discount with a rating of "
        f"{best_offer.get('rating')} stars and is currently available. "
        f"Considering price savings and product quality together, this deal provides "
        f"the best overall value among the available options."
    )