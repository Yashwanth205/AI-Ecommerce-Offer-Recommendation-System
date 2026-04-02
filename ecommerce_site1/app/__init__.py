from flask import Flask, render_template
from app.models.product_model import create_table, add_rating_column, get_connection
from app.routes.product_routes import product_bp


def create_app():
    app = Flask(__name__)

    # ✅ Safe DB init
    try:
        create_table()
        add_rating_column()
    except Exception as e:
        print("DB init error:", e)

    # Register routes
    app.register_blueprint(product_bp)

    @app.route("/")
    def home():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        conn.close()

        return render_template("products.html", products=products)

    return app