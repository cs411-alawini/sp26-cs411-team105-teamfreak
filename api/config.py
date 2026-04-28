from dotenv import load_dotenv
import os

load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "teamfreakdata"),
}

STATUS_OPTIONS = ("Active", "Settled", "Overdue", "Canceled")
SPLIT_TYPE_OPTIONS = ("Even", "Percent", "Custom")

MAIN_TABS = [
    {"key": "new_expense", "label": "New Expense", "caption": "Log", "href": "/expenses/new"},
    {"key": "dashboard", "label": "Dashboard", "caption": "Circles", "href": "/"},
    {"key": "user", "label": "User", "caption": "Profile", "href": "/user"},
]
