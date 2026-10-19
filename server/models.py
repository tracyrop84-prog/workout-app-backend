from datetime import date as date_type

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, MetaData, UniqueConstraint, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

# Naming convention gives constraints stable names, which SQLite migrations need
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

db = SQLAlchemy(metadata=metadata)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless this is switched on for each connection."""
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


EXERCISE_CATEGORIES = ("strength", "cardio", "flexibility", "balance", "core")


class Exercise(db.Model):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name_not_blank"),
        CheckConstraint(
            "category IN ('strength', 'cardio', 'flexibility', 'balance', 'core')",
            name="valid_category",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan"
    )
    # Exercise has many Workouts through WorkoutExercises
    workouts = association_proxy("workout_exercises", "workout")

    @validates("name")
    def validate_name(self, key, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Exercise name is required.")
        name = name.strip()
        if len(name) > 100:
            raise ValueError("Exercise name must be 100 characters or fewer.")
        return name

    @validates("category")
    def validate_category(self, key, category):
        category = (category or "").strip().lower()
        if category not in EXERCISE_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(EXERCISE_CATEGORIES)}.")
        return category

    def __repr__(self):
        return f"<Exercise {self.id} {self.name} ({self.category})>"


class Workout(db.Model):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="workout", cascade="all, delete-orphan"
    )
    # Workout has many Exercises through WorkoutExercises
    exercises = association_proxy("workout_exercises", "exercise")

    @validates("date")
    def validate_date(self, key, value):
        if not isinstance(value, date_type):
            raise ValueError("Date must be a valid date (YYYY-MM-DD).")
        return value

    @validates("duration_minutes")
    def validate_duration(self, key, minutes):
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise ValueError("Duration must be a whole number of minutes.")
        if not 1 <= minutes <= 600:
            raise ValueError("Duration must be between 1 and 600 minutes.")
        return minutes

    @validates("notes")
    def validate_notes(self, key, notes):
        if notes is not None and len(notes) > 1000:
            raise ValueError("Notes must be 1000 characters or fewer.")
        return notes

    def __repr__(self):
        return f"<Workout {self.id} {self.date} {self.duration_minutes}min>"


class WorkoutExercise(db.Model):
    """Join table: one exercise inside one workout, with its sets/reps/duration."""

    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("workout_id", "exercise_id", name="uq_workout_exercise_pair"),
        CheckConstraint("reps IS NULL OR reps > 0", name="reps_positive"),
        CheckConstraint("sets IS NULL OR sets > 0", name="sets_positive"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0", name="duration_seconds_positive"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id = db.Column(
        db.Integer, db.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_positive_numbers(self, key, value):
        if value is None:
            return value
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{key} must be a positive whole number.")
        return value

    def __repr__(self):
        return (f"<WorkoutExercise workout={self.workout_id} exercise={self.exercise_id} "
                f"sets={self.sets} reps={self.reps} secs={self.duration_seconds}>")
