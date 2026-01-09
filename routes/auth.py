from flask import Blueprint, request, jsonify, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from routes.db import get_db
import mysql.connector

auth_bp = Blueprint("auth", __name__)

# -----------------------------
# LOGIN
# -----------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template("login.html", error="Missing credentials")

    email = email.strip().lower()

    # ---------------- ADMIN LOGIN (TEMP) ----------------
    if email == "admin@civicconnect.com" and password == "admin123":
        session.clear()
        session.permanent = True
        session["user_role"] = "admin"
        session["email"] = email
        return redirect("/admin-dashboard")

    # ---------------- USER LOGIN ----------------
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )
    user = cursor.fetchone()

    cursor.close()
    db.close()

    if not user:
        return render_template("login.html", error="Invalid credentials")

    # ---------------- PASSWORD CHECK ----------------
    if not check_password_hash(user["password"], password):
        return render_template("login.html", error="Invalid credentials")

    # ---------------- STATUS CHECK ----------------
    if user["status"] != "active":
        return render_template(
            "login.html",
            error="Account pending approval or blocked"
        )

    # ---------------- SESSION ----------------
    session.clear()
    session.permanent = True

    session["user_id"] = user["id"]
    session["user_role"] = user["role"]
    session["user_name"] = user["name"]
    session["email"] = user["email"]

    # Optional role-based data
    if user["role"] == "citizen":
        session["pincode"] = user["pincode"]
        return redirect("/user-dashboard")

    if user["role"] == "officer":
        session["department"] = user["department"]
        return redirect("/officer-dashboard")

    return render_template("login.html", error="Login failed")


# -----------------------------
# SIGNUP
# -----------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    role = request.form.get("role")
    password = request.form.get("password")
    pincode = request.form.get("pincode")          # citizen only
    department = request.form.get("department")    # officer only

    # ---------------- BASIC VALIDATION ----------------
    if not name or not email or not phone or not password:
        return jsonify(success=False, message="Missing required fields"), 400

    email = email.strip().lower()

    if len(password) < 6:
        return jsonify(success=False, message="Password too short"), 400

    if role not in ["citizen", "officer"]:
        return jsonify(success=False, message="Invalid role"), 400

    if role == "citizen" and not pincode:
        return jsonify(
            success=False,
            message="Pincode required for citizens"
        ), 400

    if role == "officer" and not department:
        return jsonify(
            success=False,
            message="Department required for officers"
        ), 400

    # Officer status logic
    status = "pending" if role == "officer" else "active"

    # ---------------- DB CONNECTION ----------------
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="mca"
    )
    cursor = conn.cursor(dictionary=True)

    try:
        # ---------------- DUPLICATE EMAIL CHECK ----------------
        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )
        if cursor.fetchone():
            return jsonify(
                success=False,
                message="Email already exists"
            ), 409

        # ---------------- PASSWORD HASH ----------------
        hashed_password = generate_password_hash(password)

        # ---------------- INSERT USER ----------------
        cursor.execute(
            """
            INSERT INTO users
            (name, email, phone, password, role, pincode, department, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                name,
                email,
                phone,
                hashed_password,
                role,
                pincode if role == "citizen" else None,
                department if role == "officer" else None,
                status
            )
        )
        conn.commit()
        user_id = cursor.lastrowid

    finally:
        cursor.close()
        conn.close()

    # ---------------- SESSION ----------------
    # Only auto-login active users
    if status == "active":
        session["user_id"] = user_id
        session["email"] = email
        session["user_role"] = role
        session["user_name"] = name

        if role == "citizen":
            session["pincode"] = pincode
        else:
            session["department"] = department

        return jsonify(success=True)

    # Officer pending approval
    return jsonify(
        success=True,
        message="Signup successful. Officer account pending admin approval."
    )


# -----------------------------
# LOGOUT
# -----------------------------

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
