from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
try:
    from .scorer import rank_offers
    from .memory import add_to_watchlist, update_price
    from .price_agent import run_agent, check_prices
    from .nlp_processor import process_query
    from .fetcher import fetch_all_offers
    from .ai_explainer import generate_explanation
except ImportError:
    from scorer import rank_offers
    from memory import add_to_watchlist, update_price
    from price_agent import run_agent, check_prices
    from nlp_processor import process_query
    from fetcher import fetch_all_offers
    from ai_explainer import generate_explanation

import threading
import json
import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dealai_super_secret_123")
agent_thread_started = False


@app.context_processor
def inject_user():
    return dict(current_user=session.get("username"))


@app.route("/alerts")
def get_alerts():
    user_id = session.get("user_id")
    if not user_id:
        return {"alerts": []}
    response = supabase.table("alerts").select("*").eq("user_id", user_id).execute()
    return {"alerts": response.data}


@app.route("/clear-alerts", methods=["POST"])
def clear_alerts():
    user_id = session.get("user_id")
    if not user_id:
        return {"status": "not logged in"}
    supabase.table("alerts").delete().eq("user_id", user_id).execute()
    return {"status": "cleared"}


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")
        name = request.form.get("name")
        phone = request.form.get("phone")

        if password != confirm:
            return render_template("register.html", error="Passwords do not match")

        try:
            existing = supabase.table("users").select("*").eq("email", email).execute()
            if existing.data:
                return render_template("register.html", error="User already exists")

            supabase.table("users").insert({
                "email": email,
                "password": password,
                "name": name,
                "phone": phone
            }).execute()

            return redirect(url_for("login"))

        except Exception as e:
            print("Register error:", e)
            return render_template("register.html", error="Registration failed")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
            if response.data:
                user = response.data[0]
                if user["password"] == password:
                    session["user_id"] = user["id"]
                    session["username"] = user["email"]
                    session["name"] = user.get("name", "")
                    session["phone"] = user.get("phone", "")
                    return redirect(url_for("home"))
                else:
                    return render_template("login.html", error="Incorrect password")
            else:
                return render_template("login.html", error="User not found")
        except Exception as e:
            print("Login error:", e)
            return render_template("login.html", error="Something went wrong")
    return render_template("login.html")


@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = {
        "name": session.get("name", ""),
        "email": session.get("username", ""),
        "phone": session.get("phone", "")
    }
    return render_template("account.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/watchlist")
def watchlist():
    try:
        if "user_id" not in session:
            return redirect("/login")
        user_id = session["user_id"]
        res = supabase.table("watchlist").select("*").eq("user_id", user_id).execute()
        items = res.data if res.data else []
        return render_template("watchlist.html", items=items)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e)


@app.route("/remove/<product_name>")
def remove(product_name):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    product_name = product_name.strip().lower()
    supabase.table("watchlist").delete().eq("user_id", user_id).eq("product", product_name).execute()
    return redirect(url_for("watchlist"))


@app.route("/run-agent", methods=["GET", "POST"])
def run_agent_route():
    try:
        check_prices()
        return jsonify({"status": "agent check completed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET", "POST"])
def home():
    try:
        product = None
        if request.method == "POST":
            product = request.form.get("product", "").strip()
        else:
            product = request.args.get("product", "").strip()

        if product:
            product = process_query(product)

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

            if "user_id" in session and best_offer:
                try:
                    add_to_watchlist(product, best_offer)
                except Exception as e:
                    print("Watchlist add error:", e)

                try:
                    update_price(
                        product,
                        best_offer["final_price"],
                        best_offer["store"],
                        best_offer["offer_id"]
                    )
                except Exception as e:
                    print("Watchlist update error:", e)

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


def start_agent():
    with app.app_context():
        run_agent()


def ensure_agent_thread_started():
    global agent_thread_started
    if agent_thread_started:
        return

    if os.environ.get("ENABLE_PRICE_AGENT", "true").lower() != "true":
        print("Price agent disabled by ENABLE_PRICE_AGENT")
        return

    agent_thread = threading.Thread(target=start_agent, daemon=True)
    agent_thread.start()
    agent_thread_started = True
    print("Price agent background thread started")


ensure_agent_thread_started()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)