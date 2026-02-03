from flask import Blueprint, request, jsonify
from auth_utils import admin_required
from routes.db import get_db
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

# -----------------------------
# Admin Pending / Approve / Reject
# -----------------------------

@admin_bp.route("/officers/pending")
@admin_required
def get_pending_officers():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, name, email, department
        FROM users
        WHERE role='officer' AND status='pending'
    """)

    officers = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(officers)


@admin_bp.route("/approve-officer", methods=["POST"])
@admin_required
def approve_officer():
    officer_id = request.form.get("officer_id")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET status='active'
        WHERE id=%s AND role='officer'
    """, (officer_id,))

    db.commit()
    cur.close()
    db.close()

    return jsonify(success=True)


@admin_bp.route("/reject-officer", methods=["POST"])
@admin_required
def reject_officer():
    officer_id = request.form.get("officer_id")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET status='blocked'
        WHERE id=%s AND role='officer'
    """, (officer_id,))

    db.commit()
    cur.close()
    db.close()

    return jsonify(success=True)


@admin_bp.route("/officers/blocked")
@admin_required
def get_blocked_officers():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, name, email, department
        FROM users
        WHERE role='officer' AND status='blocked'
    """)

    officers = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(officers)


@admin_bp.route("/reactivate-officer", methods=["POST"])
@admin_required
def reactivate_officer():
    officer_id = request.form.get("officer_id")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET status='active'
        WHERE id=%s AND role='officer'
    """, (officer_id,))

    db.commit()
    cur.close()
    db.close()

    return jsonify(success=True)


@admin_bp.route("/issues/all")
@admin_required
def get_all_issues():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            issue_id,
            detected_issue,
            status,
            location_text,
            created_at,
            citizen_name,
            citizen_email
        FROM issues
        ORDER BY created_at DESC
    """)

    issues = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(issues)


@admin_bp.route("/issues/<issue_type>")
@admin_required
def get_issues_by_type(issue_type):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    if issue_type == "all":
        cur.execute("""
            SELECT
                issue_id,
                detected_issue,
                status,
                location_text,
                created_at
            FROM issues
            ORDER BY created_at DESC
        """)
    else:
        cur.execute("""
            SELECT
                issue_id,
                detected_issue,
                status,
                location_text,
                created_at
            FROM issues
            WHERE detected_issue=%s
            ORDER BY created_at DESC
        """, (issue_type,))

    issues = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(issues)


@admin_bp.route("/issue/<int:issue_id>")
@admin_required
def admin_issue_details(issue_id):
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            i.issue_id,
            i.detected_issue,
            i.status,
            i.description,
            i.location_text,
            i.created_at,
            i.image1_path,
            i.assigned_department,
            i.citizen_name,
            i.citizen_email,
            u.phone AS citizen_phone,
            i.confidence,
            i.severity_score
        FROM issues i
        LEFT JOIN users u
            ON i.citizen_email = u.email
        WHERE i.issue_id = %s
    """, (issue_id,))

    issue = cur.fetchone()
    cur.close()
    db.close()

    if not issue:
        return jsonify({"error": "Complaint not found"}), 404

    return jsonify(issue)


@admin_bp.route("/officers/all")
@admin_required
def get_all_officers():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, name, email, department, status
        FROM users
        WHERE role='officer'
        ORDER BY id DESC
    """)

    officers = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(officers)


@admin_bp.route("/block-officer", methods=["POST"])
@admin_required
def block_officer():
    officer_id = request.form.get("officer_id")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET status='blocked'
        WHERE id=%s AND role='officer'
    """, (officer_id,))

    db.commit()
    cur.close()
    db.close()

    return jsonify(success=True)


@admin_bp.route("/users/all")
@admin_required
def get_all_users():
    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, name, email, phone, pincode, status
        FROM users
        WHERE role='citizen'
        ORDER BY id DESC
    """)

    users = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(users)


@admin_bp.route("/block-user", methods=["POST"])
@admin_required
def block_user():
    user_id = request.form.get("user_id")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET status='blocked'
        WHERE id=%s AND role='citizen'
    """, (user_id,))

    db.commit()
    cur.close()
    db.close()

    return jsonify(success=True)


@admin_bp.route("/reactivate-user", methods=["POST"])
@admin_required
def reactivate_user():
    user_id = request.form.get("user_id")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE users
        SET status='active'
        WHERE id=%s AND role='citizen'
    """, (user_id,))

    db.commit()
    cur.close()
    db.close()

    return jsonify(success=True)


@admin_bp.route("/officers/search")
@admin_required
def search_officers():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "all")

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    sql = """
        SELECT id, name, email, department, status
        FROM users
        WHERE role='officer'
    """
    params = []

    if status != "all":
        sql += " AND status=%s"
        params.append(status)

    if q:
        sql += " AND (name ILIKE %s OR email ILIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    sql += " ORDER BY id DESC"

    cur.execute(sql, params)
    officers = cur.fetchall()

    cur.close()
    db.close()

    return jsonify(officers)


@admin_bp.route("/users/search")
@admin_required
def search_users():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "all")

    db = get_db()
    cur = db.cursor(cursor_factory=RealDictCursor)

    sql = """
        SELECT id, name, email, phone, pincode, status
        FROM users
        WHERE role='citizen'
    """
    params = []

    if status != "all":
        sql += " AND status=%s"
        params.append(status)

    if q:
        sql += " AND (name ILIKE %s OR email ILIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    sql += " ORDER BY id DESC"

    cur.execute(sql, params)
    users = cur.fetchall()

    cur.close()
    db.close()

    return jsonify(users)

# =============================
# ISSUE COUNT ROUTES
# =============================

@admin_bp.route("/count/garbage")
def count_garbage_issues():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM issues
        WHERE detected_issue = 'garbage'
    """)

    count = cur.fetchone()[0]

    cur.close()
    db.close()

    return jsonify({"count": count})


@admin_bp.route("/count/pothole")
def count_pothole_issues():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM issues
        WHERE detected_issue = 'pothole'
    """)

    count = cur.fetchone()[0]

    cur.close()
    db.close()

    return jsonify({"count": count})


@admin_bp.route("/count/general")
def count_general():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM issues
        WHERE detected_issue = 'general'
    """)

    count = cur.fetchone()[0]

    cur.close()
    db.close()

    return jsonify({"count": count})


from flask import session, redirect, url_for

@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return "", 204
