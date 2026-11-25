from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, g, jsonify, request

from .database import db
from .models import User


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(user):
    expires = datetime.now(timezone.utc) + timedelta(
        hours=current_app.config["JWT_EXPIRES_HOURS"]
    )
    payload = {"sub": str(user.id), "exp": expires}
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def read_user_from_cookie():
    token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, current_app.config["JWT_SECRET"], algorithms=["HS256"]
        )
    except jwt.PyJWTError:
        return None
    user = db_get_user(payload.get("sub"))
    return user


def db_get_user(user_id):
    if user_id is None:
        return None
    try:
        parsed = int(user_id)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, parsed)


def set_auth_cookie(response, token):
    secure = current_app.config["COOKIE_SECURE"]
    response.set_cookie(
        current_app.config["JWT_COOKIE_NAME"],
        token,
        httponly=True,
        secure=secure,
        samesite="None" if secure else "Lax",
        max_age=current_app.config["JWT_EXPIRES_HOURS"] * 3600,
        path="/",
    )
    return response


def clear_auth_cookie(response):
    secure = current_app.config["COOKIE_SECURE"]
    response.set_cookie(
        current_app.config["JWT_COOKIE_NAME"],
        "",
        httponly=True,
        secure=secure,
        samesite="None" if secure else "Lax",
        max_age=0,
        path="/",
        expires=0,
    )
    return response


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = read_user_from_cookie()
        if user is None:
            return jsonify(error="Authentication required"), 401
        g.user = user
        g.user_id = user.id
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Role is read from the database, not from the client."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = read_user_from_cookie()
        if user is None:
            return jsonify(error="Authentication required"), 401
        g.user = user
        g.user_id = user.id
        if user.role != "admin":
            return jsonify(error="Administrator role required"), 403
        return view(*args, **kwargs)

    return wrapped
