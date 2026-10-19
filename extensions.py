"""Flask extensions, created here and initialised in app.create_app().

Keeping them in their own module avoids circular imports between
app.py, models.py and the route blueprints.
"""

from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Naming convention so Alembic gives constraints stable names (needed for SQLite migrations)
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()
migrate = Migrate()
