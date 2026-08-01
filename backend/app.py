import os
import secrets

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

from db import ensure_indexes, users_col
from models import User, get_setting, set_setting


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    CORS(app, supports_credentials=True, origins=["http://localhost:4200", "http://localhost:4201"])

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "not authenticated"}), 401

    from auth import auth_bp
    from routes_ai import ai_bp
    from routes_campaigns import campaigns_bp
    from routes_dashboard import dashboard_bp
    from routes_leads import leads_bp
    from routes_settings import settings_bp
    from routes_unsubscribe import unsubscribe_bp
    from routes_users import users_bp
    from routes_webhooks import webhooks_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(leads_bp, url_prefix="/api/leads")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(campaigns_bp, url_prefix="/api/campaigns")
    app.register_blueprint(webhooks_bp, url_prefix="/api/webhooks")
    app.register_blueprint(unsubscribe_bp, url_prefix="/api/unsubscribe")
    app.register_blueprint(ai_bp, url_prefix="/api")

    ensure_indexes()
    _seed_admin()
    _seed_webhook_secret()

    # Sous le reloader Flask (debug=True), ce module s'execute deux fois (process
    # moniteur + process worker). On ne demarre la boucle de fond que dans le
    # worker qui sert vraiment les requetes, sinon les emails partiraient en double.
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from scheduler import start_scheduler

        start_scheduler(app)

    return app


def _seed_admin():
    if users_col.count_documents({}) == 0:
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "admin123")
        User.create(username, generate_password_hash(password))
        print(f"[seed] admin account created: {username} / {password} (change it in Settings)")


def _seed_webhook_secret():
    if not get_setting("webhook_secret"):
        set_setting("webhook_secret", secrets.token_urlsafe(24))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
