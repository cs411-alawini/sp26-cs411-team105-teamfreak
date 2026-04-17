import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask

from api.config import CURRENT_USER_ID, MAIN_TABS
from api.queries import format_money
from routes.circles import bp as circles_bp
from routes.dashboard import bp as dashboard_bp
from routes.expenses import bp as expenses_bp
from routes.user import bp as user_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "teamfreak-demo-secret")
app.jinja_env.filters["money"] = format_money


@app.context_processor
def inject_globals():
    return dict(main_tabs=MAIN_TABS, current_user_id=CURRENT_USER_ID)


app.register_blueprint(dashboard_bp)
app.register_blueprint(circles_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(user_bp)

if __name__ == "__main__":
    app.run(debug=True, port=8080)
