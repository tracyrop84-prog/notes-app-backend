"""Reset the database and fill it with example users and notes.

Run with:  python seed.py
Every seeded user has the password "password123".
"""

import random

from faker import Faker

from app import app
from extensions import db
from models import Note, User

fake = Faker()
SEED_PASSWORD = "password123"
USERNAMES = ["alice", "brian", "wanjiru"]


def seed():
    # Clear old data (notes first, because they reference users)
    Note.query.delete()
    User.query.delete()
    db.session.commit()

    users = []
    for username in USERNAMES:
        user = User(username=username)
        user.password_hash = SEED_PASSWORD
        users.append(user)
    db.session.add_all(users)
    db.session.commit()

    notes = []
    for user in users:
        for _ in range(random.randint(6, 12)):
            notes.append(Note(
                title=fake.sentence(nb_words=4).rstrip("."),
                content=fake.paragraph(nb_sentences=3),
                user_id=user.id,
            ))
    db.session.add_all(notes)
    db.session.commit()

    print(f"Seeded {len(users)} users and {len(notes)} notes.")
    print(f"Log in as any of {', '.join(USERNAMES)} with password '{SEED_PASSWORD}'.")


if __name__ == "__main__":
    with app.app_context():
        seed()
