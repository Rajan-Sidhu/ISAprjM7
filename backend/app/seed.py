from .auth_utils import hash_password
from .database import db
from .models import User

# Instructor demonstration accounts. Passwords are hashed before insert.
DEMO_USERS = (
    ("john@john.com", "123", "user"),
    ("admin@admin.com", "111", "admin"),
)


def seed_demo_users():
    created = False
    for email, password, role in DEMO_USERS:
        if User.query.filter_by(email=email).first() is None:
            db.session.add(
                User(
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                )
            )
            created = True
    if created:
        db.session.commit()
