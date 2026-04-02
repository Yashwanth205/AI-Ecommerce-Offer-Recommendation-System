from flask import Flask, render_template
from app.routes.product_routes import product_bp


def create_app():
    app = Flask(__name__)

    # Register routes
    app.register_blueprint(product_bp)

    @app.route("/")
    def home():
        from app.models.product_model import get_all_products

        products = get_all_products()

        return render_template("products.html", products=products)

    return app