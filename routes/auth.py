"""Session-based authentication: signup, login, check_session, logout.

Response shapes match the provided React client (client-with-sessions):
success returns the user {"id", "username"}; failure returns {"errors": [...]}.
"""

from flask import Blueprint, request, session
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User
from schemas import user_schema

auth_bp = Blueprint("auth", __name__)


def current_user():
    """Return the logged-in User, or None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    confirmation = data.get("password_confirmation")

    errors = []
    if not username:
        errors.append("Username is required.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    # The client always sends password_confirmation; Postman requests may leave it out
    if confirmation is not None and confirmation != password:
        errors.append("Password confirmation does not match.")
    if username and User.query.filter_by(username=username).first():
        errors.append("Username is already taken.")
    if errors:
        return {"errors": errors}, 422

    try:
        user = User(username=username)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return {"errors": [str(error)]}, 422
    except IntegrityError:
        # Two signups racing for the same username
        db.session.rollback()
        return {"errors": ["Username is already taken."]}, 422

    session["user_id"] = user.id
    return user_schema.dump(user), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    # Same message for unknown user and wrong password, so usernames can't be probed
    if not user or not user.authenticate(password):
        return {"errors": ["Invalid username or password."]}, 401

    session["user_id"] = user.id
    return user_schema.dump(user), 200


@auth_bp.get("/check_session")
def check_session():
    user = current_user()
    if not user:
        return {}, 401
    return user_schema.dump(user), 200


@auth_bp.delete("/logout")
def logout():
    if session.get("user_id") is None:
        return {"errors": ["You are not logged in."]}, 401
    session.pop("user_id", None)
    return {}, 204
