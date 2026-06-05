# api/scan.py
import threading
from flask import Blueprint, request, jsonify, g

scan_bp = Blueprint("scan", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@scan_bp.route("/api/scan", methods=["POST"])
def scan_all():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    from scheduler import trigger_scan_for_user
    threading.Thread(target=trigger_scan_for_user, args=(user_id,), daemon=True).start()
    return jsonify({"status": "scan started"})

@scan_bp.route("/api/searches/<search_id>/scan", methods=["POST"])
def scan_one(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    from scheduler import trigger_scan_for_search
    threading.Thread(target=trigger_scan_for_search, args=(search,), daemon=True).start()
    return jsonify({"status": "scan started"})

@scan_bp.route("/api/status", methods=["GET"])
def status():
    from scheduler import get_status
    return jsonify(get_status())
