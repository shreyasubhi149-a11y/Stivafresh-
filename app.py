from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import re
import json
from pywebpush import webpush, WebPushException
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


# =========================
# WEB PUSH CONFIGURATION
# =========================
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "private_key.pem")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:stivafresh@example.com")


def send_push(subscription, title, message):
    """Send one Web Push notification using the server-side VAPID private key."""
    try:
        webpush(
            subscription_info=subscription,
            data=message,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
        )
        return True
    except WebPushException as error:
        print("Web Push failed:", error)
        return False



# =========================
# DATABASE CONNECTION
# =========================

def get_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stivafresh.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE DATABASE TABLE
# =========================

def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT UNIQUE NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS groceries (
            id INTEGER PRIMARY KEY,
            name TEXT,
            quantity TEXT,
            type TEXT,
            purchaseDate TEXT,
            storage TEXT,
            temperature REAL,
            expiryDate TEXT,
            reminderDays INTEGER
        )
    """)


    conn.commit()
    conn.close()


create_table()


# =========================
# HOME PAGE
# =========================
@app.route("/service-worker.js")
def service_worker():
    return app.send_static_file("service-worker.js")
@app.route("/")
def home():
    return render_template("stivafresh.html")
@app.route("/stivafresh.html")
def stivafresh_page():
    return render_template("stivafresh.html")


# =========================
# OPTIONAL VISION-AI GROCERY SCAN
# =========================
@app.route("/api/scan-grocery", methods=["POST"])
def scan_grocery_with_vision():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return {"error": "Vision AI is not configured; use the browser OCR fallback."}, 503

    payload = request.get_json(silent=True) or {}
    image_data = payload.get("image", "")
    if not isinstance(image_data, str) or not image_data.startswith("data:image/") or "," not in image_data:
        return {"error": "Please provide a valid grocery image."}, 400
    if len(image_data) > 7_000_000:
        return {"error": "Image is too large. Please choose a smaller photo."}, 413
    if not re.match(r"^data:image/(png|jpeg|jpg|webp);base64,", image_data, re.I):
        return {"error": "Use a PNG, JPEG, or WEBP image."}, 400

    prompt = """You are the grocery-label assistant inside STIVA. Inspect this photo and return ONLY a JSON object with these keys: name, quantity, type, expiry_date, storage, confidence, note.
