from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os

from flask import Flask, flash, redirect, render_template_string, request, url_for
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "teamfreak-demo-secret")


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "teamfreakdata"),
}

CURRENT_USER_ID = int(os.getenv("CURRENT_USER_ID", "3"))
STATUS_OPTIONS = ("Active", "Settled", "Overdue", "Canceled")
SPLIT_TYPE_OPTIONS = ("Even", "Percent", "Custom")

MAIN_TABS = [
    {"key": "new_expense", "label": "New Expense", "caption": "Log", "href": "/expenses/new"},
    {"key": "dashboard", "label": "Dashboard", "caption": "Circles", "href": "/"},
    {"key": "user", "label": "User", "caption": "Profile", "href": "/user"},
]


BASE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }} | TeamFreak</title>
    <style>
        :root {
            --bg: #f7f3ed;
            --phone: #111111;
            --surface: #fffaf3;
            --surface-strong: #ffffff;
            --surface-soft: #ffe6cf;
            --surface-tint: #fff0e2;
            --ink: #121212;
            --muted: #6f6258;
            --accent: #f47c20;
            --accent-strong: #c85e0c;
            --accent-soft: #ffe1c6;
            --gold: #f3a245;
            --border: #e6d3bf;
            --shadow: 0 24px 60px rgba(28, 20, 11, 0.16);
            --danger-bg: #ffe7e1;
            --danger-text: #8a2d1d;
            --success-bg: #e5f8ee;
            --success-text: #165937;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: "Montserrat", "Avenir Next", "Segoe UI", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(244, 124, 32, 0.16), transparent 25%),
                radial-gradient(circle at bottom right, rgba(17, 17, 17, 0.08), transparent 24%),
                linear-gradient(180deg, #fbf7f1 0%, #f1e6d9 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem 0.75rem;
        }

        .phone-frame {
            width: min(420px, 100%);
            background: var(--phone);
            border-radius: 38px;
            padding: 12px;
            box-shadow: 0 28px 80px rgba(0, 0, 0, 0.28);
        }

        .phone-screen {
            position: relative;
            min-height: 800px;
            height: 800px;
            border-radius: 28px;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(255, 253, 249, 0.99), rgba(247, 239, 230, 0.99));
        }

        .notch {
            width: 34%;
            height: 28px;
            background: #0b0c0e;
            border-radius: 0 0 18px 18px;
            margin: 0 auto;
        }

        .page-shell {
            padding: 0.95rem 1rem 6.9rem;
            height: calc(100% - 28px);
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: rgba(244, 124, 32, 0.5) transparent;
        }

        .page-shell::-webkit-scrollbar {
            width: 8px;
        }

        .page-shell::-webkit-scrollbar-thumb {
            background: rgba(244, 124, 32, 0.5);
            border-radius: 999px;
        }

        .page-shell::-webkit-scrollbar-track {
            background: transparent;
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.45rem 0.1rem 0.9rem;
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .hero {
            background: linear-gradient(155deg, rgba(244, 124, 32, 0.98), rgba(200, 94, 12, 0.95));
            color: white;
            border-radius: 28px;
            padding: 1.3rem;
            box-shadow: 0 18px 28px rgba(200, 94, 12, 0.24);
            margin-bottom: 0.9rem;
        }

        .hero-top {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            align-items: flex-start;
        }

        .hero h1 {
            margin: 0 0 0.35rem;
            font-size: 1.95rem;
            line-height: 1.02;
            letter-spacing: -0.035em;
        }

        .hero-action,
        .button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            font-weight: 700;
            border-radius: 999px;
            cursor: pointer;
            transition: transform 0.16s ease, background-color 0.16s ease;
        }

        .hero-action {
            background: rgba(17, 17, 17, 0.14);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0.78rem 1rem;
            white-space: nowrap;
            font-size: 0.88rem;
        }

        .hero-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .hero-pill {
            padding: 0.42rem 0.74rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 0.83rem;
            font-weight: 700;
        }

        .section-title {
            margin: 1rem 0 0.65rem;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            font-weight: 800;
        }

        .subtabs {
            display: flex;
            gap: 0.55rem;
            overflow-x: auto;
            margin-bottom: 0.4rem;
            scrollbar-width: none;
        }

        .subtabs::-webkit-scrollbar {
            display: none;
        }

        .subtab {
            white-space: nowrap;
            text-decoration: none;
            border-radius: 999px;
            padding: 0.64rem 0.9rem;
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--muted);
            background: var(--surface-soft);
        }

        .subtab.active {
            background: var(--accent-soft);
            color: var(--accent-strong);
        }

        .card,
        .table-card,
        .form-card {
            margin-top: 1rem;
            background: rgba(255, 250, 243, 0.97);
            border: 1px solid rgba(230, 211, 191, 0.85);
            border-radius: 24px;
            box-shadow: 0 12px 30px rgba(104, 74, 40, 0.08);
        }

        .card,
        .table-card,
        .form-card {
            padding: 1.1rem;
        }

        .card h2,
        .table-card h2,
        .form-card h2 {
            margin: 0 0 0.45rem;
            font-size: 1.08rem;
            letter-spacing: -0.02em;
        }

        .card p,
        .table-card p,
        .form-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.94rem;
        }

        .cards-stack,
        .stats-grid,
        .detail-grid {
            display: grid;
            gap: 0.9rem;
        }

        .stats-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .circle-card {
            display: block;
            text-decoration: none;
            color: inherit;
            background: linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(255, 242, 228, 0.96));
            border: 1px solid rgba(230, 211, 191, 0.85);
            border-radius: 24px;
            padding: 1rem;
            box-shadow: 0 12px 30px rgba(104, 74, 40, 0.08);
        }

        .circle-card-header,
        .row-between {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.75rem;
        }

        .circle-card h2 {
            margin: 0 0 0.25rem;
            font-size: 1.15rem;
            letter-spacing: -0.02em;
        }

        .circle-meta {
            font-size: 0.85rem;
            color: var(--muted);
        }

        .balance-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .balance-box,
        .stat-box {
            padding: 0.88rem;
            border-radius: 18px;
            background: var(--surface);
            border: 1px solid rgba(217, 207, 191, 0.8);
        }

        .balance-box.positive {
            background: var(--surface-tint);
        }

        .value {
            display: block;
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.15rem;
        }

        .label {
            color: var(--muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 700;
        }

        .tag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.32rem 0.65rem;
            border-radius: 999px;
            background: #ffe3c5;
            color: #b0550d;
            font-size: 0.76rem;
            font-weight: 700;
        }

        .list-rows {
            display: grid;
            gap: 0.75rem;
            margin-top: 0.9rem;
        }

        .scroll-panel {
            max-height: 260px;
            overflow-y: auto;
            padding-right: 0.25rem;
            scrollbar-width: thin;
            scrollbar-color: rgba(244, 124, 32, 0.5) transparent;
        }

        .scroll-panel::-webkit-scrollbar {
            width: 8px;
        }

        .scroll-panel::-webkit-scrollbar-thumb {
            background: rgba(244, 124, 32, 0.5);
            border-radius: 999px;
        }

        .scroll-panel::-webkit-scrollbar-track {
            background: transparent;
        }

        .list-row {
            padding: 0.9rem;
            border-radius: 18px;
            background: var(--surface-strong);
            border: 1px solid rgba(230, 211, 191, 0.8);
        }

        .list-row strong {
            display: block;
            margin-bottom: 0.25rem;
        }

        .tiny {
            font-size: 0.84rem;
            color: var(--muted);
        }

        .flash-list {
            list-style: none;
            padding: 0;
            margin: 1rem 0 0;
            display: grid;
            gap: 0.75rem;
        }

        .flash {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            border: 1px solid transparent;
            font-size: 0.92rem;
        }

        .flash.error {
            background: var(--danger-bg);
            color: var(--danger-text);
            border-color: rgba(138, 45, 29, 0.16);
        }

        .flash.success {
            background: var(--success-bg);
            color: var(--success-text);
            border-color: rgba(22, 89, 55, 0.16);
        }

        form {
            display: grid;
            gap: 0.95rem;
        }

        label {
            display: grid;
            gap: 0.42rem;
            font-weight: 700;
            font-size: 0.92rem;
        }

        input,
        select,
        textarea {
            width: 100%;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.82rem 0.92rem;
            background: var(--surface-strong);
            color: var(--ink);
            font: inherit;
        }

        textarea {
            min-height: 110px;
            resize: vertical;
        }

        .button-row {
            display: flex;
            gap: 0.7rem;
            flex-wrap: wrap;
        }

        .button {
            padding: 0.8rem 1.08rem;
            border: 1px solid transparent;
        }

        .button.primary {
            background: var(--accent);
            color: white;
        }

        .button.secondary {
            background: var(--surface);
            color: var(--ink);
            border-color: var(--border);
        }

        .button:hover,
        .hero-action:hover,
        .circle-card:hover,
        .bottom-tab:hover {
            transform: translateY(-1px);
        }

        .table-wrap {
            overflow-x: auto;
            margin-top: 0.75rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 620px;
            font-size: 0.9rem;
        }

        th,
        td {
            text-align: left;
            padding: 0.8rem 0.65rem;
            border-bottom: 1px solid rgba(217, 207, 191, 0.75);
            vertical-align: top;
        }

        th {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
        }

        tr:last-child td {
            border-bottom: none;
        }

        .empty {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 18px;
            border: 1px dashed var(--border);
            background: rgba(255, 249, 240, 0.8);
            color: var(--muted);
            font-size: 0.92rem;
        }

        .bottom-nav {
            position: absolute;
            left: 1rem;
            right: 1rem;
            bottom: 1rem;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.6rem;
            padding: 0.7rem;
            background: rgba(17, 17, 17, 0.96);
            border-radius: 24px;
            box-shadow: 0 18px 30px rgba(10, 10, 10, 0.22);
        }

        .bottom-tab {
            min-height: 58px;
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.18rem;
            border-radius: 18px;
            color: rgba(255, 255, 255, 0.76);
            text-decoration: none;
            font-size: 0.76rem;
            font-weight: 700;
        }

        .bottom-tab strong {
            font-size: 0.88rem;
            letter-spacing: -0.01em;
        }

        .bottom-tab.active {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }

        @media (max-width: 720px) {
            body {
                padding: 0;
            }

            .phone-frame {
                width: 100%;
                border-radius: 0;
                padding: 0;
                background: transparent;
                box-shadow: none;
            }

            .phone-screen {
                min-height: 100vh;
                height: 100vh;
                border-radius: 0;
            }
        }
    </style>
