from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from api.services import authenticate_user, register_user

bp = Blueprint("auth", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
        else:
            user = authenticate_user(email, password)
            if user:
                session["user_id"] = user["User_Id"]
                session["user_name"] = user["Name"]
                return redirect(url_for("dashboard.dashboard"))
            else:
                flash("Invalid email or password.", "error")

    return render_template("auth/login.html", title="Sign In")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Name, email, and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            try:
                user = register_user(name, email, password)
                session["user_id"] = user["User_Id"]
                session["user_name"] = user["Name"]
                flash("Account created! Welcome to TeamFreak.", "success")
                return redirect(url_for("dashboard.dashboard"))
            except ValueError as exc:
                flash(str(exc), "error")

    return render_template("auth/register.html", title="Create Account")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
