from flask import Flask
from app.models.product_model import create_table, add_rating_column
from app.routes.product_routes import product_bp
from flask import render_template
from app.models.product_model import get_connection


def create_app():
    app = Flask(__name__)

    create_table()
    add_rating_column()

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

