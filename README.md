# Notes App – Full Auth Flask Backend

A secure Flask REST API for a personal notes productivity app. Users sign up and log in with **session-based authentication**, then create, read, update, and delete their own notes. Every notes route is protected: you must be logged in, and you can only ever see or change your own notes.

The API is built to work with the provided React client, [`client-with-sessions`](https://github.com/learn-co-curriculum/flask-c10-summative-lab-sessions-and-jwt-clients/tree/main/client-with-sessions), which expects the backend on port **5555**.

## Features

- Sign up, log in, stay logged in on refresh (`/check_session`), and log out
- Passwords hashed with **Flask-Bcrypt**; the hash can never be read back from the model
- Unique usernames, enforced by validation and a database constraint
- Full CRUD for notes, with **pagination** on the index route
- Authorization checks: `401` when logged out, `403` for another user's note
- Database migrations with **Flask-Migrate** and example data from **Faker**
- Automated test suite with **pytest**

## Tech stack

Flask · Flask-SQLAlchemy · Flask-Migrate · Flask-Bcrypt · Marshmallow · Faker · SQLite · pytest

## Project structure

```
notes-app-backend/
├── app.py            # App factory, registers extensions and blueprints
├── config.py         # App, database and test settings
├── extensions.py     # db, bcrypt and migrate instances
├── models.py         # User and Note models with validations
├── schemas.py        # Marshmallow schemas for JSON output
├── routes/
│   ├── auth.py       # /signup, /login, /check_session, /logout
│   └── notes.py      # /notes CRUD + pagination (login required)
├── migrations/       # Flask-Migrate / Alembic migrations
├── seed.py           # Example users and notes
├── tests/
│   └── test_api.py   # pytest suite
└── Pipfile
```

## Installation

Requires Python 3.12 and [pipenv](https://pipenv.pypa.io/).

```bash
git clone https://github.com/<your-username>/notes-app-backend.git
cd notes-app-backend

pipenv install
pipenv shell
```

Create the database and load example data:

```bash
export FLASK_APP=app.py
flask db upgrade
python seed.py
```

`seed.py` creates three users (`alice`, `brian`, `wanjiru`), each with the password `password123` and several notes.

## Running the app

```bash
python app.py
```

The API runs at `http://localhost:5555`. Alternatively, run `flask run --port 5555`.

### Using the React client (optional)

```bash
git clone https://github.com/learn-co-curriculum/flask-c10-summative-lab-sessions-and-jwt-clients.git
cd flask-c10-summative-lab-sessions-and-jwt-clients/client-with-sessions
npm install
npm start
```

The client proxies its requests to `http://localhost:5555`, so keep the Flask server running.

### Running tests

```bash
pytest
```

## API endpoints

All requests and responses use JSON. Errors are returned as `{"errors": ["message", ...]}`.

### Authentication

| Method | Endpoint         | Description | Success | Errors |
|--------|------------------|-------------|---------|--------|
| POST   | `/signup`        | Create an account and log in | `201` user | `422` missing fields, short password, mismatched confirmation, or taken username |
| POST   | `/login`         | Log in with username and password | `200` user | `401` invalid credentials |
| GET    | `/check_session` | Return the logged-in user, so users stay logged in on refresh | `200` user | `401` `{}` when logged out |
| DELETE | `/logout`        | Log out (clears `user_id` from the session) | `204` | `401` not logged in |

**POST /signup** body:
```json
{ "username": "tracy", "password": "secret123", "password_confirmation": "secret123" }
```
Response (`201`):
```json
{ "id": 4, "username": "tracy" }
```

**POST /login** body:
```json
{ "username": "alice", "password": "password123" }
```
Response (`200`):
```json
{ "id": 1, "username": "alice" }
```

### Notes (login required)

Every notes route returns `401` when no one is logged in.

| Method | Endpoint       | Description | Success | Errors |
|--------|----------------|-------------|---------|--------|
| GET    | `/notes`       | List your notes, newest first, paginated | `200` | `401` |
| GET    | `/notes/<id>`  | Get one of your notes | `200` | `403` not yours, `404` not found |
| POST   | `/notes`       | Create a note | `201` | `422` missing title or content |
| PATCH  | `/notes/<id>`  | Update a note's title and/or content | `200` | `403`, `404`, `422` |
| DELETE | `/notes/<id>`  | Delete a note | `204` | `403`, `404` |

**GET /notes?page=1&per_page=10**

Query parameters:
- `page`: page number (default `1`)
- `per_page`: notes per page (default `10`, maximum `50`)

Response (`200`):
```json
{
  "page": 1,
  "per_page": 10,
  "total": 23,
  "pages": 3,
  "items": [
    {
      "id": 8,
      "title": "Shopping list",
      "content": "Milk, eggs, bread",
      "user_id": 1,
      "created_at": "2026-10-19T06:54:32.989694",
      "updated_at": "2026-10-19T06:54:32.989695"
    }
  ]
}
```

**POST /notes** body:
```json
{ "title": "Shopping list", "content": "Milk, eggs, bread" }
```
The note's owner always comes from the session. A `user_id` sent in the body is ignored.

**PATCH /notes/8** body (any of the fields):
```json
{ "title": "Updated title" }
```

## Security notes

- Only the bcrypt hash of each password is stored in the database.
- The session cookie is signed with `SECRET_KEY`. Set your own in production: `export SECRET_KEY="a-long-random-string"`.
- Users can never read, change, or delete notes that belong to someone else.
