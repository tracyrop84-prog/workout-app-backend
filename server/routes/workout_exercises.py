from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from models import Exercise, Workout, WorkoutExercise, db
from routes.helpers import load_json, not_found
from schemas import workout_exercise_schema

workout_exercises_bp = Blueprint("workout_exercises", __name__)


@workout_exercises_bp.post("/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises")
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return not_found("Workout", workout_id)
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return not_found("Exercise", exercise_id)

    data, error = load_json(workout_exercise_schema)
    if error:
        return error

    try:
        workout_exercise = WorkoutExercise(workout=workout, exercise=exercise, **data)
        db.session.add(workout_exercise)
        db.session.commit()
    except ValueError as err:
        db.session.rollback()
        return {"errors": {"workout_exercise": [str(err)]}}, 400
    except IntegrityError:
        # The unique (workout_id, exercise_id) constraint
        db.session.rollback()
        return {"errors": {"exercise_id": [
            f"Exercise {exercise_id} is already in workout {workout_id}."
        ]}}, 409

    return workout_exercise_schema.dump(workout_exercise), 201
