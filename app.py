import firebase_admin
from firebase_admin import credentials, messaging

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector


# =========================================================
# FIREBASE ADMIN SDK
# =========================================================

cred = credentials.Certificate(
    "ai-blood-donation-app-firebase-adminsdk-fbsvc-06745d2c73.json"
)

firebase_admin.initialize_app(cred)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# MYSQL DATABASE CONNECTION
# =========================================================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="kowzy@17092006",
    database="blood_donation"
)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return jsonify({
        "message": "Blood Donation API is running"
    })


# =========================================================
# 1. DONOR REGISTRATION
# =========================================================

@app.route("/register-donor", methods=["POST"])
def register_donor():
    try:
        data = request.get_json()

        name = data.get("name")
        age = data.get("age")
        blood_group = data.get("blood_group")
        phone = data.get("phone")
        location = data.get("location")

        cursor = db.cursor()

        sql = """
        INSERT INTO donors
        (name, age, blood_group, phone, location)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            name,
            age,
            blood_group,
            phone,
            location
        )

        cursor.execute(sql, values)
        db.commit()

        donor_id = cursor.lastrowid

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Donor registered successfully",
            "donor_id": donor_id
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 2. BLOOD REQUEST
# =========================================================

@app.route("/request-blood", methods=["POST"])
def request_blood():
    try:
        data = request.get_json()

        patient_name = data.get("patient_name")
        blood_group = data.get("blood_group")
        hospital_name = data.get("hospital_name")
        contact_number = data.get("contact_number")

        cursor = db.cursor()

        sql = """
        INSERT INTO blood_requests
        (patient_name, blood_group, hospital_name, contact_number)
        VALUES (%s, %s, %s, %s)
        """

        values = (
            patient_name,
            blood_group,
            hospital_name,
            contact_number
        )

        cursor.execute(sql, values)
        db.commit()
        cursor.close()

        return jsonify({
            "success": True,
            "message": "Blood request submitted successfully"
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 3. SEARCH DONORS
# =========================================================

@app.route("/search-donors", methods=["GET"])
def search_donors():
    try:
        blood_group = request.args.get("blood_group")

        if not blood_group:
            return jsonify({
                "success": False,
                "message": "Blood group is required"
            }), 400

        cursor = db.cursor(dictionary=True)

        sql = """
        SELECT
            id,
            name,
            age,
            blood_group,
            phone,
            location
        FROM donors
        WHERE blood_group = %s
        """

        cursor.execute(sql, (blood_group,))

        donors = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "donors": donors
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 4. SMART DONOR RECOMMENDATION
# =========================================================

@app.route("/recommend-donors", methods=["GET"])
def recommend_donors():
    try:
        blood_group = request.args.get("blood_group")
        location = request.args.get("location", "")

        if not blood_group:
            return jsonify({
                "success": False,
                "message": "Blood group is required"
            }), 400

        cursor = db.cursor(dictionary=True)

        sql = """
        SELECT
            id,
            name,
            age,
            blood_group,
            phone,
            location,
            trust_score,

            CASE
                WHEN LOWER(location) = LOWER(%s)
                THEN 100
                ELSE 50
            END AS recommendation_score

        FROM donors

        WHERE blood_group = %s

        ORDER BY
            recommendation_score DESC,
            age ASC

        LIMIT 5
        """

        cursor.execute(
            sql,
            (location, blood_group)
        )

        donors = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "donors": donors
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 5. BLOOD DEMAND PREDICTION
# =========================================================

@app.route("/predict-demand", methods=["GET"])
def predict_demand():
    try:
        blood_group = request.args.get("blood_group")

        if not blood_group:
            return jsonify({
                "success": False,
                "message": "Blood group is required"
            }), 400

        cursor = db.cursor(dictionary=True)

        sql = """
        SELECT COUNT(*) AS total_requests
        FROM blood_requests
        WHERE blood_group = %s
        """

        cursor.execute(
            sql,
            (blood_group,)
        )

        result = cursor.fetchone()

        cursor.close()

        total_requests = result["total_requests"]

        if total_requests >= 10:
            demand = "High"
        elif total_requests >= 5:
            demand = "Medium"
        else:
            demand = "Low"

        return jsonify({
            "success": True,
            "blood_group": blood_group,
            "total_requests": total_requests,
            "predicted_demand": demand
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 6. BLOOD REQUESTS
# =========================================================

@app.route("/blood-requests", methods=["GET"])
def blood_requests():
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                patient_name,
                blood_group,
                hospital_name,
                contact_number,
                created_at
            FROM blood_requests
            ORDER BY created_at DESC
        """)

        requests = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success": True,
            "requests": requests
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 7. BLOOD BANK DASHBOARD
# =========================================================

