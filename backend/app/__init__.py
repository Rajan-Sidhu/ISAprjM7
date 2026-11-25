from pathlib import Path

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.exceptions import HTTPException

from .ai.planner import load_model, model_status
from .config import Config
from .database import db
from .models import ApiUsage
from .seed import seed_demo_users


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

    if testing:
        from sqlalchemy.pool import StaticPool

        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
        app.config["COOKIE_SECURE"] = False

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    # The default SQLite file lives in instance/, which Flask only creates
    # after the app exists. Resolve a relative sqlite path against that folder.
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("sqlite:///") and not uri.startswith("sqlite:////"):
        relative = uri.removeprefix("sqlite:///")
        if relative != ":memory:" and not Path(relative).is_absolute():
            absolute = Path(app.instance_path) / Path(relative).name
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{absolute}"

    db.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CLIENT_ORIGINS"]}},
        supports_credentials=True,
    )

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.health import health_bp
    from .routes.plans import plans_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(plans_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(health_bp, url_prefix="/api")

    @app.errorhandler(HTTPException)
    def json_error(error):
        return jsonify(error=error.description), error.code

    @app.after_request
    def record_usage(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.path.startswith("/api/") and request.method != "OPTIONS":
            try:
                db.session.add(
                    ApiUsage(
                        user_id=getattr(g, "user_id", None),
                        endpoint=request.path,
                        method=request.method,
                        status_code=response.status_code,
                    )
                )
                db.session.commit()
            except Exception:
                db.session.rollback()
        return response

    with app.app_context():
        db.create_all()
        db.session.execute(text("SELECT 1"))
        seed_demo_users()
        if not testing:
            try:
                load_model(app.config["MODEL_CACHE"])
            except Exception as exc:
                app.config["MODEL_LOAD_ERROR"] = str(exc)
                app.logger.exception("Local model failed to load")

    @app.get("/api/model")
    def model_info():
        status = model_status(app.config["MODEL_CACHE"])
        status["load_error"] = app.config.get("MODEL_LOAD_ERROR")
        return jsonify(status)

    return app
