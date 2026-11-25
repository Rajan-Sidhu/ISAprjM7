from datetime import datetime, timezone

from .database import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    plans = db.relationship("MotionPlan", back_populates="user", lazy="dynamic")
    usage = db.relationship("ApiUsage", back_populates="user", lazy="dynamic")


class MotionPlan(db.Model):
    """A saved AI motion plan. Kept separate from the user account."""

    __tablename__ = "motion_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    plan_json = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="plans")


class ApiUsage(db.Model):
    """One row per API call. Not stored on the user record."""

    __tablename__ = "api_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    user = db.relationship("User", back_populates="usage")
