import os
import uuid
import math
import numpy as np
import tensorflow as tf
import piexif

from datetime import datetime, timedelta
from PIL import Image
from flask import Blueprint, request, jsonify, session

from auth_utils import citizen_required
from routes.db import get_db
from services.department_mapper import get_department
from utils.geo_utils import dms_to_decimal,get_distance_m
from utils.image_utils import save_image,allowed_file

user_bp = Blueprint("user", __name__)

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# -----------------------------
# USER DATA
# -----------------------------

@user_bp.route("/user/counts")
@citizen_required
def user_counts():
    citizen_email = session.get("email")
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(status='Pending') AS pending,
            SUM(status='In Progress') AS progress,
            SUM(status='Resolved') AS resolved
        FROM issues
        WHERE citizen_email=%s
    """, (citizen_email,))

    data = cur.fetchone()
    cur.close()
    db.close()

    return jsonify(data)


@user_bp.route("/user/issues")
@citizen_required
def user_issues():
    citizen_email = session.get("email")
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM issues
        WHERE citizen_email=%s
        ORDER BY created_at DESC
    """, (citizen_email,))

    issues = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(issues)


@user_bp.route("/user/issue/<int:issue_id>", methods=["GET"])
def get_single_issue(issue_id):
    citizen_email = session.get("email")
    if not citizen_email:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            issue_id,
            detected_issue,
            status,
            location_text,
            created_at,
            image1_path,
            image2_path
        FROM issues
        WHERE issue_id=%s AND citizen_email=%s
    """, (issue_id, citizen_email))

    issue = cur.fetchone()
    cur.close()
    db.close()

    if not issue:
        return jsonify({"error": "Complaint not found"}), 404

    return jsonify({
        "issue_id": issue["issue_id"],
        "detected_issue": issue["detected_issue"],
        "status": issue["status"],
        "location": issue["location_text"],   # ✅ rename
        "created_at": issue["created_at"],
        "image": issue["image1_path"]          # ✅ rename
    })


@user_bp.route("/user/issue/<int:issue_id>", methods=["DELETE"])
def delete_issue(issue_id):
    citizen_email = session.get("email")
    if not citizen_email:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT status
        FROM issues
        WHERE issue_id=%s AND citizen_email=%s
    """, (issue_id, citizen_email))

    row = cur.fetchone()

    if not row:
        cur.close()
        db.close()
        return jsonify({"error": "Complaint not found"}), 404

    if row[0] != "Pending":
        cur.close()
        db.close()
        return jsonify({
            "error": "Only pending complaints can be withdrawn"
        }), 400

    cur.execute("""
        DELETE FROM issues
        WHERE issue_id=%s AND citizen_email=%s
    """, (issue_id, citizen_email))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"message": "Complaint withdrawn successfully"})


# -----------------------------
# ML MODEL
# -----------------------------

# -----------------------------
# dummy
# -----------------------------
# @user_bp.route("/predict", methods=["POST"])
# def predict():
#     return jsonify({
#         "prediction": "garbage",
#         "confidence": 0.75,
#         "severity_score": 6.5
#     })




# -----------------------------
# HELPER FUNCTIONS (EXIF)
# -----------------------------




# -----------------------------
# REPORT ISSUE (FIXED)
# -----------------------------

@user_bp.route("/report-issue", methods=["POST"])
def report_issue():
    citizen_name = session.get("user_name")
    citizen_email = session.get("email")

    predicted_issue = request.form.get("predicted_issue")
    confidence = request.form.get("confidence")
    severity_score = request.form.get("severity_score")
    description = request.form.get("description")
    location = request.form.get("location")
    lat_raw = request.form.get("lat")
    lng_raw = request.form.get("lng")

    if not lat_raw or not lng_raw:
        return jsonify({"error": "Location missing"}), 400

    lat = float(lat_raw)
    lng = float(lng_raw)

    photo1 = request.files.get("photo_1")
    photo2 = request.files.get("photo_2")

    if photo1 and not allowed_file(photo1.filename):
        return jsonify({"error": "Invalid image type"}), 400

    if photo2 and not allowed_file(photo2.filename):
        return jsonify({"error": "Invalid image type"}), 400

    exif_verified = 0
    exif_reason = "EXIF missing or invalid"

    if photo1:
        try:
            img = Image.open(photo1)
            exif_dict = piexif.load(img.info.get("exif", b""))
            gps = exif_dict["GPS"]

            img_lat = dms_to_decimal(gps[2], gps[1].decode())
            img_lng = dms_to_decimal(gps[4], gps[3].decode())

            distance = get_distance_m(img_lat, img_lng, lat, lng)

            img_time_raw = exif_dict["Exif"].get(
                piexif.ExifIFD.DateTimeOriginal
            )
            if img_time_raw:
                img_time = datetime.strptime(
                    img_time_raw.decode(),
                    "%Y:%m:%d %H:%M:%S"
                )
                if (
                    distance <= 200
                    and datetime.now() - img_time <= timedelta(days=7)
                ):
                    exif_verified = 1
                    exif_reason = "Verified"
        except:
            pass

        photo1.seek(0)

    img1_path = save_image(photo1) if photo1 else None
    img2_path = save_image(photo2) if photo2 else None

    db = get_db()
    cur = db.cursor()
    dept = get_department(predicted_issue)
    cur.execute("""
        INSERT INTO issues
        (
            detected_issue,
            confidence,
            severity_score,
            description,
            location_text,
            latitude,
            longitude,
            image1_path,
            image2_path,
            citizen_name,
            citizen_email,
            assigned_department,
            exif_verified,
            exif_reason,
            status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        predicted_issue,
        confidence,
        severity_score,
        description,
        location,
        lat,
        lng,
        img1_path,
        img2_path,
        citizen_name,
        citizen_email,
        dept,
        exif_verified,
        exif_reason,
        "Pending"        # ✅ NOW MATCHES
    ))


    db.commit()
    issue_id = cur.lastrowid
    cur.close()
    db.close()

    assigned_to = {
        "department": dept,
        "officer": "Municipal Officer",
        "priority": "High" if float(severity_score) > 0.7 else "Normal"
    }

    return jsonify({
        "complaint_id": f"#CN-{issue_id}",
        "detected_issue": predicted_issue,
        "assigned_to": assigned_to
    })
