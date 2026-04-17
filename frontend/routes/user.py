from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import Error

from api.config import MAIN_TABS
from api.queries import get_current_user, get_recent_payment_links, get_user_balance_summary
from api.services import update_user

bp = Blueprint("user", __name__)


@bp.route("/user", methods=["GET", "POST"])
def user_profile():
    if request.method == "POST":
        try:
            update_user(request.form)
        except (ValueError, Error) as exc:
            flash(f"Could not update user information: {exc}", "error")
        else:
            flash("User information updated successfully.", "success")
            return redirect(url_for("user.user_profile"))

    try:
        user = get_current_user()
        summary = get_user_balance_summary()
        owed_to_user = {"Owed_To_You": summary["Owed_To_You"]}
        recent_links = get_recent_payment_links()
    except Error as exc:
        flash(f"Database error while loading user page: {exc}", "error")
        user = None
        summary = {"Active_Circles": 0, "Total_You_Owe": 0, "Owed_To_You": 0}
        owed_to_user = {"Owed_To_You": 0}
        recent_links = []

    return render_template(
        "user/profile.html",
        title="User",
        user=user,
        summary=summary,
        owed_to_user=owed_to_user,
        recent_links=recent_links,
        active_main="user",
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == "user"), "User"),
    )
