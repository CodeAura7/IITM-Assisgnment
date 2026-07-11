from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

try:
    from ..extensions import db
    from ..models import Trek, Booking, User
except ImportError:
    from extensions import db
    from models import Trek, Booking, User


staff_bp = Blueprint("staff", __name__, template_folder="../templates/staff")


def staff_required(fn):
    from functools import wraps

    @wraps(fn)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in {"staff", "admin"}:
            flash("Access denied.", "danger")
            return redirect(url_for("index"))
        if current_user.role == "staff" and current_user.is_blacklisted:
            flash("Your staff account is blacklisted.", "danger")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)

    return decorated


@staff_bp.route("/staff")
@staff_required
def dashboard():
    assigned_trek = Trek.query.get(current_user.assigned_trek_id) if current_user.assigned_trek_id else None
    bookings = Booking.query.filter_by(trek_id=current_user.assigned_trek_id).all() if current_user.assigned_trek_id else []
    return render_template("dashboard.html", assigned_trek=assigned_trek, bookings=bookings)


@staff_bp.route("/staff/trek/<int:trek_id>")
@staff_required
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if current_user.assigned_trek_id != trek.id:
        flash("You can only view your assigned trek.", "danger")
        return redirect(url_for("staff.dashboard"))
    return render_template("trek_detail.html", trek=trek, bookings=Booking.query.filter_by(trek_id=trek.id).all())


@staff_bp.route("/staff/assign/<int:staff_id>", methods=["POST"])
@staff_required
def assign_trek(staff_id):
    staff = User.query.get_or_404(staff_id)
    trek_id = request.form.get("trek_id", type=int)
    if trek_id is None:
        flash("Please select a trek.", "danger")
        return redirect(url_for("admin.manage_staff"))

    trek = Trek.query.get_or_404(trek_id)
    staff.assigned_trek_id = trek.id
    db.session.commit()
    flash("Trek assigned successfully.", "success")
    return redirect(url_for("admin.manage_staff"))


@staff_bp.route("/staff/trek/<int:trek_id>/slots", methods=["POST"])
@staff_required
def update_slots(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if current_user.assigned_trek_id != trek.id:
        flash("You can only manage your assigned trek.", "danger")
        return redirect(url_for("staff.dashboard"))
    new_slots = int(request.form.get("available_slots", trek.available_slots))
    trek.available_slots = max(0, min(new_slots, trek.capacity))
    db.session.commit()
    flash("Slots updated.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))


@staff_bp.route("/staff/trek/<int:trek_id>/status", methods=["POST"])
@staff_required
def update_status(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if current_user.assigned_trek_id != trek.id:
        flash("You can only manage your assigned trek.", "danger")
        return redirect(url_for("staff.dashboard"))
    trek.status = request.form.get("status", trek.status)
    db.session.commit()
    flash("Trek status updated.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))


@staff_bp.route("/staff/trek/<int:trek_id>/start", methods=["POST"])
@staff_required
def mark_started(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if current_user.assigned_trek_id != trek.id:
        flash("You can only manage your assigned trek.", "danger")
        return redirect(url_for("staff.dashboard"))
    trek.status = "In Progress"
    db.session.commit()
    flash("Trek marked as started.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))


@staff_bp.route("/staff/trek/<int:trek_id>/complete", methods=["POST"])
@staff_required
def mark_completed(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if current_user.assigned_trek_id != trek.id:
        flash("You can only manage your assigned trek.", "danger")
        return redirect(url_for("staff.dashboard"))
    trek.status = "Completed"
    db.session.commit()
    flash("Trek marked as completed.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))
