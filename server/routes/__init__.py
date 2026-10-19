from routes.exercises import exercises_bp
from routes.workout_exercises import workout_exercises_bp
from routes.workouts import workouts_bp

ALL_BLUEPRINTS = (workouts_bp, exercises_bp, workout_exercises_bp)
