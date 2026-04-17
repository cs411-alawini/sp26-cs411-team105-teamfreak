from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import Error

from api.config import CURRENT_USER_ID, MAIN_TABS
from api.queries import (
    build_settlement_suggestions,
    fetch_lookup_data,
    get_circle_detail,
    get_you_owe_summary,
)
from api.services import insert_circle, insert_payment

bp = Blueprint("circles", __name__)


@bp.route("/circles/new", methods=["GET", "POST"])
def new_circle():
    try:
        _, users = fetch_lookup_data()
    except Error as exc:
        users = []
        flash(f"Database error while loading users: {exc}", "error")

    if request.method == "POST":
        try:
            circle_id = insert_circle(request.form)
        except (ValueError, Error) as exc:
            flash(f"Could not create circle: {exc}", "error")
        else:
            flash("Circle created successfully.", "success")
            return redirect(url_for("circles.circle_detail", circle_id=circle_id))

    return render_template(
        "circles/new.html",
        title="New Circle",
        users=users,
        active_main="dashboard",
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == "dashboard"), "Dashboard"),
    )


@bp.route("/circles/<int:circle_id>", methods=["GET", "POST"])
def circle_detail(circle_id):
    if request.method == "POST":
        try:
            insert_payment(circle_id, request.form)
        except (ValueError, Error) as exc:
            flash(f"Could not record payment: {exc}", "error")
        else:
            flash("Payment recorded and linked to the selected expense.", "success")
            return redirect(url_for("circles.circle_detail", circle_id=circle_id))

    try:
        detail = get_circle_detail(circle_id)
        owes_summary, eligible_expenses, raw_balances = get_you_owe_summary(circle_id)
        settlement_suggestions = build_settlement_suggestions(circle_id)
    except Error as exc:
        flash(f"Database error while loading circle detail: {exc}", "error")
        detail = None
        owes_summary, eligible_expenses, raw_balances, settlement_suggestions = [], [], [], []

    if not detail:
        flash("That circle could not be found.", "error")
        return redirect(url_for("dashboard.dashboard"))

    circle = detail["circle"]
    members = detail["members"]
    expenses = detail["expenses"]
    splits = detail["splits"]
    payments = detail["payments"]
    summary = detail["summary"]

    summary["Expense_Count"] = len(expenses)
    summary["Total_Expenses"] = sum(Decimal(expense["Amount"] or 0) for expense in expenses)
    summary["You_Owe"] = sum(
        Decimal(row["Remaining_Balance"])
        for row in raw_balances
        if row["Debtor_Id"] == CURRENT_USER_ID and row["Creditor_Id"] != CURRENT_USER_ID
    )
    summary["Owed_To_You"] = sum(
        Decimal(row["Remaining_Balance"])
        for row in raw_balances
        if row["Creditor_Id"] == CURRENT_USER_ID and row["Debtor_Id"] != CURRENT_USER_ID
    )

    return render_template(
        "circles/detail.html",
        title=circle["Circle_Name"],
        circle=circle,
        members=members,
        expenses=expenses,
        splits=splits,
        payments=payments,
        summary=summary,
        owes_summary=owes_summary,
        eligible_expenses=eligible_expenses,
        settlement_suggestions=settlement_suggestions,
        active_main="dashboard",
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == "dashboard"), "Dashboard"),
        hero_action={"href": url_for("expenses.new_expense", circle_id=circle_id), "label": "+ Add Expense"},
        subtabs=[
            {"key": "back", "label": "All Circles", "href": url_for("dashboard.dashboard")},
            {"key": "detail", "label": "Circle Detail", "href": url_for("circles.circle_detail", circle_id=circle_id)},
        ],
        active_subtab="detail",
    )
