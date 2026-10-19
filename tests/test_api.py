import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402
from extensions import db  # noqa: E402
from models import Note, User  # noqa: E402


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="alice", password="secret123"):
    return client.post("/signup", json={
        "username": username,
        "password": password,
        "password_confirmation": password,
    })


# ---------- User model ----------

def test_password_is_hashed(app):
    user = User(username="bob")
    user.password_hash = "secret123"
    db.session.add(user)
    db.session.commit()
    assert user._password_hash != "secret123"
    assert user.authenticate("secret123")
    assert not user.authenticate("wrong")


def test_password_hash_cannot_be_read(app):
    user = User(username="bob")
    user.password_hash = "secret123"
    with pytest.raises(AttributeError):
        user.password_hash


# ---------- Signup ----------

def test_signup_creates_user_and_logs_in(client):
    response = signup(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["username"] == "alice"
    assert "_password_hash" not in body
    assert client.get("/check_session").status_code == 200


def test_signup_duplicate_username(client):
    signup(client)
    response = signup(client)
    assert response.status_code == 422
    assert "Username is already taken." in response.get_json()["errors"]


def test_signup_password_mismatch(client):
    response = client.post("/signup", json={
        "username": "alice", "password": "secret123", "password_confirmation": "nope",
    })
    assert response.status_code == 422


def test_signup_missing_fields(client):
    response = client.post("/signup", json={})
    assert response.status_code == 422
    assert len(response.get_json()["errors"]) >= 2


# ---------- Login / check_session / logout ----------

def test_login_success(client):
    signup(client)
    client.delete("/logout")
    response = client.post("/login", json={"username": "alice", "password": "secret123"})
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


def test_login_wrong_password(client):
    signup(client)
    client.delete("/logout")
    response = client.post("/login", json={"username": "alice", "password": "bad"})
    assert response.status_code == 401
    assert "errors" in response.get_json()


def test_check_session_logged_out(client):
    response = client.get("/check_session")
    assert response.status_code == 401
    assert response.get_json() == {}


def test_logout(client):
    signup(client)
    assert client.delete("/logout").status_code == 204
    assert client.get("/check_session").status_code == 401


def test_logout_when_not_logged_in(client):
    assert client.delete("/logout").status_code == 401


# ---------- Notes: protection ----------

@pytest.mark.parametrize("method, path", [
    ("get", "/notes"),
    ("post", "/notes"),
    ("get", "/notes/1"),
    ("patch", "/notes/1"),
    ("delete", "/notes/1"),
])
def test_notes_require_login(client, method, path):
    response = getattr(client, method)(path, json={})
    assert response.status_code == 401


def test_users_cannot_touch_each_others_notes(client):
    signup(client, "alice")
    note_id = client.post("/notes", json={"title": "Private", "content": "Mine"}).get_json()["id"]
    client.delete("/logout")

    signup(client, "bob")
    assert client.get(f"/notes/{note_id}").status_code == 403
    assert client.patch(f"/notes/{note_id}", json={"title": "Hacked"}).status_code == 403
    assert client.delete(f"/notes/{note_id}").status_code == 403
    assert client.get("/notes").get_json()["total"] == 0


# ---------- Notes: CRUD ----------

def test_create_note(client):
    signup(client)
    response = client.post("/notes", json={"title": "Groceries", "content": "Milk, eggs"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Groceries"
    assert body["user_id"] is not None


def test_create_note_ignores_user_id_in_body(client):
    signup(client, "alice")
    alice_id = client.get("/check_session").get_json()["id"]
    response = client.post("/notes", json={"title": "T", "content": "C", "user_id": 999})
    assert response.get_json()["user_id"] == alice_id


def test_create_note_validation(client):
    signup(client)
    response = client.post("/notes", json={"title": "", "content": "x"})
    assert response.status_code == 422


def test_get_single_note(client):
    signup(client)
    note_id = client.post("/notes", json={"title": "A", "content": "B"}).get_json()["id"]
    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "A"


def test_update_note(client):
    signup(client)
    note_id = client.post("/notes", json={"title": "Old", "content": "Body"}).get_json()["id"]
    response = client.patch(f"/notes/{note_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.get_json()["title"] == "New"
    assert response.get_json()["content"] == "Body"


def test_update_note_validation(client):
    signup(client)
    note_id = client.post("/notes", json={"title": "Old", "content": "Body"}).get_json()["id"]
    assert client.patch(f"/notes/{note_id}", json={}).status_code == 422
    assert client.patch(f"/notes/{note_id}", json={"content": "  "}).status_code == 422


def test_delete_note(client):
    signup(client)
    note_id = client.post("/notes", json={"title": "Bye", "content": "Soon"}).get_json()["id"]
    assert client.delete(f"/notes/{note_id}").status_code == 204
    assert client.get(f"/notes/{note_id}").status_code == 404


def test_missing_note_returns_404(client):
    signup(client)
    assert client.get("/notes/999").status_code == 404


# ---------- Notes: pagination ----------

def test_pagination(client):
    signup(client)
    for i in range(12):
        client.post("/notes", json={"title": f"Note {i}", "content": "x"})

    first = client.get("/notes?page=1&per_page=5").get_json()
    assert first["total"] == 12
    assert first["pages"] == 3
    assert len(first["items"]) == 5
    assert first["items"][0]["title"] == "Note 11"  # newest first

    last = client.get("/notes?page=3&per_page=5").get_json()
    assert len(last["items"]) == 2

    beyond = client.get("/notes?page=9&per_page=5").get_json()
    assert beyond["items"] == []


def test_pagination_bad_params_use_defaults(client):
    signup(client)
    body = client.get("/notes?page=abc&per_page=-3").get_json()
    assert body["page"] == 1
    assert body["per_page"] == 10
