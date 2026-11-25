import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _origins(value):
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    JWT_SECRET = os.getenv(
        "JWT_SECRET", "dev-only-change-me-before-any-real-deployment"
    )
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///instance/motionmind.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLIENT_ORIGINS = _origins(
        os.getenv(
            "CLIENT_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
    )
    JWT_COOKIE_NAME = "access_token"
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    # Cross-site cookies (client and API on different domains) need
    # SameSite=None, and browsers only accept that with Secure.
    # Chrome treats http://localhost as a secure context, so local
    # two-port development still works with COOKIE_SECURE=true.
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    MODEL_NAME = "google/videoprism-lvt-base-f16r288"
    MODEL_CACHE = str(BASE_DIR / "models")
    PORT = int(os.getenv("PORT", "5001"))
