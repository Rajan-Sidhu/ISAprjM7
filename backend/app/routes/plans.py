import json

from flask import Blueprint, g, jsonify, request

from ..ai.planner import MODEL_NAME, decode_clip, mimic_motion, plan_motion
from ..auth_utils import login_required
from ..database import db
from ..models import MotionPlan

plans_bp = Blueprint("plans", __name__)


def plan_payload(row):
    body = json.loads(row.plan_json)
    return {
        "id": row.id,
        "prompt": row.prompt,
        "summary": row.summary,
        "model_name": row.model_name,
        "created_at": row.created_at.isoformat(),
        "matches": body.get("matches", []),
        "frames": body.get("frames", []),
        "servos": body.get("servos", []),
        "model": body.get("model", {}),
    }


@plans_bp.post("/plans")
@login_required
def create_plan():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt") or "").strip()
    if not prompt:
        return jsonify(error="Describe the motion you want"), 400
    if len(prompt) > 500:
        return jsonify(error="Keep the description under 500 characters"), 400

    try:
        plan = plan_motion(prompt)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 503

    row = MotionPlan(
        user_id=g.user.id,
        prompt=plan["prompt"],
        summary=plan["summary"],
        plan_json=json.dumps(plan),
        model_name=MODEL_NAME,
    )
    db.session.add(row)
    db.session.commit()
    return jsonify(plan=plan_payload(row)), 201


@plans_bp.post("/plans/mimic")
@login_required
def mimic_plan():
    data = request.get_json(silent=True) or {}
    try:
        clip = decode_clip(data.get("frames"))
        plan = mimic_motion(clip)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 503

    row = MotionPlan(
        user_id=g.user.id,
        prompt=plan["prompt"],
        summary=plan["summary"],
        plan_json=json.dumps(plan),
        model_name=MODEL_NAME,
    )
    db.session.add(row)
    db.session.commit()
    return jsonify(plan=plan_payload(row)), 201


@plans_bp.get("/plans")
@login_required
def list_plans():
    rows = (
        MotionPlan.query.filter_by(user_id=g.user.id)
        .order_by(MotionPlan.created_at.desc())
        .all()
    )
    return jsonify(plans=[plan_payload(row) for row in rows])


@plans_bp.get("/plans/<int:plan_id>")
@login_required
def get_plan(plan_id):
    row = db.session.get(MotionPlan, plan_id)
    if row is None or (row.user_id != g.user.id and g.user.role != "admin"):
        return jsonify(error="Plan not found"), 404
    return jsonify(plan=plan_payload(row))


@plans_bp.delete("/plans/<int:plan_id>")
@login_required
def delete_plan(plan_id):
    row = db.session.get(MotionPlan, plan_id)
    if row is None or (row.user_id != g.user.id and g.user.role != "admin"):
        return jsonify(error="Plan not found"), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify(ok=True)
