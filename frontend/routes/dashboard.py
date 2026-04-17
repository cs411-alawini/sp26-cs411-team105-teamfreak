from flask import Blueprint, flash, render_template, url_for
from mysql.connector import Error

from api.config import MAIN_TABS
from api.queries import get_dashboard_circles

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def dashboard():
    try:
        circles = get_dashboard_circles()
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
