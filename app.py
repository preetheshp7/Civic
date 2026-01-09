from datetime import timedelta

from flask import Flask, render_template, redirect, session
from flask_cors import CORS
from auth_utils import admin_required

# -----------------------------
# CREATE APP (FIRST!)
# -----------------------------
app = Flask(__name__, template_folder="templates")
CORS(app, supports_credentials=True)

# -----------------------------
# CONFIG
# -----------------------------
app.secret_key = "civicconnect_secret_2025_DO_NOT_CHANGE"
app.config["GOOGLE_MAPS_KEY"] = "AIzaSyBRnVFGIftMgZYJMph25qJmExTkWxQMmsg"
app.config.update(
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=6),
    SESSION_COOKIE_SECURE=False,   # True only for HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=5 * 1024 * 1024
)

# -----------------------------
# HOME / STATIC PAGES
# -----------------------------
@app.route("/")
@app.route("/home-page")
def home():
    return render_template("home.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/signup-page")
def signup_page():
    return render_template("signup.html")

@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/nearbyissue")
def nearby_page():
    return render_template("nearbyissue.html")

# -----------------------------
# DASHBOARDS
# -----------------------------
@app.route("/user-dashboard")
def user_dashboard():
    if session.get("user_role") != "citizen":
        return redirect("/login-page")
    return render_template("userdashboard.html")

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    return render_template("admindashboard.html")

@app.route("/officer-dashboard")
def officer_dashboard():
    if session.get("user_role") != "officer":
        return redirect("/login-page")
    return render_template("officerdashboard.html")

# -----------------------------
# REGISTER BLUEPRINTS (LAST)
# -----------------------------
from routes.admin_routes import admin_bp
from routes.user_routes import user_bp
from routes.officer_routes import officer_bp
from routes.auth import auth_bp
from services.ml_model import ml_bp
from routes.nearbyissues import issues_bp



app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(officer_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(issues_bp)
# ------------------------P-----
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)