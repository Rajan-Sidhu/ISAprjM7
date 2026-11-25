from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify(status="ok", service="motion-fighter-api")


@health_bp.get("/docs")
def docs():
    return jsonify(
        service="Motion Fighter API",
        note="Passwords travel only to this API. The embedding model runs in this process. No AI provider key is sent to the browser.",
        authentication="HttpOnly JWT cookie named access_token. Send requests with credentials included.",
        endpoints=[
            {"method": "POST", "path": "/api/auth/register", "auth": "public", "body": {"email": "string", "password": "string"}},
            {"method": "POST", "path": "/api/auth/login", "auth": "public", "body": {"email": "string", "password": "string"}},
            {"method": "POST", "path": "/api/auth/logout", "auth": "cookie"},
            {"method": "GET", "path": "/api/auth/me", "auth": "user"},
            {"method": "POST", "path": "/api/plans", "auth": "user", "body": {"prompt": "string"}, "ai": True},
            {"method": "GET", "path": "/api/plans", "auth": "user"},
            {"method": "GET", "path": "/api/plans/<id>", "auth": "owner or admin"},
            {"method": "DELETE", "path": "/api/plans/<id>", "auth": "owner or admin"},
            {"method": "GET", "path": "/api/admin/users", "auth": "admin"},
            {"method": "GET", "path": "/api/admin/stats", "auth": "admin"},
            {"method": "GET", "path": "/api/model", "auth": "public"},
            {"method": "GET", "path": "/api/health", "auth": "public"},
        ],
    )
