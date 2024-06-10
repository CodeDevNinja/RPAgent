import json
from jsonschema import validate, ValidationError

def validate_json_with_schema(json_string, schema):
    try:
        data = json.load(json_string)
    except ValueError as e:
        return False, f"Invalid JSON: {e}"
    
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Schema validation error: {e.message}"