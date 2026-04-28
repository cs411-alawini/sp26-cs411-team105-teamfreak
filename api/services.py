from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from werkzeug.security import check_password_hash, generate_password_hash

from api.config import SPLIT_TYPE_OPTIONS
from api.db import execute_many, execute_write, fetch_one
from api.queries import get_circle_member_ids, get_current_user, get_you_owe_summary


def register_user(name, email, password):
    existing = fetch_one("SELECT User_Id FROM Users WHERE Email = %s", (email,))
    if existing:
        raise ValueError("An account with that email already exists.")

    password_hash = generate_password_hash(password)
    user_id = execute_write(
        """
        INSERT INTO Users (Name, Email, Password_Hash, Date_Joined)
        VALUES (%s, %s, %s, %s)
        """,
        (name, email, password_hash, date.today().isoformat()),
    )
    return fetch_one("SELECT User_Id, Name, Email FROM Users WHERE User_Id = %s", (user_id,))


def authenticate_user(email, password):
    user = fetch_one(
        "SELECT User_Id, Name, Email, Password_Hash FROM Users WHERE Email = %s",
        (email,),
    )
    if not user:
        return None
    stored = user["Password_Hash"]
    # Support werkzeug hashes and plain-text demo passwords
    try:
        valid = check_password_hash(stored, password)
    except Exception:
        valid = False
    if not valid:
        valid = (stored == password)
    return user if valid else None


def insert_payment(circle_id, form_data, user_id):
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
        for row in get_you_owe_summary(circle_id, user_id)[1]
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
        (user_id, receiver_id, circle_id, amount, payment_date, description or None),
    )

    execute_write(
        """
        INSERT INTO Expense_Payment (Expense_Id, Payment_Id)
        VALUES (%s, %s)
        """,
        (expense_id, payment_id),
    )


def insert_expense(form_data, user_id):
    amount_raw = form_data.get("amount", "").strip()
    circle_id_raw = form_data.get("circle_id", "").strip()
    new_circle_name = form_data.get("new_circle_name", "").strip()
    payer_id_raw = form_data.get("user_id", "").strip()
    creation_date = date.today().isoformat()
    split_type = form_data.get("split_type", "").strip()
    description = form_data.get("description", "").strip()
    paid_date = form_data.get("paid_date", "").strip() or None
    new_circle_member_ids_raw = form_data.getlist("new_circle_member_ids")

    if not amount_raw or not payer_id_raw or not split_type:
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
        payer_id = int(payer_id_raw)
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
        if payer_id not in selected_new_member_ids:
            selected_new_member_ids.append(payer_id)

        circle_id = execute_write(
            """
            INSERT INTO Circle (Circle_Name, Creation_Date, Creation_User_Id)
            VALUES (%s, %s, %s)
            """,
            (new_circle_name, creation_date, payer_id),
        )
        circle_member_ids = selected_new_member_ids

    if split_type in {"Custom", "Percent"}:
        participant_ids = [member_id for member_id in circle_member_ids if member_id != payer_id]
        if not participant_ids:
            if split_type == "Custom":
                raise ValueError("This circle does not have other members to assign custom amounts to.")
            raise ValueError("This circle does not have other members to assign percentages to.")
    else:
        participant_ids = [member_id for member_id in circle_member_ids if member_id != payer_id]
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
            payer_id,
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
        add_members_to_new_circle(circle_id, payer_id, circle_member_ids)

    return circle_id


def insert_circle(form_data, user_id):
    circle_name = form_data.get("circle_name", "").strip()
    creation_date = date.today().isoformat()
    member_ids_raw = form_data.getlist("member_ids")

    if not circle_name:
        raise ValueError("Please fill in all required circle fields.")

    try:
        member_ids = [int(member_id) for member_id in member_ids_raw]
    except ValueError as exc:
        raise ValueError("Member selection contains an invalid user id.") from exc

    member_ids = list(dict.fromkeys(member_ids))
    if user_id not in member_ids:
        member_ids.append(user_id)

    circle_id = execute_write(
        """
        INSERT INTO Circle (Circle_Name, Creation_Date, Creation_User_Id)
        VALUES (%s, %s, %s)
        """,
        (circle_name, creation_date, user_id),
    )

    add_members_to_new_circle(circle_id, user_id, member_ids)
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


def update_user(form_data, user_id):
    name = form_data.get("name", "").strip()
    email = form_data.get("email", "").strip()
    new_password = form_data.get("new_password", "").strip()

    if not name or not email:
        raise ValueError("Name and email are required.")

    current = get_current_user(user_id)
    if new_password:
        password_hash = generate_password_hash(new_password)
    else:
        password_hash = current["Password_Hash"]

    execute_write(
        """
        UPDATE Users
        SET Name = %s, Email = %s, Password_Hash = %s
        WHERE User_Id = %s
        """,
        (name, email, password_hash, user_id),
    )
