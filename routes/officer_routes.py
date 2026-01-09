from flask import Blueprint, jsonify, session, request
from auth_utils import officer_required
from routes.db import get_db

officer_bp = Blueprint(
    "officer",
    __name__,
    url_prefix="/officer"
)

# -----------------------------
# OFFICER ISSUES (MAIN DASHBOARD)
# -----------------------------
@officer_bp.route("/issues")
@officer_required
def officer_issues():
    dept = session.get("department")
    print("DEBUG session department =", dept)

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM issues")
    all_issues = cur.fetchall()
    print("DEBUG total issues in DB =", len(all_issues))

    cur.execute("""
        SELECT *
        FROM issues
        WHERE assigned_department = %s
    """, (dept,))
    filtered_issues = cur.fetchall()
    print("DEBUG matched issues =", len(filtered_issues))

    cur.close()
    db.close()

    return jsonify({
        "officer": {
            "department": dept,
            "name": session.get("name")
        },
        "issues": filtered_issues
    })


# -----------------------------
# SINGLE ISSUE DETAILS
# -----------------------------
@officer_bp.route("/issue/<int:issue_id>")
@officer_required
def officer_issue_details(issue_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT
            i.*,
            u.phone AS citizen_phone
        FROM issues i
        LEFT JOIN users u ON i.citizen_email = u.email
        WHERE i.issue_id = %s
    """, (issue_id,))

    issue = cur.fetchone()
    cur.close()
    db.close()

    if not issue:
        return jsonify({"error": "Issue not found"}), 404

    return jsonify(issue)

# -----------------------------
# UPDATE STATUS
# -----------------------------
@officer_bp.route("/update-status", methods=["POST"])
@officer_required
def update_status():
    issue_id = request.form.get("issue_id")
    status = request.form.get("status")

    if not issue_id or not status:
        return jsonify({"error": "Missing data"}), 400

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE issues
        SET status=%s
        WHERE issue_id=%s
    """, (status, issue_id))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"message": "Status updated"})


# -----------------------------
# PRIORITY POTHOLES
# -----------------------------
@officer_bp.route("/issues/priority")
@officer_required
def priority_issues():
    dept = session.get("department")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM issues
        WHERE assigned_department=%s
        ORDER BY severity_score DESC
    """, (dept,))

    issues = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(issues)


# -----------------------------
# POTHOLE GRAPH DATA
# -----------------------------
@officer_bp.route("/issues/monthly")
@officer_required
def monthly_issues():
    dept = session.get("department")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT issue_id, created_at
        FROM issues
        WHERE assigned_department=%s
    """, (dept,))

    issues = cur.fetchall()
    cur.close()
    db.close()

    return jsonify({ "issues": issues })

