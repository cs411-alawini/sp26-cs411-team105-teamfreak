from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import Error

from api.config import CURRENT_USER_ID, MAIN_TABS, SPLIT_TYPE_OPTIONS
from api.queries import fetch_lookup_data, get_circle_participant_choices
from api.services import insert_expense

bp = Blueprint("expenses", __name__)


@bp.route("/expenses/new", methods=["GET", "POST"])
def new_expense():
    try:
        circles, users = fetch_lookup_data()
        circle_participant_choices = get_circle_participant_choices()
    except Error as exc:
        circles, users = [], []
        circle_participant_choices = {}
        flash(f"Database error while loading expense form data: {exc}", "error")

    preselected_circle_id = request.args.get("circle_id", "")
    today_str = date.today().isoformat()

    if request.method == "POST":
        try:
            circle_id = insert_expense(request.form)
        except (ValueError, Error) as exc:
            flash(f"Could not create expense: {exc}", "error")
        else:
            flash("Expense added successfully.", "success")
            return redirect(url_for("circles.circle_detail", circle_id=circle_id))

    return render_template(
        "expenses/new.html",
        title="New Expense",
        circles=circles,
        users=users,
        preselected_circle_id=preselected_circle_id,
        circle_participant_choices=circle_participant_choices,
        today_str=today_str,
        split_type_options=SPLIT_TYPE_OPTIONS,
        active_main="new_expense",
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == "new_expense"), "New Expense"),
    )
