import os
import sys
from datetime import date

import pytest

# Make server/ importable when pytest runs from the project root or server/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from models import Exercise, Workout, db  # noqa: E402


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def workout(app):
    workout = Workout(date=date(2026, 10, 1), duration_minutes=45, notes="Test workout")
    db.session.add(workout)
    db.session.commit()
    return workout


@pytest.fixture
def exercise(app):
    exercise = Exercise(name="Squat", category="strength", equipment_needed=True)
    db.session.add(exercise)
    db.session.commit()
    return exercise
