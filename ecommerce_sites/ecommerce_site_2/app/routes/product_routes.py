from flask import Blueprint, request, redirect, url_for, render_template, jsonify
import sqlite3

product_bp = Blueprint("products", __name__)

DB_PATH = "app/database/database.db"


# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    # important: prevents locking when AI agent + browser both access DB
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ---------------- VIEW PRODUCTS ----------------
@product_bp.route("/products")
def view_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    return render_template("products.html", products=products)


# ---------------- ADD PRODUCT ----------------
@product_bp.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        discount = request.form["discount"]
        availability = request.form["availability"]
        rating = request.form["rating"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO products (name, price, discount, availability, rating) VALUES (?, ?, ?, ?, ?)",
            (name, price, discount, availability, rating),
        )

        conn.commit()
        conn.close()

        return redirect(url_for("products.view_products"))

    return render_template("add_product.html")


# ---------------- EDIT PRODUCT ----------------
@product_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        discount = request.form["discount"]
        availability = request.form["availability"]
        rating = request.form["rating"]

        cursor.execute("""
            UPDATE products
            SET name=?, price=?, discount=?, availability=?, rating=?
            WHERE id=?
        """, (name, price, discount, availability, rating, id))

        conn.commit()
        conn.close()

        return redirect(url_for("products.view_products"))

    cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    product = cursor.fetchone()
    conn.close()

    return render_template("edit_product.html", product=product)


# ---------------- DELETE PRODUCT ----------------
@product_bp.route("/delete/<int:id>")
def delete_product(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("products.view_products"))


# ===================== FIXED SEARCH API =====================
@product_bp.route("/api/search")
def search_products():

    query = request.args.get("q", "").strip().lower()

    # if no query -> return empty safely
    if query == "":
        return jsonify([])

    conn = get_connection()
    cursor = conn.cursor()

    # 🔥 CRITICAL FIX:
    # LOWER(name) makes search case-insensitive
    cursor.execute("""
        SELECT id, name, price, discount, availability, rating
        FROM products
        WHERE LOWER(name) LIKE ?
    """, ('%' + query + '%',))

    results = cursor.fetchall()
    conn.close()

    products = []

    for p in results:
        products.append({
            "id": p[0],
            "name": p[1],
            "price": float(p[2]),
            "discount": float(p[3]),
            "availability": p[4],
            "rating": float(p[5])
        })

    return jsonify(products)


# ---------------- GET SINGLE PRODUCT API ----------------
@product_bp.route("/api/product/<int:id>")
def get_product(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    p = cursor.fetchone()

    conn.close()

    if not p:
        return jsonify({"error": "Product not found"}), 404

    product = {
        "id": p[0],
        "name": p[1],
        "price": float(p[2]),
        "discount": float(p[3]),
        "availability": p[4],
        "rating": float(p[5])
    }

    return jsonify(product)