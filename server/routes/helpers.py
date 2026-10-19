from flask import request
from marshmallow import ValidationError


def load_json(schema):
    """
    Validate the request body with a marshmallow schema.

    Returns (data, None) on success, or (None, error_response) if the body
    is missing or invalid.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, ({"errors": {"body": ["Request body must be a JSON object."]}}, 400)
    try:
        return schema.load(payload), None
    except ValidationError as error:
        return None, ({"errors": error.messages}, 400)


def not_found(resource, resource_id):
    return {"errors": {"id": [f"{resource} {resource_id} not found."]}}, 404
