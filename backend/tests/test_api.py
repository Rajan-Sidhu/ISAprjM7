import json
import re

import numpy as np
import pytest

from app import create_app
from app.ai import planner
from app.ai.primitives import PRIMITIVES
from app.models import User

_IDS = [item["id"] for item in PRIMITIVES]


def fake_embed(texts):
    vectors = []
    for text in texts:
        vector = np.zeros(len(_IDS), dtype=np.float32)
        lowered = text.lower()
        hits = [
            index
            for index, name in enumerate(_IDS)
            if re.search(rf"\b{name}\b", lowered)
        ]
        if hits:
            for index in hits:
                vector[index] = 1.0
        else:
            vector[:] = 0.01
        vectors.append(vector)
    return vectors


@pytest.fixture
def client(monkeypatch):
    planner.clear_model_cache()
    monkeypatch.setattr(planner, "embed_texts", fake_embed)
    app = create_app(testing=True)
    app.config["MODEL_LOAD_ERROR"] = None
    with app.app_context():
        planner._primitive_vectors = None
    with app.test_client() as test_client:
        yield test_client
    planner.clear_model_cache()


def login(client, email, password):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )


def test_demo_login_and_hashed_password(client):
    response = login(client, "john@john.com", "123")
    assert response.status_code == 200
    body = response.get_json()
    assert body["user"]["email"] == "john@john.com"
    assert body["user"]["role"] == "user"
    assert "access_token" in response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in response.headers.get("Set-Cookie", "")

    with client.application.app_context():
        user = User.query.filter_by(email="john@john.com").one()
        assert user.password_hash != "123"
        assert user.password_hash.startswith("$2")


def test_register_login_and_reject_bad_password(client):
    created = client.post(
        "/api/auth/register",
        json={"email": "new@student.com", "password": "secret", "role": "admin"},
    )
    assert created.status_code == 201
    assert created.get_json()["user"]["role"] == "user"

    duplicate = client.post(
        "/api/auth/register",
        json={"email": "new@student.com", "password": "secret"},
    )
    assert duplicate.status_code == 409

    bad = login(client, "new@student.com", "wrong")
    assert bad.status_code == 401

    client.post("/api/auth/logout")
    me = client.get("/api/auth/me")
    assert me.status_code == 401

    again = login(client, "new@student.com", "secret")
    assert again.status_code == 200
    assert again.get_json()["user"]["role"] == "user"


def test_user_cannot_open_admin_and_admin_can(client):
    login(client, "john@john.com", "123")
    forbidden = client.get("/api/admin/users")
    assert forbidden.status_code == 403

    client.post("/api/auth/logout")
    login(client, "admin@admin.com", "111")
    allowed = client.get("/api/admin/users")
    assert allowed.status_code == 200
    emails = {row["email"] for row in allowed.get_json()["users"]}
    assert "john@john.com" in emails
    assert "admin@admin.com" in emails

    stats = client.get("/api/admin/stats")
    assert stats.status_code == 200
    assert stats.get_json()["totals"]["users"] >= 2


def test_ai_plan_is_saved_and_isolated(client):
    login(client, "john@john.com", "123")
    created = client.post(
        "/api/plans",
        json={"prompt": "wave hello, then pick up the block"},
    )
    assert created.status_code == 201
    plan = created.get_json()["plan"]
    assert [match["primitive_id"] for match in plan["matches"]] == ["wave", "pick"]
    assert plan["model_name"] == "google/videoprism-lvt-base-f16r288"
    assert any(frame["label"] == "Raise the arm" for frame in plan["frames"])

    listed = client.get("/api/plans")
    assert listed.status_code == 200
    assert len(listed.get_json()["plans"]) == 1

    client.post("/api/auth/logout")
    login(client, "admin@admin.com", "111")
    hidden = client.get("/api/plans")
    assert hidden.get_json()["plans"] == []

    missing = client.delete(f"/api/plans/{plan['id']}")
    # Admin may delete. A second user who is not admin is covered below.
    assert missing.status_code == 200


def test_other_user_cannot_delete_a_plan(client):
    login(client, "john@john.com", "123")
    created = client.post("/api/plans", json={"prompt": "bow please"})
    plan_id = created.get_json()["plan"]["id"]
    client.post("/api/auth/logout")

    client.post(
        "/api/auth/register",
        json={"email": "other@student.com", "password": "secret"},
    )
    denied = client.delete(f"/api/plans/{plan_id}")
    assert denied.status_code == 404


def test_usage_is_recorded_for_the_signed_in_user(client):
    login(client, "john@john.com", "123")
    client.get("/api/auth/me")
    me = client.get("/api/auth/me")
    recent = me.get_json()["user"]["recent_usage"]
    assert recent
    assert all(row["endpoint"].startswith("/api/") for row in recent)


def test_mimic_requires_login(client):
    response = client.post("/api/plans/mimic", json={"frames": ["x"] * 8})
    assert response.status_code == 401


def test_mimic_ranks_a_punch_vector():
    from app.ai.planner import mimic_motion

    labels = ["punch", "block", "dodge", "idle"]

    def text_embedder(texts):
        vectors = []
        for text in texts:
            vector = np.zeros(len(labels), dtype=np.float32)
            for index, name in enumerate(labels):
                if name in text:
                    vector[index] = 1.0
            vectors.append(vector)
        return vectors

    def video_embedder(_clip):
        return np.array([1, 0, 0, 0], dtype=np.float32)

    plan = mimic_motion(
        np.zeros((8, 8, 8, 3), dtype=np.float32),
        video_embedder=video_embedder,
        text_embedder=text_embedder,
    )
    assert plan["matches"][0]["primitive_id"] == "punch"
    assert any(frame["label"] == "Punch forward" for frame in plan["frames"])


def test_split_clauses():
    assert planner.split_clauses("wave hello, then pick up the block") == [
        "wave hello",
        "pick up the block",
    ]
    assert planner.split_clauses("wave hello") == ["wave hello"]
