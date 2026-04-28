from decimal import Decimal

from api.db import fetch_all, fetch_one


def format_money(value):
    if value is None:
        return "0.00"
    return f"{Decimal(value):.2f}"


def fetch_lookup_data(user_id):
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
        (user_id, user_id),
    )
    users = fetch_all(
        """
        SELECT User_Id, Name, Email
        FROM Users
        ORDER BY Name
        """
    )
    return circles, users


def get_circle_participant_choices(user_id):
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
        (user_id, user_id, user_id, user_id),
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


def get_you_owe_summary(circle_id, user_id):
    balances = get_circle_balance_rows(circle_id)
    owes_map = {}
    eligible_expenses = []

    for row in balances:
        if row["Remaining_Balance"] <= 0:
            continue
        if row["Debtor_Id"] == user_id:
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


def get_current_user(user_id):
    return fetch_one(
        """
        SELECT User_Id, Name, Email, Password_Hash, Date_Joined
        FROM Users
        WHERE User_Id = %s
        """,
        (user_id,),
    )


def get_dashboard_circles(user_id):
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
        (user_id, user_id),
    )

    for circle in circles:
        _, _, balances = get_you_owe_summary(circle["Circle_Id"], user_id)
        circle["You_Owe"] = sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Debtor_Id"] == user_id and row["Creditor_Id"] != user_id
        )
        circle["Owed_To_You"] = sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Creditor_Id"] == user_id and row["Debtor_Id"] != user_id
    )
    return circles


def get_user_balance_summary(user_id):
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
        (user_id, user_id),
    )

    total_you_owe = Decimal("0.00")
    total_owed_to_you = Decimal("0.00")

    for circle in accessible_circles:
        _, _, balances = get_you_owe_summary(circle["Circle_Id"], user_id)
        total_you_owe += sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Debtor_Id"] == user_id and row["Creditor_Id"] != user_id
        )
        total_owed_to_you += sum(
            Decimal(row["Remaining_Balance"])
            for row in balances
            if row["Creditor_Id"] == user_id and row["Debtor_Id"] != user_id
        )

    return {
        "Active_Circles": len(accessible_circles),
        "Total_You_Owe": total_you_owe,
        "Owed_To_You": total_owed_to_you,
    }


def get_circle_detail(circle_id, user_id):
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
        (circle_id, user_id, user_id),
    )
    if not circle:
        return None

    members = fetch_all(
        """
        SELECT
            cm.User_Id,
            u.Name,
            u.Email,
            u.`Rank`,
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
        (user_id, user_id, user_id, circle_id),
    )

    return {
        "circle": circle,
        "members": members,
        "expenses": expenses,
        "splits": splits,
        "payments": payments,
        "summary": summary or {},
    }


def get_recent_payment_links():
    return fetch_all(
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
