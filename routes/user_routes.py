from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

try:
    from ..extensions import db
    from ..models import Trek, Booking, User
except ImportError:
    from extensions import db
    from models import Trek, Booking, User


user_bp = Blueprint("user", __name__, template_folder="../templates/user")


def user_required(fn):
    from functools import wraps

    @wraps(fn)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "user":
            flash("Access denied.", "danger")
            return redirect(url_for("index"))
        if current_user.is_blacklisted:
            flash("Your account is blacklisted.", "danger")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)

    return decorated


@user_bp.route("/user")
@user_required
def dashboard():
    treks = Trek.query.filter_by(status="Open").all()
    return render_template("dashboard.html", treks=treks)


@user_bp.route("/user/treks")
@user_required
def treks():
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "")
    query = request.args.get("query", "")
    treks = Trek.query.filter_by(status="Open")
    if difficulty:
        treks = treks.filter_by(difficulty=difficulty)
    if location:
        treks = treks.filter(Trek.location.ilike(f"%{location}%"))
    if query:
        treks = treks.filter((Trek.name.ilike(f"%{query}%")) | (Trek.location.ilike(f"%{query}%")))
    treks = treks.all()
    return render_template("treks.html", treks=treks, difficulty=difficulty, location=location, query=query)


@user_bp.route("/user/book", methods=["POST"])
@user_required
def book_trek():
    trek_id = int(request.form.get("trek_id"))
    trek = Trek.query.get_or_404(trek_id)
    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("user.my_bookings"))
    existing = Booking.query.filter_by(trek_id=trek.id, user_id=current_user.id).first()
    if existing:
        flash("You have already booked this trek.", "danger")
        return redirect(url_for("user.my_bookings"))
    if trek.available_slots <= 0:
        flash("No slots available.", "danger")
        return redirect(url_for("user.my_bookings"))

    booking = Booking(trek_id=trek.id, user_id=current_user.id, status="confirmed")
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()
    flash("Booking successful.", "success")
    return redirect(url_for("user.my_bookings"))


@user_bp.route("/user/bookings")
@user_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()
    return render_template("my_bookings.html", bookings=bookings)


@user_bp.route("/user/profile", methods=["GET", "POST"])
@user_required
def profile():
    if request.method == "POST":
        current_user.username = request.form.get("username", current_user.username).strip()
        current_user.phone = request.form.get("phone", current_user.phone)
        current_user.address = request.form.get("address", current_user.address)
        db.session.commit()
        flash("Profile updated successfully.", "success")
    return render_template("profile.html")


@user_bp.route("/user/history")
@user_required
def history():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()
    return render_template("history.html", bookings=bookings)
