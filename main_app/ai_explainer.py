import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


# ---------------------------------
# Format offer for LLM
# ---------------------------------
def format_offer(offer):

    return f"""
Store: {offer['store']}
Product: {offer['name']}
Original Price: ₹{offer['price']}
Final Payable Price: ₹{offer['final_price']}
Discount: {offer['discount']}%
Extra Offer: ₹{offer.get('offer', 0)}
Rating: {offer['rating']}⭐
Availability: {"In Stock" if offer.get('availability', True) else "Out of Stock"}
"""


# ---------------------------------
# Generate explanation
# ---------------------------------
def generate_explanation(product, offers, best_offer):

    # competitors = all except rank 1
    competitors = [o for o in offers if o.get("rank") != 1]

    best_text = format_offer(best_offer)
    others_text = "\n\n".join([format_offer(o) for o in competitors])

    # --- Accurate comparison text ---
    comparisons = ""
    for o in competitors:
        diff = round(o["final_price"] - best_offer["final_price"], 2)

        if diff > 0:
            comparisons += f"\nCompared to {o['store']}, this deal saves ₹{diff}."
        elif diff < 0:
            comparisons += f"\nThis deal is ₹{abs(diff)} costlier than {o['store']}."
        else:
            comparisons += f"\nThis deal has the same price as {o['store']}."

    # ---- Prompt ----
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

    # ---- Call Ollama safely ----
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=40)

        if response.status_code != 200:
            return fallback_explanation(best_offer)

        data = response.json()

        # Ollama sometimes returns without 'response'
        if "response" not in data:
            return fallback_explanation(best_offer)

        return data["response"].strip()

    except Exception as e:
        print("Ollama Error:", e)
        return fallback_explanation(best_offer)


# ---------------------------------
# Backup explanation (VERY IMPORTANT)
# ---------------------------------
def fallback_explanation(best_offer):

    return (
        f"The system recommends {best_offer['name']} from {best_offer['store']} "
        f"because it has the lowest final payable price of ₹{best_offer['final_price']}. "
        f"It also offers a {best_offer['discount']}% discount with a rating of "
        f"{best_offer['rating']} stars and is currently available. "
        f"Considering price savings and product quality together, this deal provides "
        f"the best overall value among the available options."
    )