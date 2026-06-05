# app.py
import os
import threading
from flask import Flask, g
from flask_cors import CORS
from models import Database

_db_lock = threading.Lock()
_db_instance = None

def get_db(db_path: str = None) -> Database:
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = Database(db_path or os.environ.get("DB_PATH", "carfinder.db"))
    return _db_instance

def create_app(db_path: str = None) -> Flask:
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            os.environ.get("FRONTEND_URL", ""),
        ],
        "allow_headers": ["Content-Type", "X-User-Id", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    }})

    db = Database(db_path or os.environ.get("DB_PATH", "carfinder.db"))

    @app.before_request
    def attach_db():
        g.db = db

    from api import register_blueprints
    register_blueprints(app)

    return app

app = create_app()
