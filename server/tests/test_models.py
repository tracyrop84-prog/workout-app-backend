"""Model validations, table constraints and relationships."""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import Exercise, Workout, WorkoutExercise, db


# ---------- Model validations ----------

def test_exercise_name_required(app):
    with pytest.raises(ValueError):
        Exercise(name="   ", category="strength")


def test_exercise_category_must_be_allowed(app):
    with pytest.raises(ValueError):
        Exercise(name="Yoga Flow", category="dancing")


def test_exercise_category_is_normalised(app):
    assert Exercise(name="Run", category=" Cardio ").category == "cardio"


def test_workout_duration_must_be_in_range(app):
    with pytest.raises(ValueError):
        Workout(date=date(2026, 1, 1), duration_minutes=0)
    with pytest.raises(ValueError):
        Workout(date=date(2026, 1, 1), duration_minutes=601)


def test_workout_date_must_be_a_date(app):
    with pytest.raises(ValueError):
        Workout(date="yesterday", duration_minutes=30)


def test_workout_exercise_numbers_must_be_positive(app):
    with pytest.raises(ValueError):
        WorkoutExercise(sets=-1, reps=10)


# ---------- Table constraints (enforced by the database itself) ----------

def test_exercise_name_unique_constraint(app, exercise):
    db.session.add(Exercise(name="Squat", category="strength"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_workout_duration_check_constraint(app):
    # Raw SQL skips the Python validators, so this proves the database rule exists
    with pytest.raises(IntegrityError):
        db.session.execute(text(
            "INSERT INTO workouts (date, duration_minutes) VALUES ('2026-01-01', -5)"
        ))
    db.session.rollback()


def test_exercise_category_check_constraint(app):
    with pytest.raises(IntegrityError):
        db.session.execute(text(
            "INSERT INTO exercises (name, category, equipment_needed) VALUES ('X', 'dancing', 0)"
        ))
    db.session.rollback()


def test_workout_exercise_pair_unique_constraint(app, workout, exercise):
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=1, reps=1))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_reps_check_constraint(app, workout, exercise):
    with pytest.raises(IntegrityError):
        db.session.execute(text(
            "INSERT INTO workout_exercises (workout_id, exercise_id, reps) "
            f"VALUES ({workout.id}, {exercise.id}, 0)"
        ))
    db.session.rollback()


# ---------- Relationships ----------

def test_has_many_through(app, workout, exercise):
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()
    assert list(workout.exercises) == [exercise]
    assert list(exercise.workouts) == [workout]
    assert workout.workout_exercises[0].exercise is exercise


def test_deleting_workout_deletes_its_workout_exercises(app, workout, exercise):
    db.session.add(WorkoutExercise(workout=workout, exercise=exercise, sets=3, reps=10))
    db.session.commit()
    db.session.delete(workout)
    db.session.commit()
    assert WorkoutExercise.query.count() == 0
    assert Exercise.query.count() == 1  # the exercise itself is kept
