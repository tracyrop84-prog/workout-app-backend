from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from models import Exercise, db
from routes.helpers import load_json, not_found
from schemas import exercise_detail_schema, exercise_schema, exercises_schema

exercises_bp = Blueprint("exercises", __name__, url_prefix="/exercises")


@exercises_bp.get("")
def list_exercises():
    exercises = Exercise.query.order_by(Exercise.name).all()
    return exercises_schema.dump(exercises), 200


@exercises_bp.get("/<int:exercise_id>")
def get_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return not_found("Exercise", exercise_id)
    return exercise_detail_schema.dump(exercise), 200


@exercises_bp.post("")
def create_exercise():
    data, error = load_json(exercise_schema)
    if error:
        return error

    try:
        exercise = Exercise(**data)
        db.session.add(exercise)
        db.session.commit()
    except ValueError as err:
        db.session.rollback()
        return {"errors": {"exercise": [str(err)]}}, 400
    except IntegrityError:
        # The unique constraint on name
        db.session.rollback()
        return {"errors": {"name": [f"An exercise named '{data['name']}' already exists."]}}, 409

    return exercise_schema.dump(exercise), 201


@exercises_bp.delete("/<int:exercise_id>")
def delete_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return not_found("Exercise", exercise_id)

    # cascade="all, delete-orphan" also removes this exercise's WorkoutExercises
    db.session.delete(exercise)
    db.session.commit()
    return {}, 204
