from flask import Blueprint

from models import Workout, db
from routes.helpers import load_json, not_found
from schemas import workout_detail_schema, workout_schema, workouts_schema

workouts_bp = Blueprint("workouts", __name__, url_prefix="/workouts")


@workouts_bp.get("")
def list_workouts():
    workouts = Workout.query.order_by(Workout.date.desc(), Workout.id.desc()).all()
    return workouts_schema.dump(workouts), 200


@workouts_bp.get("/<int:workout_id>")
def get_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return not_found("Workout", workout_id)
    return workout_detail_schema.dump(workout), 200


@workouts_bp.post("")
def create_workout():
    data, error = load_json(workout_schema)
    if error:
        return error

    try:
        workout = Workout(**data)
    except ValueError as err:
        return {"errors": {"workout": [str(err)]}}, 400

    db.session.add(workout)
    db.session.commit()
    return workout_schema.dump(workout), 201


@workouts_bp.delete("/<int:workout_id>")
def delete_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return not_found("Workout", workout_id)

    # cascade="all, delete-orphan" also removes this workout's WorkoutExercises
    db.session.delete(workout)
    db.session.commit()
    return {}, 204
