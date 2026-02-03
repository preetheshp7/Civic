from flask import Blueprint, jsonify, request, send_from_directory, current_app
from routes.db import get_db
from psycopg2.extras import RealDictCursor
import os

issues_bp = Blueprint("issues", __name__)

# -----------------------------
# Serve uploaded images
# -----------------------------

@issues_bp.route("/uploads/<path:filename>")
def serve_uploaded_image(filename):
    upload_folder = os.path.join(current_app.root_path, "static", "uploads")
    return send_from_directory(upload_folder, filename)


# -----------------------------
# Nearby issues (TEMP: all)
# -----------------------------

@issues_bp.route("/issues/nearby", methods=["GET"])
def nearby_issues():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    # TEMP: return all issues
    cur.execute("""
        SELECT
            issue_id,
            detected_issue,
            description,
            location_text,
            status,
            created_at,
            image1_path
        FROM issues
        ORDER BY created_at DESC
    """)

    issues = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(issues)


# -----------------------------
# Get issue by ID
# -----------------------------

@issues_bp.route("/issue/<int:issue_id>", methods=["GET"])
def get_issue_by_id(issue_id):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            issue_id,
            detected_issue,
            description,
            location_text,
            status,
            created_at,
            image1_path,
            assigned_department
        FROM issues
        WHERE issue_id = %s
    """, (issue_id,))

    issue = cur.fetchone()
    cur.close()
    db.close()

    if not issue:
        return jsonify({"error": "Issue not found"}), 404

    return jsonify(issue)
