from datetime import datetime, timezone

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from extensions import bcrypt, db


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Only the bcrypt hash is stored, never the plain-text password
    _password_hash = db.Column(db.String(128), nullable=False)

    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @hybrid_property
    def password_hash(self):
        # Reading the hash back out is never allowed
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates("username")
    def validate_username(self, key, username):
        username = (username or "").strip()
        if not username:
            raise ValueError("Username is required.")
        if len(username) > 80:
            raise ValueError("Username must be 80 characters or fewer.")
        return username

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="notes")

    @validates("title")
    def validate_title(self, key, title):
        title = (title or "").strip()
        if not title:
            raise ValueError("Title is required.")
        if len(title) > 120:
            raise ValueError("Title must be 120 characters or fewer.")
        return title

    @validates("content")
    def validate_content(self, key, content):
        content = (content or "").strip()
        if not content:
            raise ValueError("Content is required.")
        return content

    def __repr__(self):
        return f"<Note {self.id} {self.title!r} user={self.user_id}>"
