"""Endpoints, serialization and schema validations."""

from models import WorkoutExercise, db

ADD_URL = "/workouts/{w}/exercises/{e}/workout_exercises"


# ---------- Workouts ----------

def test_list_workouts(client, workout):
    response = client.get("/workouts")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["date"] == "2026-10-01"


def test_get_workout_includes_exercises_with_sets_reps(client, workout, exercise):
    client.post(ADD_URL.format(w=workout.id, e=exercise.id), json={"sets": 3, "reps": 10})
    body = client.get(f"/workouts/{workout.id}").get_json()
    entry = body["workout_exercises"][0]
    assert entry["sets"] == 3 and entry["reps"] == 10
    assert entry["exercise"]["name"] == "Squat"


def test_get_missing_workout(client):
    assert client.get("/workouts/999").status_code == 404


def test_create_workout(client):
    response = client.post("/workouts", json={
        "date": "2026-10-19", "duration_minutes": 50, "notes": "Leg day",
    })
    assert response.status_code == 201
    assert response.get_json()["duration_minutes"] == 50


def test_create_workout_schema_validations(client):
    missing = client.post("/workouts", json={"notes": "No date or duration"})
    assert missing.status_code == 400
    errors = missing.get_json()["errors"]
    assert "date" in errors and "duration_minutes" in errors

    bad_date = client.post("/workouts", json={"date": "not-a-date", "duration_minutes": 30})
    assert bad_date.status_code == 400

    too_long = client.post("/workouts", json={"date": "2026-10-19", "duration_minutes": 9999})
    assert too_long.status_code == 400


def test_create_workout_rejects_non_json(client):
    response = client.post("/workouts", data="hello", content_type="text/plain")
    assert response.status_code == 400


def test_delete_workout_removes_workout_exercises(client, workout, exercise):
    client.post(ADD_URL.format(w=workout.id, e=exercise.id), json={"sets": 3, "reps": 10})
    assert client.delete(f"/workouts/{workout.id}").status_code == 204
    assert client.get(f"/workouts/{workout.id}").status_code == 404
    assert WorkoutExercise.query.count() == 0


def test_delete_missing_workout(client):
    assert client.delete("/workouts/999").status_code == 404


# ---------- Exercises ----------

def test_list_exercises(client, exercise):
    body = client.get("/exercises").get_json()
    assert [e["name"] for e in body] == ["Squat"]


def test_get_exercise_includes_workouts(client, workout, exercise):
    client.post(ADD_URL.format(w=workout.id, e=exercise.id), json={"duration_seconds": 60})
    body = client.get(f"/exercises/{exercise.id}").get_json()
    assert body["workout_exercises"][0]["workout"]["id"] == workout.id


def test_create_exercise(client):
    response = client.post("/exercises", json={
        "name": "Burpee", "category": "cardio", "equipment_needed": False,
    })
    assert response.status_code == 201
    assert response.get_json()["name"] == "Burpee"


def test_create_exercise_schema_validations(client):
    bad_category = client.post("/exercises", json={"name": "Zumba", "category": "dancing"})
    assert bad_category.status_code == 400
    assert "category" in bad_category.get_json()["errors"]

    blank_name = client.post("/exercises", json={"name": "   ", "category": "cardio"})
    assert blank_name.status_code == 400


def test_create_duplicate_exercise(client, exercise):
    response = client.post("/exercises", json={"name": "Squat", "category": "strength"})
    assert response.status_code == 409


def test_delete_exercise_removes_workout_exercises(client, workout, exercise):
    client.post(ADD_URL.format(w=workout.id, e=exercise.id), json={"sets": 3, "reps": 10})
    assert client.delete(f"/exercises/{exercise.id}").status_code == 204
    assert WorkoutExercise.query.count() == 0
    assert client.get(f"/workouts/{workout.id}").status_code == 200  # workout is kept


# ---------- Adding an exercise to a workout ----------

def test_add_exercise_with_sets_and_reps(client, workout, exercise):
    response = client.post(ADD_URL.format(w=workout.id, e=exercise.id), json={"sets": 4, "reps": 8})
    assert response.status_code == 201
    body = response.get_json()
    assert body["workout_id"] == workout.id and body["exercise_id"] == exercise.id
    assert body["exercise"]["name"] == "Squat"


def test_add_exercise_with_duration(client, workout, exercise):
    response = client.post(ADD_URL.format(w=workout.id, e=exercise.id), json={"duration_seconds": 90})
    assert response.status_code == 201


def test_add_exercise_schema_validations(client, workout, exercise):
    url = ADD_URL.format(w=workout.id, e=exercise.id)
    assert client.post(url, json={}).status_code == 400                   # nothing given
    assert client.post(url, json={"sets": 3}).status_code == 400          # reps missing
    assert client.post(url, json={"sets": 0, "reps": 5}).status_code == 400  # not positive
    assert client.post(url, json={"duration_seconds": "long"}).status_code == 400


def test_add_same_exercise_twice(client, workout, exercise):
    url = ADD_URL.format(w=workout.id, e=exercise.id)
    client.post(url, json={"sets": 3, "reps": 10})
    assert client.post(url, json={"sets": 3, "reps": 10}).status_code == 409


def test_add_exercise_to_missing_workout_or_exercise(client, workout, exercise):
    assert client.post(ADD_URL.format(w=999, e=exercise.id), json={"sets": 1, "reps": 1}).status_code == 404
    assert client.post(ADD_URL.format(w=workout.id, e=999), json={"sets": 1, "reps": 1}).status_code == 404
