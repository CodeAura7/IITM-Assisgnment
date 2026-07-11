from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash

try:
    from .extensions import db
except ImportError:
    from extensions import db


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")
    status = db.Column(db.String(20), default="Open")
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    approval_status = db.Column(db.String(20), default="approved")
    is_blacklisted = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=True)

    assigned_trek = db.relationship("Trek", foreign_keys=[assigned_trek_id], backref="staff_member")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("trek_id", "user_id", name="uq_booking_trek_user"),)

    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="confirmed")

    trek = db.relationship("Trek", backref="bookings")
    user = db.relationship("User", backref="bookings")
