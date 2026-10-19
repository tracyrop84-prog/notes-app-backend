from flask import Flask

from config import Config
from extensions import bcrypt, db, migrate
from routes import auth_bp, notes_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.sort_keys = False

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Import models so Flask-Migrate can see them when generating migrations
    import models  # noqa: F401

    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)

    @app.get("/")
    def index():
        return {"message": "Notes API is running"}, 200

    @app.errorhandler(404)
    def not_found(error):
        return {"errors": ["Resource not found."]}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return {"errors": ["Method not allowed."]}, 405

    return app


app = create_app()


if __name__ == "__main__":
    # Port 5555 matches the proxy in the provided React client
    app.run(port=5555, debug=True)
