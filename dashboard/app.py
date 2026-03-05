"""Flask application factory for CR Obituaries Dashboard."""

from flask import Flask, jsonify

from dashboard.config import Config
from dashboard.db import close_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register teardown for DB connections
    app.teardown_appcontext(close_db)

    # Health check
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # Register routes blueprint
    from dashboard.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
