from flask import Flask, jsonify
from server.db import init_db
from server.endpoints import vault_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(vault_bp)

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        init_db()

    return app


app = create_app()