Rules:
- Identify the grocery item if visible. If you cannot identify it confidently, use an empty string for name.
- quantity may be filled only when visibly stated on packaging; otherwise use an empty string.
- type must be exactly 'Packed' for packaged products or 'Fresh' for loose produce; if uncertain use an empty string.
- expiry_date must be YYYY-MM-DD ONLY if a full, explicit expiry/use-by/best-before date is visibly printed and legible. Otherwise use an empty string. Never invent an expiry date, infer it from the item's appearance, or calculate from a manufacturing date / 'X months from manufacture'.
- storage must be 'Refrigerator', 'Room Temperature', or an empty string. Only fill it if clearly supported by the label or obvious product guidance.
- confidence must be a number between 0 and 1 reflecting your confidence in the item identification.
- note should be a short uncertainty warning when needed.
- Do not confuse manufacturing/packed-on dates with expiry dates. The user will verify every result before saving."""
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.environ.get("STIVA_VISION_MODEL", "gpt-4.1-mini"),
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_data, "detail": "high"}
                ]
            }]
        )
        raw = (response.output_text or "").strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
        data = json.loads(raw)
        expiry = data.get("expiry_date", "")
        if not isinstance(expiry, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", expiry):
            expiry = ""
        name = data.get("name", "")
        quantity = data.get("quantity", "")
        item_type = data.get("type", "")
        storage = data.get("storage", "")
        return {
            "name": name[:80] if isinstance(name, str) else "",
            "quantity": quantity[:50] if isinstance(quantity, str) else "",
            "type": item_type if item_type in ("Fresh", "Packed") else "",
            "expiry_date": expiry,
            "storage": storage if storage in ("Refrigerator", "Room Temperature") else "",
            "confidence": data.get("confidence", 0),
            "note": str(data.get("note", ""))[:240]
        }
    except Exception as error:
        app.logger.warning("Vision scan failed: %s", type(error).__name__)
        return {"error": "Vision scan failed. Try again or use label OCR."}, 502


# =========================
# PUBLIC VAPID KEY
# =========================
@app.route("/api/push/public-key", methods=["GET"])
def get_push_public_key():
    public_key = os.environ.get("VAPID_PUBLIC_KEY")
    if not public_key:
        return {"error": "VAPID_PUBLIC_KEY is not configured on the server."}, 503
    return {"publicKey": public_key}


# =========================
# WEB PUSH SUBSCRIPTION
# =========================
@app.route("/api/push/subscribe", methods=["POST"])
def subscribe_push():
    subscription = request.json or {}
    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys", {})

    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        return {"error": "Invalid push subscription"}, 400

    conn = get_db()
    conn.execute("""
        INSERT INTO push_subscriptions (endpoint, p256dh, auth)
        VALUES (?, ?, ?)
        ON CONFLICT(endpoint) DO UPDATE SET
            p256dh=excluded.p256dh, auth=excluded.auth
    """, (endpoint, keys["p256dh"], keys["auth"]))
    conn.commit()
    conn.close()
    return {"message": "Push subscription saved"}


@app.route("/api/push/test", methods=["POST"])
def test_push():
    payload = {"title": "STIVA", "body": "Push notifications are working!"}
    public_key = os.environ.get("VAPID_PUBLIC_KEY")
    private_key = os.environ.get("VAPID_PRIVATE_KEY")
    subject = os.environ.get("VAPID_SUBJECT", "mailto:stivafresh@example.com")

    if not public_key or not private_key:
        return {"error": "VAPID keys are not configured on the server"}, 503

    conn = get_db()
    rows = conn.execute("SELECT endpoint, p256dh, auth FROM push_subscriptions").fetchall()
    conn.close()

    sent = 0
    for row in rows:
        try:
            webpush(
                subscription_info={
                    "endpoint": row["endpoint"],
                    "keys": {"p256dh": row["p256dh"], "auth": row["auth"]}
                },
                data=jsonify(payload).get_data(as_text=True),
                vapid_private_key=private_key,
                vapid_claims={"sub": subject}
            )
            sent += 1
        except WebPushException as exc:
            print("Push failed:", exc)

    return {"message": "Push sent", "sent": sent}

# =========================
# GET ALL GROCERIES
# =========================

@app.route("/api/groceries", methods=["GET"])
def get_groceries():
    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM groceries"
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================
# ADD GROCERY
# =========================

@app.route("/api/groceries", methods=["POST"])
def add_grocery():
    grocery = request.json

    conn = get_db()

    conn.execute("""
        INSERT INTO groceries
        (id, name, quantity, type, purchaseDate, storage,
         temperature, expiryDate, reminderDays)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        grocery["id"],
        grocery["name"],
        grocery["quantity"],
        grocery["type"],
        grocery["purchaseDate"],
        grocery["storage"],
        grocery["temperature"],
        grocery["expiryDate"],
        grocery["reminderDays"]
    ))

    conn.commit()
    conn.close()

    return grocery


# =========================
# DELETE GROCERY
# =========================

@app.route("/api/groceries/<int:grocery_id>", methods=["DELETE"])
def delete_grocery(grocery_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM groceries WHERE id = ?",
        (grocery_id,)
    )

    conn.commit()
    conn.close()

    return {"message": "Grocery deleted successfully"}


# =========================
# TEST ROUTE
# =========================

@app.route("/api/test")
def test():
    return {"message": "STIVA backend is working!"}



# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
   app.run(host="127.0.0.1", port=8000, debug=False)
