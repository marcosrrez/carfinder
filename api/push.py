from flask import Blueprint, request, jsonify, g

push_bp = Blueprint("push", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@push_bp.route("/api/push/vapid-public-key", methods=["GET"])
def get_vapid_key():
    import os
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    return jsonify({"key": key})

@push_bp.route("/api/push/subscribe", methods=["POST"])
def subscribe():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    sub = data.get("subscription", {})
    keys = sub.get("keys", {})
    g.db.save_push_subscription(
        user_id,
        sub.get("endpoint", ""),
        keys.get("p256dh", ""),
        keys.get("auth", "")
    )
    return jsonify({"ok": True})

@push_bp.route("/api/push/unsubscribe", methods=["POST"])
def unsubscribe():
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    endpoint = data.get("endpoint", "")
    g.db.delete_push_subscription(user_id, endpoint)
    return jsonify({"ok": True})
