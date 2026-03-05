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

    # Network diagnostic endpoint
    @app.route("/api/health/net")
    def health_net():
        import socket
        host = app.config["DB_HOST"]
        port = app.config["DB_PORT"]
        result = {"host": host, "port": port}
        try:
            result["resolved_ips"] = [ip[4][0] for ip in socket.getaddrinfo(host, port)]
        except Exception as exc:
            result["dns_error"] = str(exc)
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            result["tcp_connect"] = "ok"
        except Exception as exc:
            result["tcp_connect_error"] = str(exc)
        return jsonify(result)

    # DB health check (diagnose connection issues)
    @app.route("/api/health/db")
    def health_db():
        try:
            from dashboard.db import get_db
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM obituaries")
            count = cursor.fetchone()[0]
            cursor.close()
            return jsonify({"status": "ok", "obituary_count": count})
        except Exception as exc:
            return jsonify({"status": "error", "error": str(exc)}), 500

    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(exc):
        import traceback
        app.logger.error("Unhandled exception: %s", traceback.format_exc())
        return f"<h1>500 Internal Server Error</h1><pre>{exc}</pre>", 500

    # Register routes blueprint
    from dashboard.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
