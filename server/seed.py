#!/usr/bin/env python3
"""Reset the database and add example data. Safe to run as many times as you like."""

from datetime import date, timedelta

from app import app
from models import Exercise, Workout, WorkoutExercise, db

with app.app_context():
    # Clear old data first (join table first, because it references the other two)
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()
    db.session.commit()

    squat = Exercise(name="Back Squat", category="strength", equipment_needed=True)
    pushup = Exercise(name="Push-Up", category="strength", equipment_needed=False)
    deadlift = Exercise(name="Deadlift", category="strength", equipment_needed=True)
    run = Exercise(name="Treadmill Run", category="cardio", equipment_needed=True)
    jump_rope = Exercise(name="Jump Rope", category="cardio", equipment_needed=True)
    plank = Exercise(name="Plank", category="core", equipment_needed=False)
    stretch = Exercise(name="Hamstring Stretch", category="flexibility", equipment_needed=False)
    exercises = [squat, pushup, deadlift, run, jump_rope, plank, stretch]
    db.session.add_all(exercises)

    today = date.today()
    leg_day = Workout(date=today - timedelta(days=6), duration_minutes=60,
                      notes="Lower body strength. Focus on squat depth.")
    cardio_day = Workout(date=today - timedelta(days=4), duration_minutes=35,
                         notes="Steady-state cardio, moderate pace.")
    full_body = Workout(date=today - timedelta(days=2), duration_minutes=45,
                        notes="Full body circuit.")
    recovery = Workout(date=today, duration_minutes=20, notes=None)
    workouts = [leg_day, cardio_day, full_body, recovery]
    db.session.add_all(workouts)

    workout_exercises = [
        # Strength entries use sets + reps
        WorkoutExercise(workout=leg_day, exercise=squat, sets=5, reps=5),
        WorkoutExercise(workout=leg_day, exercise=deadlift, sets=3, reps=8),
        WorkoutExercise(workout=leg_day, exercise=stretch, duration_seconds=120),
        # Timed entries use duration_seconds
        WorkoutExercise(workout=cardio_day, exercise=run, duration_seconds=1800),
        WorkoutExercise(workout=cardio_day, exercise=jump_rope, duration_seconds=300),
        WorkoutExercise(workout=full_body, exercise=pushup, sets=4, reps=15),
        WorkoutExercise(workout=full_body, exercise=squat, sets=3, reps=12),
        WorkoutExercise(workout=full_body, exercise=plank, sets=3, reps=1, duration_seconds=60),
        WorkoutExercise(workout=recovery, exercise=stretch, duration_seconds=300),
        WorkoutExercise(workout=recovery, exercise=plank, duration_seconds=90),
    ]
    db.session.add_all(workout_exercises)
    db.session.commit()

    print(f"Seeded {len(exercises)} exercises, {len(workouts)} workouts "
          f"and {len(workout_exercises)} workout exercises.")
