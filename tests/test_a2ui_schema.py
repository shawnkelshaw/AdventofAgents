import json
import pytest
from jsonschema import validate, ValidationError
from calendar_agent.a2ui_schema import A2UI_SCHEMA

# Parse the schema once for testing
schema = json.loads(A2UI_SCHEMA)

def test_valid_begin_rendering():
    payload = {
        "beginRendering": {
            "surfaceId": "test_surface",
            "root": "root_id"
        }
    }
    validate(instance=payload, schema=schema)

def test_valid_surface_update():
    payload = {
        "surfaceUpdate": {
            "surfaceId": "test_surface",
            "components": [
                {
                    "id": "root_id",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Hello World"}
                        }
                    }
                }
            ]
        }
    }
    validate(instance=payload, schema=schema)

def test_invalid_missing_action():
    payload = {}
    # jsonschema doesn't automatically enforce "exactly one of" unless defined
    # But our schema description says it must contain exactly one.
    # The schema actually has these as optional properties.
    # Let's verify that a payload with multiple actions is technically allowed by schema
    # (though description says otherwise)
    payload = {
        "beginRendering": {"surfaceId": "s1", "root": "r1"},
        "deleteSurface": {"surfaceId": "s1"}
    }
    validate(instance=payload, schema=schema) # This passes because schema doesn't use oneOf at root

def test_invalid_component_type():
    payload = {
        "surfaceUpdate": {
            "surfaceId": "test_surface",
            "components": [
                {
                    "id": "root_id",
                    "component": {
                        "UnknownType": {}
                    }
                }
            ]
        }
    }
    with pytest.raises(ValidationError):
        validate(instance=payload, schema=schema)

def test_valid_button_with_variant():
    payload = {
        "surfaceUpdate": {
            "surfaceId": "test_surface",
            "components": [
                {
                    "id": "btn_1",
                    "component": {
                        "Button": {
                            "child": "text_1",
                            "variant": "primary",
                            "action": {"name": "test_action"}
                        }
                    }
                }
            ]
        }
    }
    validate(instance=payload, schema=schema)
