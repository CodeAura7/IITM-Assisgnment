import os

from flask import Flask, redirect, url_for
from flask_login import current_user

try:
    from .config import Config
    from .extensions import db, login_manager
    from .models import Booking, Trek, User
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.staff_routes import staff_bp
    from .routes.user_routes import user_bp
except ImportError:
    from config import Config
    from extensions import db, login_manager
    from models import Booking, Trek, User
    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.staff_routes import staff_bp
    from routes.user_routes import user_bp


def seed_database():
    db.create_all()

    admin = User.query.filter_by(email="admin@example.com").first()
    if not admin:
        admin = User(username="admin", email="admin@example.com", role="admin", approval_status="approved")
        admin.set_password("admin123")
        db.session.add(admin)

    staff = User.query.filter_by(email="staff@example.com").first()
    if not staff:
        staff = User(username="staff", email="staff@example.com", role="staff", approval_status="approved")
        staff.set_password("staff123")
        db.session.add(staff)

    sample_trek = Trek.query.filter_by(name="Snow Trail Trek").first()
    if not sample_trek:
        sample_trek = Trek(
            name="Snow Trail Trek",
            location="Manali",
            description="A scenic trek with alpine views and a glacial lake.",
            duration_days=3,
            price=3500,
            capacity=12,
            available_slots=12,
            difficulty="Moderate",
            status="Open",
        )
        db.session.add(sample_trek)

    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            if current_user.role == "staff":
                return redirect(url_for("staff.dashboard"))
            return redirect(url_for("user.dashboard"))
        return redirect(url_for("auth.login"))

    with app.app_context():
        seed_database()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