</head>
<body>
    <div class="phone-frame">
        <main class="phone-screen">
            <div class="notch"></div>
            <div class="page-shell">
                <div class="status-row">
                    <span>TeamFreak Demo</span>
                    <span>User {{ current_user_id }}</span>
                </div>

                <section class="hero">
                    <div class="hero-top">
                        <div>
                            <h1>{{ title }}</h1>
                        </div>
                        {% if hero_action %}
                            <a class="hero-action" href="{{ hero_action.href }}">{{ hero_action.label }}</a>
                        {% endif %}
                    </div>
                    {% if hero_pills %}
                        <div class="hero-meta">
                            {% for pill in hero_pills %}
                                <span class="hero-pill">{{ pill }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </section>

                {% if subtabs %}
                    <div class="section-title">{{ active_main_label }}</div>
                    <nav class="subtabs">
                        {% for subtab in subtabs %}
                            <a class="subtab {% if subtab.key == active_subtab %}active{% endif %}" href="{{ subtab.href }}">
                                {{ subtab.label }}
                            </a>
                        {% endfor %}
                    </nav>
                {% endif %}

                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        <ul class="flash-list">
                            {% for category, message in messages %}
                                <li class="flash {{ category }}">{{ message }}</li>
                            {% endfor %}
                        </ul>
                    {% endif %}
                {% endwith %}

                {{ content|safe }}
            </div>

            <nav class="bottom-nav">
                {% for tab in main_tabs %}
                    <a class="bottom-tab {% if tab.key == active_main %}active{% endif %}" href="{{ tab.href }}">
                        <strong>{{ tab.label }}</strong>
                        <span>{{ tab.caption }}</span>
                    </a>
                {% endfor %}
            </nav>
        </main>
    </div>
</body>
</html>
"""


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def fetch_all_raw(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def execute_write(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def execute_many(query, params_list):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.executemany(query, params_list)
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def format_money(value):
    if value is None:
        return "0.00"
    return f"{Decimal(value):.2f}"


def fetch_lookup_data():
    circles = fetch_all(
        """
        SELECT Circle_Id, Circle_Name
        FROM Circle
        WHERE Creation_User_Id = %s
           OR Circle_Id IN (
                SELECT Circle_Id
                FROM Circle_Member
                WHERE User_Id = %s
           )
        ORDER BY Circle_Name
        """
        ,
        (CURRENT_USER_ID, CURRENT_USER_ID),
    )
    users = fetch_all(
        """
        SELECT User_Id, Name, Email
        FROM Users
        ORDER BY Name
        """
    )
    return circles, users


def get_circle_participant_choices():
    rows = fetch_all(
        """
        SELECT
            c.Circle_Id,
            u.User_Id,
            u.Name,
            u.Email
        FROM Circle c
        JOIN Users creator ON c.Creation_User_Id = creator.User_Id
        JOIN Users u ON u.User_Id = creator.User_Id
        WHERE c.Creation_User_Id = %s
           OR c.Circle_Id IN (
                SELECT Circle_Id
                FROM Circle_Member
                WHERE User_Id = %s
           )

        UNION

        SELECT
            c.Circle_Id,
            u.User_Id,
            u.Name,
            u.Email
        FROM Circle c
        JOIN Circle_Member cm ON c.Circle_Id = cm.Circle_Id
        JOIN Users u ON cm.User_Id = u.User_Id
        WHERE c.Creation_User_Id = %s
           OR c.Circle_Id IN (
                SELECT Circle_Id
                FROM Circle_Member
                WHERE User_Id = %s
           )
        ORDER BY Circle_Id, Name
        """,
        (CURRENT_USER_ID, CURRENT_USER_ID, CURRENT_USER_ID, CURRENT_USER_ID),
    )

    choices = {}
    for row in rows:
        choices.setdefault(str(row["Circle_Id"]), [])
        if not any(existing["User_Id"] == row["User_Id"] for existing in choices[str(row["Circle_Id"])]):
            choices[str(row["Circle_Id"])].append(row)
    return choices


def get_circle_member_ids(circle_id):
    rows = fetch_all(
        """
        SELECT DISTINCT User_Id
        FROM (
            SELECT c.Creation_User_Id AS User_Id
            FROM Circle c
            WHERE c.Circle_Id = %s
            UNION
            SELECT cm.User_Id
            FROM Circle_Member cm
            WHERE cm.Circle_Id = %s
        ) members
        """,
        (circle_id, circle_id),
    )
    return [row["User_Id"] for row in rows]


def get_circle_balance_rows(circle_id):
    rows = fetch_all(
        """
        SELECT
            e.Expense_Id,
            e.Description,
            e.Creation_Date,
            creator.User_Id AS Creditor_Id,
            creator.Name AS Creditor_Name,
            es.User_Id AS Debtor_Id,
            debtor.Name AS Debtor_Name,
            es.Amount_Owed,
            COALESCE(linked_payments.Total_Paid, 0) AS Total_Paid
        FROM Expense e
        JOIN Users creator ON e.User_Id = creator.User_Id
        JOIN Expense_Split es ON e.Expense_Id = es.Expense_Id
        JOIN Users debtor ON es.User_Id = debtor.User_Id
        LEFT JOIN (
            SELECT
                ep.Expense_Id,
                p.Sender_Id,
                p.Receiver_Id,
                SUM(p.Amount) AS Total_Paid
            FROM Expense_Payment ep
            JOIN Payments p ON ep.Payment_Id = p.Payment_Id
            GROUP BY ep.Expense_Id, p.Sender_Id, p.Receiver_Id
        ) linked_payments
            ON linked_payments.Expense_Id = e.Expense_Id
            AND linked_payments.Sender_Id = es.User_Id
            AND linked_payments.Receiver_Id = e.User_Id
        WHERE e.Circle_Id = %s
          AND es.User_Id <> e.User_Id
        ORDER BY e.Expense_Id DESC, debtor.Name
        """,
        (circle_id,),
    )

    for row in rows:
        owed = Decimal(row["Amount_Owed"] or 0).quantize(Decimal("0.01"))
        paid = Decimal(row["Total_Paid"] or 0).quantize(Decimal("0.01"))
        remaining = max(Decimal("0.00"), (owed - paid).quantize(Decimal("0.01")))
        row["Remaining_Balance"] = remaining
    return rows


def get_you_owe_summary(circle_id):
    balances = get_circle_balance_rows(circle_id)
    owes_map = {}
    eligible_expenses = []

    for row in balances:
        if row["Remaining_Balance"] <= 0:
            continue
        if row["Debtor_Id"] == CURRENT_USER_ID:
            creditor_id = row["Creditor_Id"]
            owes_map.setdefault(
                creditor_id,
                {
                    "receiver_id": creditor_id,
                    "receiver_name": row["Creditor_Name"],
                    "amount": Decimal("0.00"),
                },
            )
            owes_map[creditor_id]["amount"] += row["Remaining_Balance"]
            eligible_expenses.append(
                {
                    "expense_id": row["Expense_Id"],
                    "receiver_id": creditor_id,
                    "receiver_name": row["Creditor_Name"],
                    "remaining_balance": row["Remaining_Balance"],
                    "description": row["Description"] or "No description",
                    "creation_date": row["Creation_Date"],
                }
            )

    owes_summary = list(owes_map.values())
    owes_summary.sort(key=lambda item: item["receiver_name"])
    eligible_expenses.sort(key=lambda item: (item["receiver_name"], item["expense_id"]))
    return owes_summary, eligible_expenses, balances


def build_settlement_suggestions(circle_id):
    balances = get_circle_balance_rows(circle_id)
    net = {}

    for row in balances:
        remaining = row["Remaining_Balance"]
        if remaining <= 0:
            continue
        debtor_id = row["Debtor_Id"]
        creditor_id = row["Creditor_Id"]
        net[debtor_id] = net.get(debtor_id, Decimal("0.00")) - remaining
        net[creditor_id] = net.get(creditor_id, Decimal("0.00")) + remaining

    user_names = {
        row["Debtor_Id"]: row["Debtor_Name"] for row in balances
    }
    user_names.update({row["Creditor_Id"]: row["Creditor_Name"] for row in balances})

    debtors = [[user_id, amount.copy_abs()] for user_id, amount in net.items() if amount < 0]
    creditors = [[user_id, amount] for user_id, amount in net.items() if amount > 0]

    suggestions = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, debt_amount = debtors[debtor_index]
        creditor_id, credit_amount = creditors[creditor_index]
        transfer_amount = min(debt_amount, credit_amount).quantize(Decimal("0.01"))

        if transfer_amount > 0:
            suggestions.append(
                {
                    "from_id": debtor_id,
                    "from_name": user_names.get(debtor_id, f"User {debtor_id}"),
                    "to_id": creditor_id,
                    "to_name": user_names.get(creditor_id, f"User {creditor_id}"),
                    "amount": transfer_amount,
                }
            )

        debt_amount = (debt_amount - transfer_amount).quantize(Decimal("0.01"))
        credit_amount = (credit_amount - transfer_amount).quantize(Decimal("0.01"))
        debtors[debtor_index][1] = debt_amount
        creditors[creditor_index][1] = credit_amount

        if debt_amount <= 0:
            debtor_index += 1
        if credit_amount <= 0:
            creditor_index += 1

    return suggestions


def insert_payment(circle_id, form_data):
    receiver_id_raw = form_data.get("receiver_id", "").strip()
    expense_id_raw = form_data.get("expense_id", "").strip()
    amount_raw = form_data.get("amount", "").strip()
    description = form_data.get("description", "").strip()
    payment_date = date.today().isoformat()

    if not receiver_id_raw or not expense_id_raw or not amount_raw:
        raise ValueError("Receiver, linked expense, and amount are required.")

    try:
        receiver_id = int(receiver_id_raw)
        expense_id = int(expense_id_raw)
        amount = Decimal(amount_raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (ValueError, InvalidOperation) as exc:
        raise ValueError("Payment inputs must be valid values.") from exc

    if amount <= 0:
        raise ValueError("Payment amount must be greater than 0.")

    eligible_rows = {
        row["expense_id"]: row
        for row in get_you_owe_summary(circle_id)[1]
        if row["receiver_id"] == receiver_id
    }

    if expense_id not in eligible_rows:
        raise ValueError("The selected expense does not match the selected receiver or is not owed by you.")

    remaining_balance = Decimal(eligible_rows[expense_id]["remaining_balance"]).quantize(Decimal("0.01"))
    if amount > remaining_balance:
        raise ValueError("Payment amount cannot exceed the remaining amount you owe on that expense.")

    payment_id = execute_write(
        """
        INSERT INTO Payments (
            Sender_Id,
            Receiver_Id,
            Circle_Id,
            Amount,
            Payment_Date,
            Description
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (CURRENT_USER_ID, receiver_id, circle_id, amount, payment_date, description or None),
    )

    execute_write(
        """
        INSERT INTO Expense_Payment (Expense_Id, Payment_Id)
        VALUES (%s, %s)
        """,
        (expense_id, payment_id),
    )


def get_current_user():
    return fetch_one(
        """
        SELECT User_Id, Name, Email, Password_Hash, Date_Joined
        FROM Users
        WHERE User_Id = %s
        """,
        (CURRENT_USER_ID,),
    )


def get_dashboard_circles():
    circles = fetch_all(
        """
        SELECT
            c.Circle_Id,
            c.Circle_Name,
            c.Creation_Date,
            creator.Name AS Creator_Name,
            COALESCE(m.member_count, 0) AS Member_Count
        FROM Circle c
        JOIN Users creator ON c.Creation_User_Id = creator.User_Id
        LEFT JOIN (
            SELECT Circle_Id, COUNT(*) AS member_count
            FROM Circle_Member
            GROUP BY Circle_Id
        ) m ON c.Circle_Id = m.Circle_Id
        WHERE c.Creation_User_Id = %s
           OR c.Circle_Id IN (
                SELECT Circle_Id
                FROM Circle_Member
                WHERE User_Id = %s
           )
        ORDER BY c.Circle_Name
        """,
        (CURRENT_USER_ID, CURRENT_USER_ID),
    )

    for circle in circles:
        _, _, balances = get_you_owe_summary(circle["Circle_Id"])
        circle["You_Owe"] = sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Debtor_Id"] == CURRENT_USER_ID and row["Creditor_Id"] != CURRENT_USER_ID
        )
        circle["Owed_To_You"] = sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Creditor_Id"] == CURRENT_USER_ID and row["Debtor_Id"] != CURRENT_USER_ID
    )
    return circles


