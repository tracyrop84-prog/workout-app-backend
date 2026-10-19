from flask import Flask
from flask_migrate import Migrate

from models import db
from routes import ALL_BLUEPRINTS


def create_app(config=None):
    """Build the Flask app. Tests pass their own config (e.g. an in-memory database)."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config:
        app.config.update(config)
    app.json.sort_keys = False

    db.init_app(app)
    Migrate(app, db)

    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)

    @app.get("/")
    def index():
        return {"message": "Workout API is running"}, 200

    @app.errorhandler(404)
    def not_found(error):
        return {"errors": {"url": ["Resource not found."]}}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return {"errors": {"method": ["Method not allowed."]}}, 405

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
