"""Marshmallow schemas that turn model objects into JSON-ready dicts."""

from marshmallow import Schema, fields


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    # The password hash is deliberately not included


class NoteSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    content = fields.Str()
    user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


user_schema = UserSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)
