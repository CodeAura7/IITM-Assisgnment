from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

try:
    from ..extensions import db
    from ..models import User, Trek, Booking
except ImportError:
    from extensions import db
    from models import User, Trek, Booking


admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "admin":
            flash("Access denied.", "danger")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)

    return decorated


@admin_bp.route("/admin")
@admin_required
def dashboard():
    treks = Trek.query.all()
    users = User.query.filter(User.role != "admin").all()
    staff_members = User.query.filter_by(role="staff").all()
    bookings = Booking.query.all()
    return render_template("dashboard.html", treks=treks, users=users, staff_members=staff_members, bookings=bookings)


@admin_bp.route("/admin/treks", methods=["GET", "POST"])
@admin_required
def manage_treks():
    query = request.args.get("query", "").strip()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        duration_days = int(request.form.get("duration_days", 0))
        price = float(request.form.get("price", 0))
        capacity = int(request.form.get("capacity", 0))
        difficulty = request.form.get("difficulty", "Easy")
        status = request.form.get("status", "Open")
        if not all([name, location, description]) or duration_days <= 0 or price < 0 or capacity <= 0:
            flash("Please enter valid trek details.", "danger")
            return redirect(url_for("admin.manage_treks"))
        trek = Trek(name=name, location=location, description=description, duration_days=duration_days, price=price,
                    capacity=capacity, available_slots=capacity, difficulty=difficulty, status=status)
        db.session.add(trek)
        db.session.commit()
        flash("Trek created successfully.", "success")
        return redirect(url_for("admin.manage_treks"))
    treks = Trek.query
    if query:
        try:
            trek_id = int(query)
            treks = treks.filter((Trek.id == trek_id) | (Trek.name.ilike(f"%{query}%")))
        except ValueError:
            treks = treks.filter(Trek.name.ilike(f"%{query}%"))
    treks = treks.all()
    return render_template("manage_treks.html", treks=treks, query=query)


@admin_bp.route("/admin/treks/edit/<int:trek_id>", methods=["GET", "POST"])
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if request.method == "POST":
        trek.name = request.form.get("name", trek.name).strip()
        trek.location = request.form.get("location", trek.location).strip()
        trek.description = request.form.get("description", trek.description).strip()
        trek.duration_days = int(request.form.get("duration_days", trek.duration_days))
        trek.price = float(request.form.get("price", trek.price))
        trek.capacity = int(request.form.get("capacity", trek.capacity))
        trek.difficulty = request.form.get("difficulty", trek.difficulty)
        trek.status = request.form.get("status", trek.status)
        trek.available_slots = max(0, trek.capacity - sum(1 for b in trek.bookings if b.status == "confirmed"))
        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin.manage_treks"))
    return render_template("edit_trek.html", trek=trek)


@admin_bp.route("/admin/treks/delete/<int:trek_id>", methods=["POST"])
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek.id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted successfully.", "success")
    return redirect(url_for("admin.manage_treks"))


@admin_bp.route("/admin/users")
@admin_required
def manage_users():
    query = request.args.get("query", "").strip()
    users = User.query.filter(User.role != "admin")
    if query:
        try:
            user_id = int(query)
            users = users.filter((User.id == user_id) | (User.username.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
        except ValueError:
            users = users.filter((User.username.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
    users = users.all()
    return render_template("manage_users.html", users=users, query=query)


@admin_bp.route("/admin/staff", methods=["GET", "POST"])
@admin_required
def manage_staff():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("All staff fields are required.", "danger")
            return redirect(url_for("admin.manage_staff"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("admin.manage_staff"))
        staff = User(username=username, email=email, role="staff", approval_status="approved")
        staff.set_password(password)
        db.session.add(staff)
        db.session.commit()
        flash("Staff created successfully.", "success")
        return redirect(url_for("admin.manage_staff"))
    query = request.args.get("query", "").strip()
    staff_members = User.query.filter_by(role="staff")
    if query:
        try:
            staff_id = int(query)
            staff_members = staff_members.filter((User.id == staff_id) | (User.username.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
        except ValueError:
            staff_members = staff_members.filter((User.username.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
    staff_members = staff_members.all()
    treks = Trek.query.all()
    return render_template("manage_staff.html", staff_members=staff_members, treks=treks, query=query)


@admin_bp.route("/admin/staff/approve/<int:staff_id>", methods=["POST"])
@admin_required
def approve_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.approval_status = "approved"
    db.session.commit()
    flash("Staff account approved.", "success")
    return redirect(url_for("admin.manage_staff"))


@admin_bp.route("/admin/staff/blacklist/<int:staff_id>", methods=["POST"])
@admin_required
def blacklist_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.is_blacklisted = True
    db.session.commit()
    flash("Staff account blacklisted.", "success")
    return redirect(url_for("admin.manage_staff"))


@admin_bp.route("/admin/staff/unblacklist/<int:staff_id>", methods=["POST"])
@admin_required
def unblacklist_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.is_blacklisted = False
    db.session.commit()
    flash("Staff account unblacklisted.", "success")
    return redirect(url_for("admin.manage_staff"))


@admin_bp.route("/admin/user/blacklist/<int:user_id>", methods=["POST"])
@admin_required
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = True
    db.session.commit()
    flash("User blacklisted.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/admin/user/unblacklist/<int:user_id>", methods=["POST"])
@admin_required
def unblacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blacklisted = False
    db.session.commit()
    flash("User unblacklisted.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/admin/bookings")
@admin_required
def bookings():
    bookings = Booking.query.order_by(Booking.booked_at.desc()).all()
    return render_template("bookings.html", bookings=bookings)


@admin_bp.route("/admin/history")
@admin_required
def history():
    bookings = Booking.query.order_by(Booking.booked_at.desc()).all()
    return render_template("history.html", bookings=bookings)
