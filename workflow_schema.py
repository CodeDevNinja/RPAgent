workflow_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "workflow_name": {
            "type": "string"
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["launch_app", "wait_for_element", "click", "extract_content"]
                    },
                    "package_name": {
                        "type": "string"
                    },
                    "selector": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["xpath"]
                            },
                            "value": {
                                "type": "string"
                            }
                        },
                        "required": ["type", "value"]
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1
                    },
                    "output_variable": {
                        "type": "string"
                    }
                },
                "required": ["action"],
                "oneOf": [
                    {
                        "required": ["name"]
                    },
                    {
                        "required": ["selector"]
                    }
                ],
                "dependencies": {
                    "package_name": ["action"]
                }
            }
        }
    },
    "required": ["workflow_name", "events"]
}
