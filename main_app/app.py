from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from main_app.scorer import rank_offers
from main_app.memory import add_to_watchlist
from main_app.price_agent import run_agent
from main_app.nlp_processor import process_query
from main_app.fetcher import fetch_all_offers
from main_app.ai_explainer import generate_explanation

import threading
import json
import os
# ✅ SUPABASE IMPORT
from supabase import create_client

# ✅ SUPABASE CONFIG
url = "https://hsyiwhuksmnzkpfezvxn.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"
supabase = create_client(url, key)





app = Flask(__name__)
app.secret_key = "dealai_super_secret_123"


# ---------------- MAKE USER AVAILABLE IN ALL HTML ----------------
@app.context_processor
def inject_user():
    return dict(current_user=session.get("username"))


@app.route("/alerts")
def get_alerts():

    if "user_id" not in session:
        return {"alerts": []}

    user_id = session["user_id"]

    response = supabase.table("alerts") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("id", desc=True) \
        .limit(1) \
        .execute()

    return {"alerts": response.data}

# ---------------------------------------------------
# CLEAR ALERTS
# ---------------------------------------------------
@app.route("/clear-alerts", methods=["POST"])
def clear_alerts():

    if "user_id" not in session:
        return {"status": "no user"}

    user_id = session["user_id"]

    supabase.table("alerts") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()

    return {"status": "cleared"}


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # ✅ Validation
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match!")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters!")

        try:
            # ✅ Insert into Supabase
            supabase.table("users").insert({
                "name": name,
                "email": email,
                "phone": phone,
                "password": password
            }).execute()

            return render_template("register.html", success="Account created successfully!")

        except Exception as e:
            print("REGISTER ERROR:", e)
            return render_template("register.html", error="Registration failed!")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        try:
            # 🔍 Check user in Supabase
            response = supabase.table("users") \
                .select("*") \
                .eq("email", email) \
                .execute()

            if response.data:
                user = response.data[0]

                # 🔐 Password check
                if user["password"] == password:

                    # ✅ Store session
                    session["user_id"] = user["id"]
                    session["username"] = user["email"]

                    return redirect(url_for("home"))

                else:
                    return render_template("login.html", error="Incorrect password")

            else:
                return render_template("login.html", error="User not found")

        except Exception as e:
            print("Login error:", e)
            return render_template("login.html", error="Something went wrong")

    return render_template("login.html")


# ---------------------------------------------------
# ACCOUNT PAGE
# ---------------------------------------------------
@app.route("/account")
def account():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    res = supabase.table("users") \
        .select("*") \
        .eq("id", user_id) \
        .execute()

    user = res.data[0] if res.data else {}

    return render_template("account.html", user=user)

# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------
# WATCHLIST PAGE
# ---------------------------------------------------
@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():

    try:
        if "user_id" not in session:
            return redirect("/login")

        user_id = session["user_id"]
        product = request.form.get("product")

        print("ADDING:", product, user_id)  # DEBUG

        if not product:
            return "Product is empty"

        res = supabase.table("watchlist").insert({
            "user_id": user_id,
            "product": product
        }).execute()

        print("INSERT RESULT:", res.data)

        return redirect("/watchlist")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e)
    

@app.route("/watchlist")
def watchlist():

    try:
        if "user_id" not in session:
            return redirect("/login")

        user_id = session["user_id"]

        res = supabase.table("watchlist") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()

        items = res.data if res.data else []

        print("WATCHLIST DATA:", items)  # DEBUG

        return render_template("watchlist.html", items=items), 200, {
    "Cache-Control": "no-store"
}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e)

# ---------------------------------------------------
@app.route("/remove/<product_name>")
def remove(product_name):

    from flask import session, redirect, url_for
    from supabase import create_client

    # Supabase config (same as your watchlist.py)
    url = "https://hsyiwhuksmnzkpfezvxn.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"
    supabase = create_client(url, key)

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    product_name = product_name.strip().lower()

    # DELETE FROM SUPABASE
    supabase.table("watchlist") \
        .delete() \
        .eq("user_id", user_id) \
        .eq("product", product_name) \
        .execute()

    print(f"❌ Removed from watchlist: {product_name}")

    return redirect(url_for("watchlist"))
#---------------------------------------------------
# MAIN SEARCH
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():

    try:
        product = None

        if request.method == "POST":
            product = request.form.get("product", "").strip()
        else:
            product = request.args.get("product", "").strip()

        if product:

            if product == "":
                return render_template("index.html", offers=[], best=None,
                                       explanation="Please enter a product name.")

            product = process_query(product)

            # ---------------- FETCH OFFERS ----------------
            try:
                offers = fetch_all_offers(product)
            except Exception as e:
                print("FETCH ERROR:", e)
                offers = []

            if not offers:
                offers = [
                    {"price": 50000, "discount": 10, "offer": 2000, "availability": True, "store": "Ecommerce Site 1"},
                    {"price": 48000, "discount": 5, "offer": 1000, "availability": True, "store": "Ecommerce Site 2"}
                ]

            ranked_offers, best_offer = rank_offers(offers)

            # ---------------- ADD TO WATCHLIST ----------------
            if "user_id" in session:
                try:
                    user_id = session["user_id"]

                    print("ADDING TO WATCHLIST:", product, user_id)

                    # ✅ CHECK DUPLICATE
                    existing = supabase.table("watchlist") \
                        .select("*") \
                        .eq("user_id", user_id) \
                        .eq("product", product) \
                        .execute()

                    if not existing.data:
                        supabase.table("watchlist").insert({
                            "user_id": user_id,
                            "product": product,
                            "last_best_price": best_offer.get("final_price", 0),
                            "last_best_store": best_offer.get("store", ""),
                            "last_best_offer_id": best_offer.get("offer_id", "")
                        }).execute()

                        print("✅ Added to watchlist")

                    else:
                        print("⚠️ Already exists in watchlist")

                except Exception as e:
                    print("❌ Watchlist add error:", e)

            # ---------------- UPDATE PRICE ----------------
            try:
                if "user_id" in session:
                    supabase.table("watchlist") \
                        .update({
                            "last_best_price": best_offer.get("final_price", 0),
                            "last_best_store": best_offer.get("store", ""),
                            "last_best_offer_id": best_offer.get("offer_id", "")
                        }) \
                        .eq("product", product) \
                        .eq("user_id", session["user_id"]) \
                        .execute()

            except Exception as e:
                print("❌ Watchlist update error:", e)

            # ---------------- AI EXPLANATION ----------------
            explanation = None
            try:
                if len(ranked_offers) > 1:
                    explanation = generate_explanation(product, ranked_offers, best_offer)
            except Exception as e:
                print("AI error:", e)
                explanation = "AI explanation currently unavailable."

            return render_template("index.html",
                                   offers=ranked_offers,
                                   best=best_offer,
                                   explanation=explanation)

        return render_template("index.html", offers=None, best=None, explanation=None)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e)

# ---------------------------------------------------
# BACKGROUND AGENT
# ---------------------------------------------------
def start_agent():
    with app.app_context():
        run_agent()


if __name__ == "__main__":
    agent_thread = threading.Thread(target=start_agent, daemon=True)
    agent_thread.start()

    app.run(host="0.0.0.0", port=5000)