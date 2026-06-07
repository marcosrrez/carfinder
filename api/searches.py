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
    # normalize radius key — frontend may send either name
    if "radius" in data and "radius_miles" not in data:
        data["radius_miles"] = data["radius"]
    data.setdefault("radius_miles", 100)
    data.setdefault("interval_hours", 2)
    data.setdefault("city", data.get("zip", ""))
    data.setdefault("trim", "")
    data.setdefault("trims", "")
    data.setdefault("drivetrain", "Any")
    required = ["make", "model", "year", "max_price", "ideal_price",
                "max_miles", "ideal_miles", "zip", "alert_emails"]
    for field in required:
        if not data.get(field):
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
