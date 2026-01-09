from functools import wraps
from flask import session, redirect, jsonify, request

def citizen_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_role") != "citizen":
            return redirect("/login-page")
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_role") != "admin":
            return redirect("/login-page")
        return f(*args, **kwargs)
    return wrapper



from functools import wraps
from flask import session, redirect, request, jsonify

def officer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print("DEBUG user_role =", session.get("user_role"))
        print("DEBUG session =", dict(session))

        if session.get("user_role") != "officer":
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Unauthorized"}), 401
            return redirect("/login-page")

        return f(*args, **kwargs)
    return wrapper


