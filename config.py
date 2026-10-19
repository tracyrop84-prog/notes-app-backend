import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask signs the session cookie with this key. Set SECRET_KEY in production.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Fast hashing keeps the test suite quick
    BCRYPT_LOG_ROUNDS = 4
