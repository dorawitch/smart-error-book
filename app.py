import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import MAX_CONTENT_LENGTH
from models.models import init_db
from routes.error_routes import error_bp


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    CORS(app)

    init_db()
    app.register_blueprint(error_bp)

    @app.route("/", methods=["GET"])
    def healthcheck():
        return jsonify({"msg": "Smart Error Book API is running"})

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
