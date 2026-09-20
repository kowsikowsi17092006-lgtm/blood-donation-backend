import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, messaging

from flask import Flask, request, jsonify
from flask_cors import CORS

import mysql.connector


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# FIREBASE ADMIN SDK
# =========================================================
import os
import json
import firebase_admin
from firebase_admin import credentials

firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

if firebase_json and not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_json))
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
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
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

        print("REGISTER DONOR ERROR:", e)

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

        request_id = cursor.lastrowid

        cursor.close()

        return jsonify({
            "success": True,
            "message": "Blood request submitted successfully",
            "request_id": request_id
        }), 201

    except Exception as e:

        print("BLOOD REQUEST ERROR:", e)

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
        db.ping(reconnect=True, attempts=3, delay=2)

        blood_group = request.args.get("blood_group")

        cursor = db.cursor(dictionary=True)

        sql = """
        SELECT
            id,
            name,
            age,
            blood_group,
            phone,
            location,
            trust_score
        FROM donors
        WHERE LOWER(blood_group) = LOWER(%s)
        """

        cursor.execute(sql, (blood_group,))

        donors = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "donors": donors
        }), 200

    except Exception as e:

        print("SEARCH DONORS ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route("/recommend-donors", methods=["GET"])
def recommend_donors():

    try:
        db.ping(reconnect=True, attempts=3, delay=2)

        blood_group = request.args.get("blood_group")
        location = request.args.get("location")

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
                WHEN LOWER(location) = LOWER(%s) THEN 100
                ELSE 50
            END AS recommendation_score
        FROM donors
        WHERE LOWER(blood_group) = LOWER(%s)
        ORDER BY recommendation_score DESC, trust_score DESC
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

        print("RECOMMENDATION ERROR:", e)

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

        cursor = db.cursor()

        sql = """
        SELECT COUNT(*)
        FROM blood_requests
        WHERE blood_group = %s
        """

        cursor.execute(sql, (blood_group,))

        count = cursor.fetchone()[0]

        cursor.close()

        if count >= 10:
            demand = "High"
        elif count >= 5:
            demand = "Medium"
        else:
            demand = "Low"

        return jsonify({
            "success": True,
            "blood_group": blood_group,
            "request_count": count,
            "demand": demand
        }), 200

    except Exception as e:

        print("DEMAND PREDICTION ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 6. BLOOD REQUESTS - HOSPITAL DASHBOARD
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

        requests_data = cursor.fetchall()

        cursor.close()

        return jsonify({
            "success": True,
            "requests": requests_data
        }), 200

    except Exception as e:

        print("BLOOD REQUESTS ERROR:", e)

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
            COUNT(*) AS available_donors
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

        print("BLOOD BANK DASHBOARD ERROR:", e)

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

        cursor = db.cursor()

        sql = """
        UPDATE donors
        SET fcm_token = %s
        WHERE id = %s
        """

        cursor.execute(
            sql,
            (fcm_token, donor_id)
        )

        db.commit()

        cursor.close()

        return jsonify({
            "success": True,
            "message": "FCM token saved successfully"
        }), 200

    except Exception as e:

        print("FCM TOKEN ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# 9. EMERGENCY BLOOD ALERT
# =========================================================

@app.route("/emergency-alert", methods=["POST"])
def emergency_alert():

    try:
        data = request.get_json()

        patient_name = data.get("patient_name")
        blood_group = data.get("blood_group")
        hospital_name = data.get("hospital_name")
        contact_number = data.get("contact_number")

        cursor = db.cursor(dictionary=True)

        # Save emergency blood request
        insert_sql = """
        INSERT INTO blood_requests
        (patient_name, blood_group, hospital_name, contact_number)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            insert_sql,
            (
                patient_name,
                blood_group,
                hospital_name,
                contact_number
            )
        )

        db.commit()

        # Find donors with FCM tokens
        cursor.execute("""
        SELECT fcm_token
        FROM donors
        WHERE blood_group = %s
        AND fcm_token IS NOT NULL
        AND fcm_token != ''
        """, (blood_group,))

        donors = cursor.fetchall()

        cursor.close()

        tokens = [
            donor["fcm_token"]
            for donor in donors
        ]

        sent_count = 0

        if tokens:

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title="Emergency Blood Request",
                    body=f"Urgent {blood_group} blood needed at {hospital_name}"
                ),
                tokens=tokens
            )

            response = messaging.send_each_for_multicast(message)

            sent_count = response.success_count

        return jsonify({
            "success": True,
            "message": "Emergency alert sent successfully",
            "alerts_sent": sent_count
        }), 200

    except Exception as e:

        print("EMERGENCY ALERT ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# START FLASK SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )