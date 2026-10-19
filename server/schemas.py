"""Marshmallow schemas.

Each model has a schema used two ways:
- schema.dump(obj) turns a model into JSON-ready data (serialization)
- schema.load(json) validates incoming JSON before a model is created (deserialization)
"""

from marshmallow import Schema, ValidationError, fields, validate, validates, validates_schema

from models import EXERCISE_CATEGORIES


class ExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category = fields.Str(required=True, validate=validate.OneOf(EXERCISE_CATEGORIES))
    equipment_needed = fields.Bool(load_default=False)

    @validates("name")
    def validate_name(self, value):
        if not value.strip():
            raise ValidationError("Name cannot be blank.")


class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Int(required=True, strict=True, validate=validate.Range(min=1, max=600))
    notes = fields.Str(allow_none=True, validate=validate.Length(max=1000))


class WorkoutExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = fields.Int(strict=True, allow_none=True, validate=validate.Range(min=1))
    sets = fields.Int(strict=True, allow_none=True, validate=validate.Range(min=1))
    duration_seconds = fields.Int(strict=True, allow_none=True, validate=validate.Range(min=1))

    @validates_schema
    def require_sets_reps_or_duration(self, data, **kwargs):
        """Strength-style entries need sets AND reps; timed entries need duration_seconds."""
        has_sets_reps = data.get("sets") is not None and data.get("reps") is not None
        has_duration = data.get("duration_seconds") is not None
        if not (has_sets_reps or has_duration):
            raise ValidationError("Provide both sets and reps, or duration_seconds.")
        if (data.get("sets") is None) != (data.get("reps") is None):
            raise ValidationError("sets and reps must be provided together.")


# ----- Output schemas with nested relationships -----

class WorkoutExerciseWithExerciseSchema(WorkoutExerciseSchema):
    """Used inside a workout: each entry shows which exercise it is."""
    exercise = fields.Nested(ExerciseSchema, dump_only=True)


class WorkoutExerciseWithWorkoutSchema(WorkoutExerciseSchema):
    """Used inside an exercise: each entry shows which workout it belongs to."""
    workout = fields.Nested(WorkoutSchema, dump_only=True)


class WorkoutDetailSchema(WorkoutSchema):
    """GET /workouts/<id>: the workout plus its exercises with sets/reps/duration."""
    workout_exercises = fields.List(fields.Nested(WorkoutExerciseWithExerciseSchema), dump_only=True)


class ExerciseDetailSchema(ExerciseSchema):
    """GET /exercises/<id>: the exercise plus the workouts it appears in."""
    workout_exercises = fields.List(fields.Nested(WorkoutExerciseWithWorkoutSchema), dump_only=True)


exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
exercise_detail_schema = ExerciseDetailSchema()

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_detail_schema = WorkoutDetailSchema()

workout_exercise_schema = WorkoutExerciseWithExerciseSchema()
