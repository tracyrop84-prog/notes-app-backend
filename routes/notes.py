"""CRUD routes for the Note resource.

Every route requires a logged-in user, and users can only see or change
their own notes.
"""

from flask import Blueprint, request, session

from extensions import db
from models import Note
from schemas import note_schema, notes_schema

notes_bp = Blueprint("notes", __name__, url_prefix="/notes")

MAX_PER_PAGE = 50


@notes_bp.before_request
def require_login():
    """Block every /notes request unless the user is logged in."""
    if session.get("user_id") is None:
        return {"errors": ["You must be logged in to do that."]}, 401


def get_owned_note(note_id):
    """
    Return (note, None) if the current user owns the note,
    otherwise (None, error_response).
    """
    note = db.session.get(Note, note_id)
    if note is None:
        return None, ({"errors": [f"Note {note_id} not found."]}, 404)
    if note.user_id != session["user_id"]:
        return None, ({"errors": ["You do not have permission to access this note."]}, 403)
    return note, None


def parse_positive_int(value, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


@notes_bp.get("")
def list_notes():
    """GET /notes?page=1&per_page=10 - the current user's notes, newest first."""
    page = parse_positive_int(request.args.get("page"), 1)
    per_page = min(parse_positive_int(request.args.get("per_page"), 10), MAX_PER_PAGE)

    query = (
        db.select(Note)
        .filter_by(user_id=session["user_id"])
        .order_by(Note.created_at.desc(), Note.id.desc())
    )
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)

    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "items": notes_schema.dump(pagination.items),
    }, 200


@notes_bp.get("/<int:note_id>")
def get_note(note_id):
    note, error = get_owned_note(note_id)
    if error:
        return error
    return note_schema.dump(note), 200


@notes_bp.post("")
def create_note():
    data = request.get_json(silent=True) or {}
    try:
        # user_id always comes from the session, never from the request body
        note = Note(
            title=data.get("title"),
            content=data.get("content"),
            user_id=session["user_id"],
        )
    except ValueError as error:
        return {"errors": [str(error)]}, 422

    db.session.add(note)
    db.session.commit()
    return note_schema.dump(note), 201


@notes_bp.patch("/<int:note_id>")
def update_note(note_id):
    note, error = get_owned_note(note_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    editable = {key: data[key] for key in ("title", "content") if key in data}
    if not editable:
        return {"errors": ["Send at least one of: title, content."]}, 422

    try:
        for key, value in editable.items():
            setattr(note, key, value)
    except ValueError as error:
        db.session.rollback()
        return {"errors": [str(error)]}, 422

    db.session.commit()
    return note_schema.dump(note), 200


@notes_bp.delete("/<int:note_id>")
def delete_note(note_id):
    note, error = get_owned_note(note_id)
    if error:
        return error

    db.session.delete(note)
    db.session.commit()
    return {}, 204
