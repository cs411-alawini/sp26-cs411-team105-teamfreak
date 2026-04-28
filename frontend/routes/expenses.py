from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error

from api.config import MAIN_TABS, SPLIT_TYPE_OPTIONS
from api.queries import fetch_lookup_data, get_circle_participant_choices, get_expense_detail_proc
from api.services import insert_expense
from routes.auth import login_required

bp = Blueprint("expenses", __name__)


@bp.route("/expenses/new", methods=["GET", "POST"])
@login_required
def new_expense():
    user_id = session["user_id"]
    try:
        circles, users = fetch_lookup_data(user_id)
        circle_participant_choices = get_circle_participant_choices(user_id)
    except Error as exc:
        circles, users = [], []
        circle_participant_choices = {}
        flash(f"Database error while loading expense form data: {exc}", "error")

    preselected_circle_id = request.args.get("circle_id", "")
    today_str = date.today().isoformat()

    if request.method == "POST":
        try:
            circle_id = insert_expense(request.form, user_id)
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


@bp.route("/expenses/<int:expense_id>/review")
@login_required
def expense_review(expense_id):
    try:
        expense, splits, payments = get_expense_detail_proc(expense_id)
    except Error as exc:
        flash(f"Database error loading expense: {exc}", "error")
        expense, splits, payments = None, [], []

    if not expense:
        flash("Expense not found.", "error")
        return redirect(url_for("dashboard.dashboard"))

    return render_template(
        "expenses/review.html",
        title=f"Expense #{expense_id} Review",
        expense=expense,
        splits=splits,
        payments=payments,
        active_main="dashboard",
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == "dashboard"), "Dashboard"),
        subtabs=[
            {"key": "back", "label": "Back to Circle", "href": url_for("circles.circle_detail", circle_id=expense["Circle_Id"])},
            {"key": "review", "label": "Expense Review", "href": url_for("expenses.expense_review", expense_id=expense_id)},
        ],
        active_subtab="review",
    )
