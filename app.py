# app.py
import json
import os
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify

app = Flask(__name__)
_scan_lock = threading.Lock()
RESULTS_FILE = "results.json"

def load_results() -> dict:
    if not os.path.exists(RESULTS_FILE):
        return {"listings": [], "last_scan": None, "next_scan": None, "total": 0, "new_count": 0}
    with open(RESULTS_FILE) as f:
        return json.load(f)

def save_results(listings: list[dict], new_count: int, next_scan_iso: str) -> None:
    data = {
        "listings": listings,
        "last_scan": datetime.now().isoformat(),
        "next_scan": next_scan_iso,
        "total": len(listings),
        "new_count": new_count,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def dashboard():
    return render_template("dashboard.html", **load_results())

@app.route("/api/results")
def api_results():
    return jsonify(load_results())

@app.route("/api/scan", methods=["POST"])
def scan_now():
    from scheduler import trigger_scan
    threading.Thread(target=trigger_scan, daemon=True).start()
    return jsonify({"status": "scan started"})
