import re

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from ..auth_utils import (
    clear_auth_cookie,
    create_token,
    hash_password,
    login_required,
    read_user_from_cookie,
    set_auth_cookie,
    verify_password,
)
from ..database import db
from ..models import ApiUsage, MotionPlan, User

auth_bp = Blueprint("auth", __name__)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def user_payload(user):
    usage_count = (
        db.session.query(func.count(ApiUsage.id))
        .filter(ApiUsage.user_id == user.id)
        .scalar()
    )
    plan_count = (
        db.session.query(func.count(MotionPlan.id))
        .filter(MotionPlan.user_id == user.id)
        .scalar()
    )
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
        "usage_count": usage_count or 0,
        "plan_count": plan_count or 0,
    }


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")

    # Role is never taken from the client. Self-registration is always "user".
    if not _EMAIL.match(email):
        return jsonify(error="Enter a valid email address"), 400
    if not 3 <= len(password) <= 128:
        return jsonify(error="Password must be between 3 and 128 characters"), 400
    if User.query.filter_by(email=email).first() is not None:
        return jsonify(error="An account with that email already exists"), 409

    user = User(email=email, password_hash=hash_password(password), role="user")
    db.session.add(user)
    db.session.commit()
    g.user_id = user.id

    response = jsonify(user=user_payload(user))
    response.status_code = 201
    return set_auth_cookie(response, create_token(user))


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    user = User.query.filter_by(email=email).first()
    if user is None or not verify_password(password, user.password_hash):
        return jsonify(error="Invalid email or password"), 401

    g.user_id = user.id
    response = jsonify(user=user_payload(user))
    return set_auth_cookie(response, create_token(user))


@auth_bp.post("/logout")
def logout():
    user = read_user_from_cookie()
    if user is not None:
        g.user_id = user.id
    response = jsonify(ok=True)
    return clear_auth_cookie(response)


@auth_bp.get("/me")
@login_required
def me():
    recent = (
        ApiUsage.query.filter_by(user_id=g.user.id)
        .order_by(ApiUsage.created_at.desc())
        .limit(8)
        .all()
    )
    payload = user_payload(g.user)
    payload["recent_usage"] = [
        {
            "endpoint": row.endpoint,
            "method": row.method,
            "status_code": row.status_code,
            "created_at": row.created_at.isoformat(),
        }
        for row in recent
    ]
    return jsonify(user=payload)