@app.route("/blood-bank-dashboard", methods=["GET"])
def blood_bank_dashboard():
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                blood_group,
                COUNT(*) AS donor_count
            FROM donors
            GROUP BY blood_group
            ORDER BY blood_group
        """)

        data = cursor.fetchall()
        cursor.close()

        return jsonify({
            "success": True,
            "blood_stock": data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 8. SAVE FCM TOKEN
# =========================================================

@app.route("/save-fcm-token", methods=["POST"])
def save_fcm_token():
    try:
        data = request.get_json()

        donor_id = data.get("donor_id")
        fcm_token = data.get("fcm_token")

        if not donor_id or not fcm_token:
            return jsonify({
                "success": False,
                "message": "Donor ID and FCM token are required"
            }), 400

        cursor = db.cursor()

        sql = """
        UPDATE donors
        SET fcm_token = %s
        WHERE id = %s
        """

        cursor.execute(sql, (fcm_token, donor_id))
        db.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "FCM token saved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 9. EMERGENCY BLOOD ALERT + FCM NOTIFICATION
# =========================================================

@app.route("/emergency-alert", methods=["POST"])
def emergency_alert():
    try:
        data = request.get_json()

        patient_name = data.get("patient_name")
        blood_group = data.get("blood_group")
        hospital_name = data.get("hospital_name")
        contact_number = data.get("contact_number")

        if not patient_name or not blood_group or not hospital_name or not contact_number:
            return jsonify({
                "success": False,
                "message": "All fields are required"
            }), 400

        # -------------------------------------------------
        # Save emergency request
        # -------------------------------------------------

        cursor = db.cursor()

        sql = """
        INSERT INTO blood_requests
        (patient_name, blood_group, hospital_name, contact_number)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (
            patient_name,
            blood_group,
            hospital_name,
            contact_number
        ))

        db.commit()
        cursor.close()

        # -------------------------------------------------
        # Find matching donors with FCM tokens
        # -------------------------------------------------

        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT fcm_token
            FROM donors
            WHERE blood_group = %s
              AND fcm_token IS NOT NULL
              AND fcm_token <> ''
        """, (blood_group,))

        donor_rows = cursor.fetchall()
        cursor.close()

        tokens = [
            row["fcm_token"]
            for row in donor_rows
            if row.get("fcm_token")
        ]

        notifications_sent = 0
        notifications_failed = 0

        # -------------------------------------------------
        # Send FCM notification
        # -------------------------------------------------

        if tokens:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title="🚨 Emergency Blood Alert",
                    body=(
                        f"Urgent {blood_group} blood required at "
                        f"{hospital_name} for {patient_name}. "
                        f"Please respond if you can donate."
                    )
                ),
                data={
                    "type": "emergency_blood_alert",
                    "patient_name": str(patient_name),
                    "blood_group": str(blood_group),
                    "hospital_name": str(hospital_name),
                    "contact_number": str(contact_number)
                },
                tokens=tokens
            )

            response = messaging.send_each_for_multicast(message)

            notifications_sent = response.success_count
            notifications_failed = response.failure_count

            print("Notifications sent:", response.success_count)
            print("Notifications failed:", response.failure_count)

        return jsonify({
            "success": True,
            "message": "Emergency blood alert sent successfully",
            "matching_donors": len(tokens),
            "notifications_sent": notifications_sent,
            "notifications_failed": notifications_failed
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# RUN FLASK SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
