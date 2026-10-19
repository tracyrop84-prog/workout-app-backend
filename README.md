# Workout Tracker API

A Flask + SQLAlchemy backend for a workout tracking app used by personal trainers. Trainers can create workouts, build a reusable library of exercises, and add exercises to workouts with sets, reps, or a duration.

The API validates data in three layers:
- **Marshmallow schemas** reject bad requests before anything reaches the database.
- **Model validations** (`@validates`) keep bad values off the model objects.
- **Table constraints** let the database itself refuse invalid rows.

## Tech stack

Flask · Flask-SQLAlchemy · Flask-Migrate · Marshmallow · SQLite · pytest

## Project structure

```
workout-app-backend/
├── Pipfile
├── README.md
└── server/
    ├── app.py                    # App factory, registers blueprints, runs on port 5555
    ├── models.py                 # Exercise, Workout, WorkoutExercise + constraints/validations
    ├── schemas.py                # Marshmallow schemas (serialization + schema validations)
    ├── seed.py                   # Resets the database and adds example data
    ├── routes/
    │   ├── workouts.py           # /workouts endpoints
    │   ├── exercises.py          # /exercises endpoints
    │   ├── workout_exercises.py  # add an exercise to a workout
    │   └── helpers.py            # shared request/response helpers
    ├── migrations/               # Flask-Migrate (Alembic) migrations
    └── tests/                    # pytest suite
```

## Data model

```
Workout 1 ──< WorkoutExercise >── 1 Exercise
```

| Model | Fields |
|-------|--------|
| **Exercise** | `id`, `name`, `category`, `equipment_needed` |
| **Workout** | `id`, `date`, `duration_minutes`, `notes` |
| **WorkoutExercise** (join table) | `id`, `workout_id`, `exercise_id`, `reps`, `sets`, `duration_seconds` |

**Relationships**
- A `Workout` has many `WorkoutExercises`, and has many `Exercises` through them.
- An `Exercise` has many `WorkoutExercises`, and has many `Workouts` through them.
- A `WorkoutExercise` belongs to one `Workout` and one `Exercise`.
- Deleting a workout or an exercise also deletes its `WorkoutExercises`.

## Validations

| Layer | Rules |
|-------|-------|
| **Table constraints** | Exercise `name` is unique and not blank · `category` must be an allowed value · `duration_minutes > 0` · `reps`, `sets`, `duration_seconds` must be positive · the same exercise can't be added to the same workout twice · foreign keys must point to real rows |
| **Model validations** | Exercise name required, max 100 characters · category must be one of `strength`, `cardio`, `flexibility`, `balance`, `core` (case-insensitive) · workout date must be a real date · duration between 1 and 600 minutes · notes max 1000 characters · reps/sets/duration must be positive whole numbers |
| **Schema validations** | Required fields (`name`, `category`, `date`, `duration_minutes`) · `category` must be one of the allowed values · `duration_minutes` between 1 and 600 · `date` must be `YYYY-MM-DD` · a workout exercise needs **both sets and reps**, or **duration_seconds** · whole numbers only (no strings or decimals) |

## Installation

Requires Python 3.12 and [pipenv](https://pipenv.pypa.io/).

```bash
git clone https://github.com/<your-username>/workout-app-backend.git
cd workout-app-backend
pipenv install --dev
pipenv shell
```

Set up the database and add example data (run these from the `server/` folder):

```bash
cd server
flask db upgrade head
python seed.py
```

`seed.py` clears all tables before inserting, so you can run it again at any time to reset the data without creating duplicates.

## Running the app

From the `server/` folder:

```bash
python app.py
```

The API runs at `http://localhost:5555`. Alternatively, run `flask run --port 5555`.

### Running tests

From the `server/` folder:

```bash
pytest
```

## API endpoints

All requests and responses use JSON. Validation errors return `400` with details, for example:
```json
{ "errors": { "duration_minutes": ["Must be greater than or equal to 1 and less than or equal to 600."] } }
```

### Workouts

| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| GET | `/workouts` | List all workouts, newest first | `200` | |
| GET | `/workouts/<id>` | One workout with its exercises, including sets/reps/duration | `200` | `404` |
| POST | `/workouts` | Create a workout | `201` | `400` |
| DELETE | `/workouts/<id>` | Delete a workout and its workout exercises | `204` | `404` |

**POST /workouts** body:
```json
{ "date": "2026-10-19", "duration_minutes": 45, "notes": "Leg day" }
```

**GET /workouts/1** response:
```json
{
  "id": 1,
  "date": "2026-10-13",
  "duration_minutes": 60,
  "notes": "Lower body strength. Focus on squat depth.",
  "workout_exercises": [
    {
      "id": 1,
      "workout_id": 1,
      "exercise_id": 1,
      "reps": 5,
      "sets": 5,
      "duration_seconds": null,
      "exercise": { "id": 1, "name": "Back Squat", "category": "strength", "equipment_needed": true }
    }
  ]
}
```

### Exercises

| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| GET | `/exercises` | List all exercises, A–Z | `200` | |
| GET | `/exercises/<id>` | One exercise with the workouts it appears in | `200` | `404` |
| POST | `/exercises` | Create an exercise | `201` | `400` invalid, `409` name taken |
| DELETE | `/exercises/<id>` | Delete an exercise and its workout exercises | `204` | `404` |

**POST /exercises** body:
```json
{ "name": "Bench Press", "category": "strength", "equipment_needed": true }
```
`category` must be one of `strength`, `cardio`, `flexibility`, `balance`, `core`. `equipment_needed` defaults to `false`.

### Adding an exercise to a workout

| Method | Endpoint | Description | Success | Errors |
|--------|----------|-------------|---------|--------|
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout with sets/reps or a duration | `201` | `400` invalid, `404` workout/exercise not found, `409` already added |

Body: provide **sets and reps**, or **duration_seconds** (or all three):
```json
{ "sets": 4, "reps": 10 }
```
```json
{ "duration_seconds": 300 }
```

Response (`201`):
```json
{
  "id": 11,
  "workout_id": 5,
  "exercise_id": 8,
  "reps": 10,
  "sets": 4,
  "duration_seconds": null,
  "exercise": { "id": 8, "name": "Bench Press", "category": "strength", "equipment_needed": true }
}
```

## Checking validations in the Flask shell

```bash
cd server
flask shell
```
```python
>>> from models import *
>>> Exercise(name="", category="strength")        # ValueError: Exercise name is required.
>>> Workout(date=None, duration_minutes=0)        # ValueError
>>> w = Workout.query.first()
>>> list(w.exercises)                             # exercises through WorkoutExercises
>>> Exercise.query.first().workouts               # workouts through WorkoutExercises
```
