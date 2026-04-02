from flask import Blueprint, request, redirect, url_for, render_template, jsonify
from app.models.product_model import get_all_products, add_product
import os
from supabase import create_client

product_bp = Blueprint("products", __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------- VIEW PRODUCTS ----------------
@product_bp.route("/products")
def view_products():
    products = get_all_products()
    return render_template("products.html", products=products)


# ---------------- ADD PRODUCT ----------------
@product_bp.route("/add", methods=["GET", "POST"])
def add_product_route():
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        discount = int(request.form.get("discount", 0))
        availability = request.form["availability"]
        rating = float(request.form.get("rating", 0))

        add_product(name, price, discount, availability, rating)

        return redirect(url_for("products.view_products"))

    return render_template("add_product.html")


# ---------------- EDIT PRODUCT ----------------
@product_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        discount = int(request.form.get("discount", 0))
        availability = request.form["availability"]
        rating = float(request.form.get("rating", 0))

        supabase.table("products").update({
            "name": name,
            "price": price,
            "discount": discount,
            "availability": availability,
            "rating": rating
        }).eq("id", id).execute()

        return redirect(url_for("products.view_products"))

    # GET single product
    response = supabase.table("products").select("*").eq("id", id).single().execute()
    product = response.data

    return render_template("edit_product.html", product=product)


# ---------------- DELETE PRODUCT ----------------
@product_bp.route("/delete/<int:id>")
def delete_product(id):
    supabase.table("products").delete().eq("id", id).execute()
    return redirect(url_for("products.view_products"))


# ---------------- SEARCH API ----------------
@product_bp.route("/api/search")
def search_products():
    query = request.args.get("q", "").strip().lower()

    if query == "":
        return jsonify([])

    response = supabase.table("products").select("*").ilike("name", f"%{query}%").execute()

    return jsonify(response.data)


# ---------------- GET SINGLE PRODUCT ----------------
@product_bp.route("/api/product/<int:id>")
def get_product(id):
    response = supabase.table("products").select("*").eq("id", id).single().execute()

    if not response.data:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(response.data)