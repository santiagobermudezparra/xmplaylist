"""XM Spotify Sync Frontend."""

import os
import requests
from flask import Flask, render_template, jsonify

API_URL = os.getenv("API_URL", "http://localhost:22112")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "22111"))

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", api_url=API_URL)


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/status")
def api_status():
    try:
        response = requests.get(f"{API_URL}/api/v1/status", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/sync", methods=["POST"])
def api_sync():
    try:
        response = requests.post(f"{API_URL}/api/v1/sync", timeout=60)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/tracks")
def api_tracks():
    try:
        response = requests.get(f"{API_URL}/api/v1/tracks", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503


def main():
    app.run(host="0.0.0.0", port=FRONTEND_PORT)


if __name__ == "__main__":
    main()
