# api/listings.py
from flask import Blueprint, request, jsonify, g

listings_bp = Blueprint("listings", __name__)

def require_user():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    return user_id

@listings_bp.route("/api/searches/<search_id>/listings", methods=["GET"])
def get_listings(search_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    search = g.db.get_search(search_id)
    if not search or search["user_id"] != user_id:
        return jsonify({"error": "Not found"}), 404
    listings = g.db.get_listings(search_id)
    saved_ids = set(g.db.get_saved_ids(user_id))
    hidden_ids = set(g.db.get_hidden_ids(user_id))
    from scorer import score_listing, deal_for
    result = []
    for l in listings:
        if l["id"] in hidden_ids:
            continue
        tier = score_listing(l, search)
        if not tier:
            continue
        deal = deal_for(l)
        result.append({
            **l,
            "tier": tier,
            "deal": deal,
            "saved": l["id"] in saved_ids,
        })
    result.sort(key=lambda x: (["ideal","good","ok"].index(x["tier"]), x["deal"]["delta"], x["price"]))
    return jsonify(result)

@listings_bp.route("/api/listings/<listing_id>/save", methods=["POST"])
def save_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.save_listing(user_id, listing_id)
    return jsonify({"saved": True})

@listings_bp.route("/api/listings/<listing_id>/save", methods=["DELETE"])
def unsave_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.unsave_listing(user_id, listing_id)
    return jsonify({"saved": False})

@listings_bp.route("/api/listings/<listing_id>/hide", methods=["POST"])
def hide_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.hide_listing(user_id, listing_id)
    return jsonify({"hidden": True})

@listings_bp.route("/api/listings/<listing_id>/hide", methods=["DELETE"])
def unhide_listing(listing_id):
    user_id = require_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    g.db.unhide_listing(user_id, listing_id)
    return jsonify({"hidden": False})