def get_user_balance_summary():
    accessible_circles = fetch_all(
        """
        SELECT Circle_Id
        FROM Circle
        WHERE Creation_User_Id = %s
           OR Circle_Id IN (
                SELECT Circle_Id
                FROM Circle_Member
                WHERE User_Id = %s
           )
        ORDER BY Circle_Id
        """,
        (CURRENT_USER_ID, CURRENT_USER_ID),
    )

    total_you_owe = Decimal("0.00")
    total_owed_to_you = Decimal("0.00")

    for circle in accessible_circles:
        _, _, balances = get_you_owe_summary(circle["Circle_Id"])
        total_you_owe += sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Debtor_Id"] == CURRENT_USER_ID and row["Creditor_Id"] != CURRENT_USER_ID
        )
        total_owed_to_you += sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Creditor_Id"] == CURRENT_USER_ID and row["Debtor_Id"] != CURRENT_USER_ID
        )

    return {
        "Active_Circles": len(accessible_circles),
        "Total_You_Owe": total_you_owe,
        "Owed_To_You": total_owed_to_you,
    }


def get_circle_detail(circle_id):
    circle = fetch_one(
        """
        SELECT
            c.Circle_Id,
            c.Circle_Name,
            c.Creation_Date,
            c.Creation_User_Id,
            u.Name AS Creator_Name,
            u.Email AS Creator_Email
        FROM Circle c
        JOIN Users u ON c.Creation_User_Id = u.User_Id
        WHERE c.Circle_Id = %s
          AND (
                c.Creation_User_Id = %s
                OR c.Circle_Id IN (
                    SELECT Circle_Id
                    FROM Circle_Member
                    WHERE User_Id = %s
                )
          )
        """,
        (circle_id, CURRENT_USER_ID, CURRENT_USER_ID),
    )
    if not circle:
        return None

    members = fetch_all(
        """
        SELECT
            cm.User_Id,
            u.Name,
            u.Email,
            cm.Role,
            cm.Status,
            cm.Date_Joined
        FROM Circle_Member cm
        JOIN Users u ON cm.User_Id = u.User_Id
        WHERE cm.Circle_Id = %s
        ORDER BY u.Name
        """,
        (circle_id,),
    )

    expenses = fetch_all(
        """
        SELECT
            e.Expense_Id,
            e.Amount,
            e.Creation_Date,
            e.Paid_Date,
            CASE
                WHEN COALESCE(payment_totals.Total_Paid, 0) >= e.Amount THEN 'Settled'
                ELSE e.Status
            END AS Status,
            e.Description,
            e.Split_Type,
            u.Name AS Created_By
        FROM Expense e
        JOIN Users u ON e.User_Id = u.User_Id
        LEFT JOIN (
            SELECT ep.Expense_Id, SUM(p.Amount) AS Total_Paid
            FROM Expense_Payment ep
            JOIN Payments p ON ep.Payment_Id = p.Payment_Id
            GROUP BY ep.Expense_Id
        ) payment_totals ON e.Expense_Id = payment_totals.Expense_Id
        WHERE e.Circle_Id = %s
        ORDER BY e.Creation_Date DESC, e.Expense_Id DESC
        """,
        (circle_id,),
    )

    splits = fetch_all(
        """
        SELECT
            es.Expense_Id,
            u.Name AS User_Name,
            es.Amount_Owed,
            e.Description
        FROM Expense_Split es
        JOIN Expense e ON es.Expense_Id = e.Expense_Id
        JOIN Users u ON es.User_Id = u.User_Id
        WHERE e.Circle_Id = %s
        ORDER BY es.Expense_Id DESC, u.Name
        """,
        (circle_id,),
    )

    payments = fetch_all(
        """
        SELECT
            p.Payment_Id,
            sender.Name AS Sender_Name,
            receiver.Name AS Receiver_Name,
            p.Amount,
            p.Payment_Date,
            p.Description
        FROM Payments p
        JOIN Users sender ON p.Sender_Id = sender.User_Id
        JOIN Users receiver ON p.Receiver_Id = receiver.User_Id
        WHERE p.Circle_Id = %s
        ORDER BY p.Payment_Date DESC, p.Payment_Id DESC
        """,
        (circle_id,),
    )

    summary = fetch_one(
        """
        SELECT
            COALESCE(COUNT(DISTINCT e.Expense_Id), 0) AS Expense_Count,
            COALESCE(SUM(DISTINCT e.Amount), 0) AS Total_Expenses,
            COALESCE(SUM(CASE WHEN es.User_Id = %s THEN es.Amount_Owed ELSE 0 END), 0) AS You_Owe,
            COALESCE(SUM(CASE WHEN e.User_Id = %s AND es.User_Id <> %s THEN es.Amount_Owed ELSE 0 END), 0) AS Owed_To_You
        FROM Circle c
        LEFT JOIN Expense e ON c.Circle_Id = e.Circle_Id
        LEFT JOIN Expense_Split es ON e.Expense_Id = es.Expense_Id
        WHERE c.Circle_Id = %s
        """,
        (CURRENT_USER_ID, CURRENT_USER_ID, CURRENT_USER_ID, circle_id),
    )

    return {
        "circle": circle,
        "members": members,
        "expenses": expenses,
        "splits": splits,
        "payments": payments,
        "summary": summary or {},
    }


