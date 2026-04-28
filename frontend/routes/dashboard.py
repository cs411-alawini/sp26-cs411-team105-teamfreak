from flask import Blueprint, flash, render_template, session, url_for
from mysql.connector import Error

from api.config import MAIN_TABS
from api.queries import get_dashboard_circles
from routes.auth import login_required

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def dashboard():
    user_id = session["user_id"]
    try:
        circles = get_dashboard_circles(user_id)
    except Error as exc:
        flash(f"Database error while loading dashboard circles: {exc}", "error")
        circles = []

    return render_template(
        "dashboard.html",
        title="Dashboard",
        circles=circles,
        active_main="dashboard",
        hero_action={"href": url_for("circles.new_circle"), "label": "+ New Circle"},
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == "dashboard"), "Dashboard"),
    )
