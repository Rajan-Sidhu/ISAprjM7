from flask import Blueprint, jsonify
from sqlalchemy import func

from ..auth_utils import admin_required
from ..database import db
from ..models import ApiUsage, MotionPlan, User

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@admin_required
def users():
    plan_counts = dict(
        db.session.query(MotionPlan.user_id, func.count(MotionPlan.id)).group_by(
            MotionPlan.user_id
        )
    )
    request_counts = dict(
        db.session.query(ApiUsage.user_id, func.count(ApiUsage.id))
        .filter(ApiUsage.user_id.isnot(None))
        .group_by(ApiUsage.user_id)
    )
    rows = User.query.order_by(User.created_at.asc()).all()
    return jsonify(
        users=[
            {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "plan_count": plan_counts.get(user.id, 0),
                "request_count": request_counts.get(user.id, 0),
            }
            for user in rows
        ]
    )


@admin_bp.get("/stats")
@admin_required
def stats():
    by_endpoint = (
        db.session.query(ApiUsage.method, ApiUsage.endpoint, func.count(ApiUsage.id))
        .group_by(ApiUsage.method, ApiUsage.endpoint)
        .order_by(func.count(ApiUsage.id).desc())
        .all()
    )
    recent = (
        db.session.query(ApiUsage, User.email)
        .outerjoin(User, User.id == ApiUsage.user_id)
        .order_by(ApiUsage.created_at.desc())
        .limit(40)
        .all()
    )
    return jsonify(
        totals={
            "users": User.query.count(),
            "plans": MotionPlan.query.count(),
            "requests": ApiUsage.query.count(),
        },
        by_endpoint=[
            {"method": method, "endpoint": endpoint, "count": count}
            for method, endpoint, count in by_endpoint
        ],
        recent=[
            {
                "id": row.id,
                "email": email,
                "method": row.method,
                "endpoint": row.endpoint,
                "status_code": row.status_code,
                "created_at": row.created_at.isoformat(),
            }
            for row, email in recent
        ],
    )
