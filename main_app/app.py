from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from main_app.scorer import rank_offers
from main_app.memory import add_to_watchlist
from main_app.price_agent import run_agent
from main_app.user_model import create_user_table
from main_app.nlp_processor import process_query
from main_app.fetcher import fetch_all_offers
from main_app.ai_explainer import generate_explanation

import threading
import json
import os
import sqlite3
# ✅ SUPABASE IMPORT
from supabase import create_client

# ✅ SUPABASE CONFIG
url = "https://hsyiwhuksmnzkpfezvxn.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhzeWl3aHVrc21uemtwZmV6dnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzMTEyNTMsImV4cCI6MjA4OTg4NzI1M30.A7XOs-uKHJoH4sLMYjXEJ-AB361JBZHYbfm4DfXllSI"
supabase = create_client(url, key)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "users.db")


app = Flask(__name__)
app.secret_key = "dealai_super_secret_123"


# ---------------- MAKE USER AVAILABLE IN ALL HTML ----------------
@app.context_processor
def inject_user():
    return dict(current_user=session.get("username"))


# ---------------- ALERT FILE ----------------
ALERTS_PATH = os.path.join(BASE_DIR, "../database/alerts.json")


# ---------------- INITIALIZE USER DATABASE ----------------
create_user_table()


# ---------------------------------------------------
# GET ALERTS
# ---------------------------------------------------
@app.route("/alerts")
def get_alerts():
    response = supabase.table("alerts").select("*").execute()
    return {"alerts": response.data}


# ---------------------------------------------------
# CLEAR ALERTS
# ---------------------------------------------------
@app.route("/clear-alerts", methods=["POST"])
def clear_alerts():
    supabase.table("alerts").delete().neq("id", 0).execute()
    return {"status": "cleared"}


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
                (username, email, phone, password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return render_template("register.html", error="Email already registered. Please login.")

    return render_template("register.html")


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "SELECT id, username, email, phone, password FROM users WHERE email=?",
            (email,)
        )

        user = cur.fetchone()
        conn.close()

        if user and user[4] == password:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]
            session["phone"] = user[3]

            return redirect(url_for("home"))

        else:
            return render_template("login.html", error="Invalid Email or Password")

    return render_template("login.html")


# ---------------------------------------------------
# ACCOUNT PAGE
# ---------------------------------------------------
@app.route("/account")
def account():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "account.html",
        username=session.get("username"),
        email=session.get("email"),
        phone=session.get("phone")
    )


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
@app.route("/watchlist")
def watchlist_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        with open("../database/watchlist.json", "r") as f:
            watchlist = json.load(f)
    except:
        watchlist = []

    return render_template("watchlist.html", watchlist=watchlist)

# ---------------------------------------------------
# REMOVE PRODUCT FROM WATCHLIST
@app.route("/remove_watch/<product_name>")
def remove_watch(product_name):

    if "user_id" not in session:
        return redirect(url_for("login"))

    # correct paths (very important)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    watchlist_path = os.path.join(base_dir, "../database/watchlist.json")
    alerts_path = os.path.join(base_dir, "../database/alerts.json")

    try:
        # ---------- REMOVE FROM WATCHLIST ----------
        if os.path.exists(watchlist_path):
            with open(watchlist_path, "r") as f:
                watchlist = json.load(f)
        else:
            watchlist = []

        updated_watchlist = []
        for item in watchlist:
            if item.get("product", "").lower() != product_name.lower():
                updated_watchlist.append(item)

        with open(watchlist_path, "w") as f:
            json.dump(updated_watchlist, f, indent=4)

        # ---------- REMOVE OLD ALERTS ----------
        if os.path.exists(alerts_path):
            with open(alerts_path, "r") as f:
                alerts = json.load(f)

            updated_alerts = []
            for alert in alerts:
                if alert.get("product", "").lower() != product_name.lower():
                    updated_alerts.append(alert)

            with open(alerts_path, "w") as f:
                json.dump(updated_alerts, f, indent=4)

        print(f"Removed '{product_name}' from watchlist and alerts.")

    except Exception as e:
        print("Error removing from watchlist:", e)

    return redirect(url_for("watchlist_page"))
#---------------------------------------------------
# MAIN SEARCH
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():

    product = None

    # 🔥 HANDLE BOTH POST + GET
    if request.method == "POST":
        product = request.form.get("product", "").strip()
    else:
        product = request.args.get("product", "").strip()

    if product:

        if product == "":
            return render_template("index.html", offers=[], best=None,
                                   explanation="Please enter a product name.")

        product = process_query(product)

        offers = fetch_all_offers(product)

        if not offers:
            return render_template("index.html", offers=[], best=None,
                                   explanation="No products found. Make sure both ecommerce servers are running.")

        ranked_offers, best_offer = rank_offers(offers)

        add_to_watchlist(product)

        explanation = None
        try:
            if len(ranked_offers) > 1:
                explanation = generate_explanation(product, ranked_offers, best_offer)
        except Exception as e:
            print("AI explanation error:", e)
            explanation = "AI explanation currently unavailable."

        return render_template("index.html",
                               offers=ranked_offers,
                               best=best_offer,
                               explanation=explanation)

    # 🔥 DEFAULT HOME
    return render_template("index.html", offers=None, best=None, explanation=None)


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