from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 🔥 Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================
# CREDIT RULE ENGINE
# ==========================
def calculate_credits(waste_type, confidence):

    if confidence < 0.85:
        return 0, "Low confidence detection"

    rules = {
        "Organic": 10,
        "Recyclable": 15,
        "Plastic": 5,
        "Non-Recyclable": -5
    }

    return rules.get(waste_type, 0), "Processed"


# ==========================
# RECEIVE DETECTION
# ==========================
@app.route("/dispose", methods=["POST"])
def dispose():

    data = request.json

    if not data:
        return jsonify({"error": "No data"}), 400

    user_id = data.get("userId")
    waste_type = data.get("wasteType")
    confidence = float(data.get("confidence", 0))

    if not user_id or not waste_type:
        return jsonify({"error": "Missing fields"}), 400

    credits, message = calculate_credits(waste_type, confidence)

    user_ref = db.collection("users").document(user_id)

    # Use transaction to avoid multiple reads
    @firestore.transactional
    def update_user(transaction, user_ref):
        snapshot = user_ref.get(transaction=transaction)

        if snapshot.exists:
            current_credits = snapshot.to_dict().get("credits", 0)
        else:
            current_credits = 0
            transaction.set(user_ref, {
                "name": user_id,   # 👈 show roll number as name
                "rollNumber": user_id,
                "credits": 0,
                "badge": "Bronze",
                "createdAt": firestore.SERVER_TIMESTAMP
            })
        new_credits = current_credits + credits

        # Badge logic
        if new_credits >= 500:
            badge = "Gold"
        elif new_credits >= 200:
            badge = "Silver"
        else:
            badge = "Bronze"

        transaction.update(user_ref, {
            "credits": new_credits,
            "badge": badge
        })

        return new_credits, badge

    transaction = db.transaction()
    current_credits, badge = update_user(transaction, user_ref)

    # Log waste (separate, fast)
    db.collection("waste_logs").add({
        "userId": user_id,
        "wasteType": waste_type,
        "confidence": confidence,
        "creditsEarned": credits,
        "dateTime": firestore.SERVER_TIMESTAMP
    })

    return jsonify({
        "status": "ok",
        "creditsAdded": credits,
        "currentCredits": current_credits,
        "badge": badge
    })


# ==========================
# STATS
# ==========================
@app.route("/stats")
def stats():

    logs = db.collection("waste_logs").stream()
    stats_data = {}

    for doc in logs:
        wt = doc.to_dict().get("wasteType")
        stats_data[wt] = stats_data.get(wt, 0) + 1

    return jsonify(stats_data)


# ==========================
# ANALYTICS
# ==========================
@app.route("/analytics")
def analytics():

    logs = db.collection("waste_logs").stream()

    total = 0
    today_count = 0
    daily_counts = {}

    today_str = datetime.now().strftime("%Y-%m-%d")

    for doc in logs:
        data = doc.to_dict()
        total += 1

        timestamp = data.get("dateTime")
        if timestamp:
            date_str = timestamp.strftime("%Y-%m-%d")

            if date_str == today_str:
                today_count += 1

            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

    return jsonify({
        "totalWaste": total,
        "todayWaste": today_count,
        "dailyData": daily_counts
    })


# ==========================
# TOP USERS
# ==========================
@app.route("/top-users")
def top_users():

    users = db.collection("users") \
        .order_by("credits", direction=firestore.Query.DESCENDING) \
        .limit(5) \
        .stream()

    result = []

    for doc in users:
        data = doc.to_dict()
        result.append({
            "userId": doc.id,
            "credits": data.get("credits", 0),
            "badge": data.get("badge", "Bronze")
        })

    return jsonify(result)


# ==========================
# GET USER
# ==========================
@app.route("/user/<user_id>")
def get_user(user_id):

    doc = db.collection("users").document(user_id).get()

    if doc.exists:
        data = doc.to_dict()
        return jsonify({
            "name": data.get("name", user_id),
            "rollNumber": data.get("rollNumber", user_id),
            "credits": data.get("credits", 0)
        })

    return jsonify({
        "name": user_id,
        "rollNumber": user_id,
        "credits": 0
    })


# ==========================
@app.route("/dashboard")
def dashboard():
    return send_from_directory("static", "dashboard.html")


@app.route("/")
def home():
    return "♻️ Waste Segregation Backend Running"

@app.route("/test")
def test():
    return jsonify({"status": "server ok"})
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)