def insert_expense(form_data):
    amount_raw = form_data.get("amount", "").strip()
    circle_id_raw = form_data.get("circle_id", "").strip()
    new_circle_name = form_data.get("new_circle_name", "").strip()
    user_id_raw = form_data.get("user_id", "").strip()
    creation_date = date.today().isoformat()
    split_type = form_data.get("split_type", "").strip()
    description = form_data.get("description", "").strip()
    paid_date = form_data.get("paid_date", "").strip() or None
    new_circle_member_ids_raw = form_data.getlist("new_circle_member_ids")

    if not amount_raw or not user_id_raw or not split_type:
        raise ValueError("Please fill in all required expense fields.")

    if not circle_id_raw:
        raise ValueError("Please choose a circle.")

    if circle_id_raw == "__new__" and not new_circle_name:
        raise ValueError("Please enter a name for the new circle.")

    if split_type not in SPLIT_TYPE_OPTIONS:
        raise ValueError("The selected split type is not valid.")

    try:
        amount = Decimal(amount_raw)
    except InvalidOperation as exc:
        raise ValueError("Amount must be a valid number such as 24.99.") from exc

    if amount <= 0:
        raise ValueError("Amount must be greater than 0.")

    try:
        user_id = int(user_id_raw)
    except ValueError as exc:
        raise ValueError("User selection must be a valid id.") from exc

    if circle_id_raw != "__new__":
        try:
            circle_id = int(circle_id_raw)
        except ValueError as exc:
            raise ValueError("Circle selection must be a valid id.") from exc
        circle_member_ids = get_circle_member_ids(circle_id)
    else:
        try:
            selected_new_member_ids = [int(member_id) for member_id in new_circle_member_ids_raw]
        except ValueError as exc:
            raise ValueError("New circle member selection contains an invalid user id.") from exc

        selected_new_member_ids = list(dict.fromkeys(selected_new_member_ids))
        if user_id not in selected_new_member_ids:
            selected_new_member_ids.append(user_id)

        circle_id = execute_write(
            """
            INSERT INTO Circle (Circle_Name, Creation_Date, Creation_User_Id)
            VALUES (%s, %s, %s)
            """,
            (new_circle_name, creation_date, user_id),
        )
        circle_member_ids = selected_new_member_ids

    if split_type in {"Custom", "Percent"}:
        participant_ids = [member_id for member_id in circle_member_ids if member_id != user_id]
        if not participant_ids:
            if split_type == "Custom":
                raise ValueError("This circle does not have other members to assign custom amounts to.")
            raise ValueError("This circle does not have other members to assign percentages to.")
    else:
        participant_ids = [member_id for member_id in circle_member_ids if member_id != user_id]
        if not participant_ids:
            raise ValueError("This circle does not have other members to split the expense with.")

    expense_id = execute_write(
        """
        INSERT INTO Expense (
            Amount,
            Circle_Id,
            User_Id,
            Creation_Date,
            Paid_Date,
            Status,
            Description,
            Split_Type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            amount,
            circle_id,
            user_id,
            creation_date,
            paid_date,
            "Active",
            description or None,
            split_type,
        ),
    )

    if split_type == "Custom":
        split_amounts = build_custom_split(form_data, participant_ids, amount)
    elif split_type == "Percent":
        split_amounts = build_percent_split(form_data, participant_ids, amount)
    else:
        split_amounts = build_even_split(amount, participant_ids)

    execute_many(
        """
        INSERT INTO Expense_Split (Expense_Id, User_Id, Amount_Owed)
        VALUES (%s, %s, %s)
        """,
        [(expense_id, participant_id, owed_amount) for participant_id, owed_amount in split_amounts.items()],
    )

    if circle_id_raw == "__new__":
        add_members_to_new_circle(circle_id, user_id, circle_member_ids)

    return circle_id


def insert_circle(form_data):
    circle_name = form_data.get("circle_name", "").strip()
    creation_date = date.today().isoformat()
    member_ids_raw = form_data.getlist("member_ids")

    if not circle_name:
        raise ValueError("Please fill in all required circle fields.")

    creator_id = CURRENT_USER_ID

    try:
        member_ids = [int(member_id) for member_id in member_ids_raw]
    except ValueError as exc:
        raise ValueError("Member selection contains an invalid user id.") from exc

    member_ids = list(dict.fromkeys(member_ids))
    if creator_id not in member_ids:
        member_ids.append(creator_id)

    circle_id = execute_write(
        """
        INSERT INTO Circle (Circle_Name, Creation_Date, Creation_User_Id)
        VALUES (%s, %s, %s)
        """,
        (circle_name, creation_date, creator_id),
    )

    add_members_to_new_circle(circle_id, creator_id, member_ids)
    return circle_id


def build_even_split(total_amount, participant_ids):
    split_count = len(participant_ids)
    base_amount = (total_amount / split_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    split_amounts = {participant_id: base_amount for participant_id in participant_ids}
    remainder = total_amount - (base_amount * split_count)
    if remainder != Decimal("0.00"):
        first_participant = participant_ids[0]
        split_amounts[first_participant] = (split_amounts[first_participant] + remainder).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    return split_amounts


def build_custom_split(form_data, participant_ids, total_amount):
    split_amounts = {}
    running_total = Decimal("0.00")
    for participant_id in participant_ids:
        raw_amount = form_data.get(f"custom_owed_{participant_id}", "").strip()
        if not raw_amount:
            raise ValueError("Every selected participant needs a custom owed amount.")
        try:
            owed_amount = Decimal(raw_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError("Custom split amounts must be valid numbers.") from exc
        if owed_amount < 0:
            raise ValueError("Custom split amounts cannot be negative.")
        split_amounts[participant_id] = owed_amount
        running_total += owed_amount

    if running_total != total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):
        raise ValueError("Custom split amounts must add up exactly to the full expense amount.")

    return split_amounts


def build_percent_split(form_data, participant_ids, total_amount):
    percent_map = {}
    running_percent = Decimal("0.00")
    for participant_id in participant_ids:
        raw_percent = form_data.get(f"percent_owed_{participant_id}", "").strip()
        if not raw_percent:
            raise ValueError("Every selected participant needs a percent owed value.")
        try:
            percent_value = Decimal(raw_percent).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError("Percent split values must be valid numbers.") from exc
        if percent_value < 0:
            raise ValueError("Percent split values cannot be negative.")
        percent_map[participant_id] = percent_value
        running_percent += percent_value

    if running_percent != Decimal("100.00"):
        raise ValueError("Percent split values must add up to exactly 100%.")

    split_amounts = {}
    running_total = Decimal("0.00")
    ordered_ids = list(percent_map.keys())
    for index, participant_id in enumerate(ordered_ids):
        if index == len(ordered_ids) - 1:
            owed_amount = (total_amount - running_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            owed_amount = ((total_amount * percent_map[participant_id]) / Decimal("100.00")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            running_total += owed_amount
        split_amounts[participant_id] = owed_amount

    return split_amounts


def add_members_to_new_circle(circle_id, creator_id, participant_ids):
    rows = [(circle_id, creator_id, "Owner", "Active", date.today().isoformat())]
    seen = {creator_id}
    for participant_id in participant_ids:
        if participant_id not in seen:
            rows.append((circle_id, participant_id, "Member", "Active", date.today().isoformat()))
            seen.add(participant_id)

    execute_many(
        """
        INSERT INTO Circle_Member (Circle_Id, User_Id, Role, Status, Date_Joined)
        VALUES (%s, %s, %s, %s, %s)
        """,
        rows,
    )


def update_user(form_data):
    name = form_data.get("name", "").strip()
    email = form_data.get("email", "").strip()
    password_hash = form_data.get("password_hash", "").strip()

    if not name or not email:
        raise ValueError("Name and email are required.")

    current = get_current_user()
    execute_write(
        """
        UPDATE Users
        SET Name = %s, Email = %s, Password_Hash = %s
        WHERE User_Id = %s
        """,
        (name, email, password_hash or current["Password_Hash"], CURRENT_USER_ID),
    )


def render_page(title, subtitle, content_template, **context):
    content = render_template_string(content_template, **context)
    active_main = context.get("active_main", "dashboard")
    return render_template_string(
        BASE_TEMPLATE,
        title=title,
        subtitle=subtitle,
        content=content,
        hero_pills=context.get("hero_pills", []),
        hero_action=context.get("hero_action"),
        subtabs=context.get("subtabs", []),
        active_subtab=context.get("active_subtab"),
        active_main=active_main,
        active_main_label=next((tab["label"] for tab in MAIN_TABS if tab["key"] == active_main), "Dashboard"),
        main_tabs=MAIN_TABS,
        current_user_id=CURRENT_USER_ID,
    )


@app.route("/")
def dashboard():
    try:
        circles = get_dashboard_circles()
    except Error as exc:
        flash(f"Database error while loading dashboard circles: {exc}", "error")
        circles = []

    content_template = """
    {% if circles %}
        <section class="cards-stack">
            {% for circle in circles %}
                <a class="circle-card" href="{{ url_for('circle_detail', circle_id=circle.Circle_Id) }}">
                    <div class="circle-card-header">
                        <div>
                            <h2>{{ circle.Circle_Name }}</h2>
                            <div class="circle-meta">
                                Created {{ circle.Creation_Date }} by {{ circle.Creator_Name }}
                            </div>
                        </div>
                        <span class="tag">{{ circle.Member_Count }} members</span>
                    </div>
                    <div class="balance-grid">
                        <div class="balance-box">
                            <span class="value">${{ money(circle.You_Owe) }}</span>
                            <span class="label">You Owe</span>
                        </div>
                        <div class="balance-box positive">
                            <span class="value">${{ money(circle.Owed_To_You) }}</span>
                            <span class="label">Owed To You</span>
                        </div>
                    </div>
                </a>
            {% endfor %}
        </section>
    {% else %}
        <div class="empty">No circles were returned. Create your first one from the button above.</div>
    {% endif %}
    """
    return render_page(
        "Dashboard",
        "See all of your circles at a glance, with quick balance summaries before drilling into the details.",
        content_template,
        circles=circles,
        money=format_money,
        active_main="dashboard",
        hero_action={"href": url_for("new_circle"), "label": "+ New Circle"},
    )


@app.route("/circles/new", methods=["GET", "POST"])
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
            return redirect(url_for("circle_detail", circle_id=circle_id))

    content_template = """
    <section class="form-card">
        <h2>Create New Circle</h2>
        <p>This is the top-level group creation flow that lives off the Dashboard.</p>
        <form method="post">
            <label>
                Circle Name *
                <input type="text" name="circle_name" placeholder="Roommates, Spring Break, Trip Fund..." required>
            </label>
            <section class="table-card">
                <h2>Choose Circle Members</h2>
                <p>Search and select the users who should belong to this circle.</p>
                <label>
                    Search users
                    <input type="text" id="circle-member-search" placeholder="Search by name or email">
                </label>
                <div class="list-rows scroll-panel" id="circle-members-list">
                    {% for user in users %}
                        <label class="list-row circle-member-row" data-search="{{ (user.Name ~ ' ' ~ user.Email)|lower }}">
                            <div class="row-between">
                                <div>
                                    <strong>{{ user.Name }}</strong>
                                    <div class="tiny">{{ user.Email }}</div>
                                </div>
                                <input
                                    type="checkbox"
                                    name="member_ids"
                                    value="{{ user.User_Id }}"
                                    {% if user.User_Id == current_user_id %}checked disabled{% endif %}
                                >
                            </div>
                            {% if user.User_Id == current_user_id %}
                                <div class="tiny" style="margin-top: 0.5rem;">The creator is automatically included in the new circle.</div>
                            {% endif %}
                        </label>
                    {% endfor %}
                </div>
            </section>
            <div class="button-row">
                <button class="button primary" type="submit">Create Circle</button>
                <a class="button secondary" href="{{ url_for('dashboard') }}">Back to Dashboard</a>
            </div>
        </form>
        <script>
            const memberSearch = document.getElementById('circle-member-search');
            const memberRows = Array.from(document.querySelectorAll('.circle-member-row'));
            const memberCheckboxes = Array.from(document.querySelectorAll('input[name="member_ids"]'));

            function filterMembers() {
                const term = (memberSearch.value || "").trim().toLowerCase();
                memberRows.forEach((row) => {
                    row.style.display = !term || row.dataset.search.includes(term) ? "grid" : "none";
                });
            }

            function syncCreatorMembership() {
                memberCheckboxes.forEach((checkbox) => {
                    const isCreator = checkbox.value === "{{ current_user_id }}";
                    checkbox.disabled = isCreator;
                    if (isCreator) {
                        checkbox.checked = true;
                    }
                });
            }

            memberSearch.addEventListener("input", filterMembers);
            syncCreatorMembership();
            filterMembers();
        </script>
    </section>
    """
    return render_page(
        "New Circle",
        "Create a new circle from the top of the Dashboard before adding members and expenses.",
        content_template,
        users=users,
        current_user_id=CURRENT_USER_ID,
        active_main="dashboard",
    )


@app.route("/circles/<int:circle_id>", methods=["GET", "POST"])
def circle_detail(circle_id):
    if request.method == "POST":
        try:
            insert_payment(circle_id, request.form)
        except (ValueError, Error) as exc:
            flash(f"Could not record payment: {exc}", "error")
        else:
            flash("Payment recorded and linked to the selected expense.", "success")
            return redirect(url_for("circle_detail", circle_id=circle_id))

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
        return redirect(url_for("dashboard"))

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

    content_template = """
    <section class="table-card">
        <h2>Make Payment</h2>
        <p>Record a payment inside this circle and link it directly to the expense it settles.</p>
        {% if owes_summary %}
            <div class="list-rows">
                {% for item in owes_summary %}
                    <div class="list-row">
                        <strong>You owe {{ item.receiver_name }}</strong>
                        <div class="tiny">${{ money(item.amount) }}</div>
                    </div>
                {% endfor %}
            </div>

            <form method="post" style="margin-top: 1rem;">
                <label>
                    Send To *
                    <select name="receiver_id" id="receiver-select" required>
                        <option value="">Select receiver</option>
                        {% for item in owes_summary %}
                            <option value="{{ item.receiver_id }}">{{ item.receiver_name }} (${{ money(item.amount) }})</option>
                        {% endfor %}
                    </select>
                </label>
                <label>
                    Linked Expense *
                    <select name="expense_id" id="expense-select" required>
                        <option value="">Select expense</option>
                        {% for expense in eligible_expenses %}
                            <option
                                value="{{ expense.expense_id }}"
                                data-receiver-id="{{ expense.receiver_id }}"
                                data-remaining="{{ money(expense.remaining_balance) }}"
                            >
                                Expense {{ expense.expense_id }} | {{ expense.receiver_name }} | ${{ money(expense.remaining_balance) }} remaining | {{ expense.description }}
                            </option>
                        {% endfor %}
                    </select>
                </label>
                <label>
                    Amount *
                    <input type="number" name="amount" id="payment-amount" step="0.01" min="0.01" placeholder="0.00" required>
                </label>
                <label>
                    Description
                    <textarea name="description" placeholder="Dinner repayment, rent share, groceries..."></textarea>
                </label>
                <div class="button-row">
                    <button class="button primary" type="submit">Record Payment</button>
                </div>
            </form>
        {% else %}
            <div class="empty">You do not currently owe anyone in this circle.</div>
        {% endif %}
    </section>

    <section class="table-card">
        <h2>Settlement Suggestions</h2>
        <p>These are simplified payment suggestions inside the circle that reduce unnecessary back-and-forth payments.</p>
        {% if settlement_suggestions %}
            <div class="list-rows">
                {% for suggestion in settlement_suggestions %}
                    <div class="list-row">
                        <strong>{{ suggestion.from_name }} can pay {{ suggestion.to_name }}</strong>
                        <div class="tiny">${{ money(suggestion.amount) }}</div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="empty">No simplified settlement suggestions are needed right now.</div>
        {% endif %}
    </section>

    <section class="stats-grid">
        <article class="stat-box">
            <span class="value">${{ money(summary.Total_Expenses) }}</span>
            <span class="label">Total Expenses</span>
        </article>
        <article class="stat-box">
            <span class="value">{{ summary.Expense_Count or 0 }}</span>
            <span class="label">Expenses Logged</span>
        </article>
        <article class="stat-box">
            <span class="value">${{ money(summary.You_Owe) }}</span>
            <span class="label">You Owe</span>
        </article>
        <article class="stat-box">
            <span class="value">${{ money(summary.Owed_To_You) }}</span>
            <span class="label">Owed To You</span>
        </article>
    </section>

    <section class="table-card">
        <h2>Circle Overview</h2>
        <div class="list-rows">
            <div class="list-row">
                <strong>Creator</strong>
                <div class="tiny">{{ circle.Creator_Name }} ({{ circle.Creator_Email }})</div>
            </div>
            <div class="list-row">
                <strong>Created On</strong>
                <div class="tiny">{{ circle.Creation_Date }}</div>
            </div>
        </div>
    </section>

    <section class="table-card">
        <h2>Members</h2>
        {% if members %}
            <div class="list-rows">
                {% for member in members %}
                    <div class="list-row">
                        <div class="row-between">
                            <div>
                                <strong>{{ member.Name }}</strong>
                                <div class="tiny">{{ member.Email }}</div>
                            </div>
                            <span class="tag">{{ member.Status }}</span>
                        </div>
                        <div class="tiny">Role: {{ member.Role }}{% if member.Date_Joined %} | Joined: {{ member.Date_Joined }}{% endif %}</div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="empty">No circle members were returned.</div>
        {% endif %}
    </section>

    <section class="table-card">
        <h2>Expenses</h2>
        {% if expenses %}
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Expense ID</th>
                            <th>Creator</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Split Type</th>
                            <th>Created</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for expense in expenses %}
                            <tr>
                                <td>{{ expense.Expense_Id }}</td>
                                <td>{{ expense.Created_By }}</td>
                                <td>${{ money(expense.Amount) }}</td>
                                <td>{{ expense.Status }}</td>
                                <td>{{ expense.Split_Type }}</td>
                                <td>{{ expense.Creation_Date }}</td>
                                <td>{{ expense.Description or "No description" }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="empty">No expenses were returned for this circle.</div>
        {% endif %}
    </section>

    <section class="table-card">
        <h2>Expense Splits</h2>
        {% if splits %}
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Expense ID</th>
                            <th>User</th>
                            <th>Amount Owed</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for split in splits %}
                            <tr>
                                <td>{{ split.Expense_Id }}</td>
                                <td>{{ split.User_Name }}</td>
                                <td>${{ money(split.Amount_Owed) }}</td>
                                <td>{{ split.Description or "No description" }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="empty">No expense split data was returned.</div>
        {% endif %}
    </section>

    <section class="table-card">
        <h2>Payments</h2>
        {% if payments %}
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Payment ID</th>
                            <th>Sender</th>
                            <th>Receiver</th>
                            <th>Amount</th>
                            <th>Date</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for payment in payments %}
                            <tr>
                                <td>{{ payment.Payment_Id }}</td>
                                <td>{{ payment.Sender_Name }}</td>
                                <td>{{ payment.Receiver_Name }}</td>
                                <td>${{ money(payment.Amount) }}</td>
                                <td>{{ payment.Payment_Date }}</td>
                                <td>{{ payment.Description or "No description" }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="empty">No payment records were returned for this circle.</div>
        {% endif %}
    </section>

    <script>
        const receiverSelect = document.getElementById('receiver-select');
        const expenseSelect = document.getElementById('expense-select');
        const paymentAmountInput = document.getElementById('payment-amount');

        function syncExpenseOptions() {
            if (!receiverSelect || !expenseSelect) return;
            const receiverId = receiverSelect.value;
            let firstVisibleOption = "";

            Array.from(expenseSelect.options).forEach((option, index) => {
                if (index === 0) {
                    option.hidden = false;
                    return;
                }
                const matches = !receiverId || option.dataset.receiverId === receiverId;
                option.hidden = !matches;
                if (matches && !firstVisibleOption) {
                    firstVisibleOption = option.value;
                }
            });

            if (expenseSelect.selectedOptions.length && expenseSelect.selectedOptions[0].hidden) {
                expenseSelect.value = "";
            }
        }

        function syncAmountHint() {
            if (!expenseSelect || !paymentAmountInput) return;
            const selectedOption = expenseSelect.selectedOptions[0];
            if (selectedOption && selectedOption.dataset.remaining) {
                paymentAmountInput.max = selectedOption.dataset.remaining;
                paymentAmountInput.placeholder = selectedOption.dataset.remaining;
            } else {
                paymentAmountInput.removeAttribute('max');
                paymentAmountInput.placeholder = "0.00";
            }
        }

        if (receiverSelect && expenseSelect) {
            receiverSelect.addEventListener('change', () => {
                syncExpenseOptions();
                syncAmountHint();
            });
            expenseSelect.addEventListener('change', syncAmountHint);
            syncExpenseOptions();
            syncAmountHint();
        }
    </script>
    """
    return render_page(
        circle["Circle_Name"],
        "This detail view is where circle members, expenses, balances, expense splits, and payments come together.",
        content_template,
        circle=circle,
        members=members,
        expenses=expenses,
        splits=splits,
        payments=payments,
        summary=summary,
        money=format_money,
        owes_summary=owes_summary,
        eligible_expenses=eligible_expenses,
        settlement_suggestions=settlement_suggestions,
        active_main="dashboard",
        hero_action={"href": url_for("new_expense", circle_id=circle_id), "label": "+ Add Expense"},
        subtabs=[
            {"key": "back", "label": "All Circles", "href": url_for("dashboard")},
            {"key": "detail", "label": "Circle Detail", "href": url_for("circle_detail", circle_id=circle_id)},
        ],
        active_subtab="detail",
    )


@app.route("/expenses/new", methods=["GET", "POST"])
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
            return redirect(url_for("circle_detail", circle_id=circle_id))

    content_template = """
    <section class="form-card">
        <h2>Log New Expense</h2>
        <p>
            This left tab is dedicated to creating a new expense. You can assign it to an
            existing circle or create a new circle inline.
        </p>
        <form method="post">
            <label>
                Amount *
                <input type="number" name="amount" step="0.01" min="0.01" placeholder="49.99" required>
            </label>
            <label>
                Circle *
                <select name="circle_id">
                    <option value="">Select a circle</option>
                    <option value="__new__" {% if preselected_circle_id == "__new__" %}selected{% endif %}>Create a new circle</option>
                    {% for circle in circles %}
                        <option value="{{ circle.Circle_Id }}" {% if preselected_circle_id|string == circle.Circle_Id|string %}selected{% endif %}>
                            {{ circle.Circle_Name }} (ID {{ circle.Circle_Id }})
                        </option>
                    {% endfor %}
                </select>
            </label>
            <label id="new-circle-field" style="display: none;">
                New Circle Name
                <input type="text" name="new_circle_name" placeholder="Only needed when creating a new circle">
            </label>
            <section id="new-circle-members-section" class="table-card" style="display: none;">
                <h2>Choose Circle Members</h2>
                <p>Search and select the users who should belong to this new circle.</p>
                <label>
                    Search users
                    <input type="text" id="new-circle-member-search" placeholder="Search by name or email">
                </label>
                <div class="list-rows scroll-panel" id="new-circle-members-list">
                    {% for user in users %}
                        <label class="list-row new-circle-member-row" data-search="{{ (user.Name ~ ' ' ~ user.Email)|lower }}">
                            <div class="row-between">
                                <div>
                                    <strong>{{ user.Name }}</strong>
                                    <div class="tiny">{{ user.Email }}</div>
                                </div>
                                <input
                                    type="checkbox"
                                    name="new_circle_member_ids"
                                    value="{{ user.User_Id }}"
                                    {% if user.User_Id == current_user_id %}checked disabled{% endif %}
                                >
                            </div>
                            {% if user.User_Id == current_user_id %}
                                <div class="tiny" style="margin-top: 0.5rem;">The payer is automatically included as a member of the new circle.</div>
                            {% endif %}
                        </label>
                    {% endfor %}
                </div>
            </section>
            <label>
                Who Paid? *
                <select name="user_id" required></select>
            </label>
            <label>
                Original Purchase Date
                <input type="date" name="paid_date" value="{{ today_str }}">
            </label>
            <label>
                Split Type *
                <select name="split_type" required>
                    {% for split_type in split_type_options %}
                        <option value="{{ split_type }}">{{ split_type }}</option>
                    {% endfor %}
                </select>
            </label>
            <section id="custom-split-section" class="table-card" style="display: none;">
                <h2 id="split-detail-title">Custom Split</h2>
                <p>
                    Select the people who owe you and enter either exact dollar amounts or percentages,
                    depending on the chosen split type.
                </p>
                <div id="custom-split-empty" class="empty" style="display: none;">
                    Choose a circle first. Split assignment needs a circle so we know who can be assigned.
                </div>
                <div id="custom-split-list" class="list-rows scroll-panel"></div>
            </section>
            <label>
                Description
                <textarea name="description" placeholder="Dinner, groceries, concert tickets..."></textarea>
            </label>
            <div class="button-row">
                <button class="button primary" type="submit">Create Expense</button>
            </div>
        </form>
        <script>
            const circleSelect = document.querySelector('select[name="circle_id"]');
            const newCircleField = document.getElementById('new-circle-field');
            const newCircleMembersSection = document.getElementById('new-circle-members-section');
            const newCircleMemberSearch = document.getElementById('new-circle-member-search');
            const newCircleMemberRows = Array.from(document.querySelectorAll('.new-circle-member-row'));
            const newCircleMemberCheckboxes = Array.from(document.querySelectorAll('input[name="new_circle_member_ids"]'));
            const splitTypeSelect = document.querySelector('select[name="split_type"]');
            const payerSelect = document.querySelector('select[name="user_id"]');
            const customSplitSection = document.getElementById('custom-split-section');
            const splitDetailTitle = document.getElementById('split-detail-title');
            const customSplitList = document.getElementById('custom-split-list');
            const customSplitEmpty = document.getElementById('custom-split-empty');
            const circleParticipantChoices = {{ circle_participant_choices|tojson }};
            const allUsers = {{ users|tojson }};
            const currentUserId = "{{ current_user_id }}";
            let preferredPayerId = currentUserId;

            function syncCircleMode() {
                const isNewCircle = circleSelect.value === "__new__";
                newCircleField.style.display = isNewCircle ? "grid" : "none";
                newCircleMembersSection.style.display = isNewCircle ? "block" : "none";
                renderPayerOptions();
                syncNewCirclePayer();
            }

            function syncNewCirclePayer() {
                const isNewCircle = circleSelect.value === "__new__";
                newCircleMemberCheckboxes.forEach((checkbox) => {
                    const isPayer = checkbox.value === payerSelect.value;
                    checkbox.disabled = isNewCircle && isPayer;
                    if (isPayer) {
                        checkbox.checked = true;
                    }
                });
            }

            function getSelectedNewCircleMembers() {
                return newCircleMemberCheckboxes
                    .filter((checkbox) => checkbox.checked)
                    .map((checkbox) => {
                        const row = checkbox.closest('.new-circle-member-row');
                        const name = row.querySelector('strong')?.textContent || "";
                        const email = row.querySelector('.tiny')?.textContent || "";
                        return { User_Id: checkbox.value, Name: name, Email: email };
                    });
            }

            function renderPayerOptions() {
                const selectedCircle = circleSelect.value;
                const isNewCircle = selectedCircle === "__new__";
                const payerCandidates = isNewCircle
                    ? getSelectedNewCircleMembers()
                    : (circleParticipantChoices[selectedCircle] || []);

                payerSelect.innerHTML = "";

                if (!selectedCircle || payerCandidates.length === 0) {
                    payerSelect.innerHTML = '<option value="">Select a circle first</option>';
                    return;
                }

                payerCandidates.forEach((user) => {
                    const option = document.createElement("option");
                    option.value = user.User_Id;
                    option.textContent = `${user.Name} (ID ${user.User_Id})`;
                    payerSelect.appendChild(option);
                });

                const validPreferred = payerCandidates.some((user) => String(user.User_Id) === String(preferredPayerId));
                payerSelect.value = validPreferred ? preferredPayerId : String(payerCandidates[0].User_Id);
                preferredPayerId = payerSelect.value;
            }

            function filterNewCircleMembers() {
                const term = (newCircleMemberSearch.value || "").trim().toLowerCase();
                newCircleMemberRows.forEach((row) => {
                    row.style.display = !term || row.dataset.search.includes(term) ? "grid" : "none";
                });
            }

            function renderCustomSplit() {
                const splitMode = splitTypeSelect.value;
                const showAssignedSplit = splitMode === "Custom" || splitMode === "Percent";
                customSplitSection.style.display = showAssignedSplit ? "block" : "none";
                if (!showAssignedSplit) {
                    customSplitList.innerHTML = "";
                    return;
                }

                splitDetailTitle.textContent = splitMode === "Percent" ? "Percent Split" : "Custom Split";

                const selectedCircle = circleSelect.value;
                const payerId = payerSelect.value;
                const members = selectedCircle === "__new__"
                    ? getSelectedNewCircleMembers()
                    : (circleParticipantChoices[selectedCircle] || []);

                if (!selectedCircle || members.length === 0) {
                    customSplitEmpty.style.display = "block";
                    customSplitList.innerHTML = "";
                    return;
                }

                customSplitEmpty.style.display = "none";
                customSplitList.innerHTML = members
                    .filter((member) => String(member.User_Id) !== payerId)
                    .map((member) => `
                        <label class="list-row">
                            <div class="row-between">
                                <div>
                                    <strong>${member.Name}</strong>
                                    <div class="tiny">${member.Email}</div>
                                </div>
                                <span class="tag">Included</span>
                            </div>
                            <div class="tiny" style="margin-top: 0.7rem;">
                                <label>
                                    ${splitMode === "Percent" ? `Percent owed by ${member.Name}` : `Amount owed by ${member.Name}`}
                                    <input
                                        type="number"
                                        name="${splitMode === "Percent" ? `percent_owed_${member.User_Id}` : `custom_owed_${member.User_Id}`}"
                                        step="0.01"
                                        min="0"
                                        ${splitMode === "Percent" ? `max="100"` : ""}
                                        placeholder="${splitMode === "Percent" ? '0.00%' : '0.00'}"
                                    >
                                </label>
                            </div>
                        </label>
                    `)
                    .join("");
            }

            circleSelect.addEventListener("change", syncCircleMode);
            circleSelect.addEventListener("change", renderCustomSplit);
            splitTypeSelect.addEventListener("change", renderCustomSplit);
            payerSelect.addEventListener("change", () => {
                preferredPayerId = payerSelect.value;
                syncNewCirclePayer();
                renderCustomSplit();
            });
            newCircleMemberSearch.addEventListener("input", filterNewCircleMembers);
            newCircleMemberCheckboxes.forEach((checkbox) =>
                checkbox.addEventListener("change", () => {
                    renderPayerOptions();
                    syncNewCirclePayer();
                    renderCustomSplit();
                })
            );
            syncCircleMode();
            filterNewCircleMembers();
            renderCustomSplit();
        </script>
    </section>
    """
    return render_page(
        "New Expense",
        "Use this tab when the main task is logging a new charge and assigning it to a circle.",
        content_template,
        circles=circles,
        users=users,
        current_user_id=CURRENT_USER_ID,
        preselected_circle_id=preselected_circle_id,
        circle_participant_choices=circle_participant_choices,
        today_str=today_str,
        split_type_options=SPLIT_TYPE_OPTIONS,
        active_main="new_expense",
    )


@app.route("/user", methods=["GET", "POST"])
def user_profile():
    if request.method == "POST":
        try:
            update_user(request.form)
        except (ValueError, Error) as exc:
            flash(f"Could not update user information: {exc}", "error")
        else:
            flash("User information updated successfully.", "success")
            return redirect(url_for("user_profile"))

    try:
        user = get_current_user()
        summary = get_user_balance_summary()
        owed_to_user = {"Owed_To_You": summary["Owed_To_You"]}
        recent_links = fetch_all(
            """
            SELECT
                ep.Expense_Id,
                ep.Payment_Id,
                p.Payment_Date,
                p.Amount
            FROM Expense_Payment ep
            JOIN Payments p ON ep.Payment_Id = p.Payment_Id
            ORDER BY p.Payment_Date DESC, ep.Payment_Id DESC
            LIMIT 5
            """
        )
    except Error as exc:
        flash(f"Database error while loading user page: {exc}", "error")
        user = None
        summary = {"Active_Circles": 0, "Total_You_Owe": 0, "Owed_To_You": 0}
        owed_to_user = {"Owed_To_You": 0}
        recent_links = []

    content_template = """
    {% if user %}
        <section class="stats-grid">
            <article class="stat-box">
                <span class="value">{{ summary.Active_Circles or 0 }}</span>
                <span class="label">Active Circles</span>
            </article>
            <article class="stat-box">
                <span class="value">${{ money(summary.Total_You_Owe) }}</span>
                <span class="label">You Owe</span>
            </article>
            <article class="stat-box">
                <span class="value">${{ money(owed_to_user.Owed_To_You) }}</span>
                <span class="label">Owed To You</span>
            </article>
            <article class="stat-box">
                <span class="value">{{ user.Date_Joined }}</span>
                <span class="label">Joined</span>
            </article>
        </section>

        <section class="form-card">
            <h2>Your Information</h2>
            <p>This right tab is your profile home and edit screen.</p>
            <form method="post">
                <label>
                    Name *
                    <input type="text" name="name" value="{{ user.Name }}" required>
                </label>
                <label>
                    Email *
                    <input type="email" name="email" value="{{ user.Email }}" required>
                </label>
                <label>
                    Password Hash
                    <input type="text" name="password_hash" value="{{ user.Password_Hash }}">
                </label>
                <div class="button-row">
                    <button class="button primary" type="submit">Save Profile</button>
                </div>
            </form>
        </section>

        <section class="table-card">
            <h2>Recent Expense-Payment Links</h2>
            {% if recent_links %}
                <div class="list-rows">
                    {% for row in recent_links %}
                        <div class="list-row">
                            <strong>Expense {{ row.Expense_Id }} linked to Payment {{ row.Payment_Id }}</strong>
                            <div class="tiny">${{ money(row.Amount) }} on {{ row.Payment_Date }}</div>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="empty">No recent expense-payment links were returned.</div>
            {% endif %}
        </section>
    {% else %}
        <div class="empty">The current user could not be loaded.</div>
    {% endif %}
    """
    return render_page(
        "User",
        "See your profile, edit your information, and keep a small view of your personal summary data.",
        content_template,
        user=user,
        summary=summary,
        owed_to_user=owed_to_user,
        recent_links=recent_links,
        money=format_money,
        active_main="user",
    )


if __name__ == "__main__":
    app.run(debug=True)
