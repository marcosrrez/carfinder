# api/searches.py
from flask import Blueprint, request, jsonify, g

searches_bp = Blueprint("searches", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@searches_bp.route("/api/searches", methods=["GET"])
def list_searches():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    searches = g.db.list_searches(user_id)
    return jsonify(searches)

@searches_bp.route("/api/searches", methods=["POST"])
def create_search():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    data["user_id"] = user_id
    required = ["make", "model", "year", "max_price", "ideal_price",
                "max_miles", "ideal_miles", "zip", "city", "alert_email"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    search = g.db.create_search(data)
    return jsonify(search), 201

@searches_bp.route("/api/searches/<search_id>", methods=["GET"])
def get_search(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    return jsonify(search)

@searches_bp.route("/api/searches/<search_id>", methods=["PUT"])
def update_search(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    updated = g.db.update_search(search_id, request.get_json())
    return jsonify(updated)

@searches_bp.route("/api/searches/<search_id>", methods=["DELETE"])
def delete_search(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    g.db.delete_search(search_id)
    return jsonify({"deleted": True})
