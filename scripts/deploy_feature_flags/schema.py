"""The AWS.AppConfig.FeatureFlags JSON schema, used to validate feature_flags.json before
creating a new hosted configuration version or starting a deployment.

Schema copied from:
https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-type-reference-feature-flags.html
"""

from __future__ import annotations

from typing import Any

import jsonschema

FEATURE_FLAGS_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "flagSetDefinition": {
            "type": "object",
            "properties": {
                "version": {"$ref": "#/definitions/flagSchemaVersions"},
                "flags": {"$ref": "#/definitions/flagDefinitions"},
                "values": {"$ref": "#/definitions/flagValues"},
            },
            "required": ["version"],
            "additionalProperties": False,
        },
        "flagDefinitions": {
            "type": "object",
            "patternProperties": {"^[a-z][a-zA-Z\\d_-]{0,63}$": {"$ref": "#/definitions/flagDefinition"}},
            "additionalProperties": False,
        },
        "flagDefinition": {
            "type": "object",
            "properties": {
                "name": {"$ref": "#/definitions/customerDefinedName"},
                "description": {"$ref": "#/definitions/customerDefinedDescription"},
                "_createdAt": {"type": "string"},
                "_updatedAt": {"type": "string"},
                "_deprecation": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["planned"]},
                        "date": {"type": "string", "format": "date"},
                    },
                    "additionalProperties": False,
                },
                "attributes": {"$ref": "#/definitions/attributeDefinitions"},
            },
            "additionalProperties": False,
        },
        "attributeDefinitions": {
            "type": "object",
            "patternProperties": {"^[a-z][a-zA-Z\\d_-]{0,63}$": {"$ref": "#/definitions/attributeDefinition"}},
            "maxProperties": 25,
            "additionalProperties": False,
        },
        "attributeDefinition": {
            "type": "object",
            "properties": {
                "description": {"$ref": "#/definitions/customerDefinedDescription"},
                "constraints": {
                    "oneOf": [
                        {"$ref": "#/definitions/numberConstraints"},
                        {"$ref": "#/definitions/stringConstraints"},
                        {"$ref": "#/definitions/arrayConstraints"},
                        {"$ref": "#/definitions/boolConstraints"},
                    ]
                },
            },
            "additionalProperties": False,
        },
        "flagValues": {
            "type": "object",
            "patternProperties": {"^[a-z][a-zA-Z\\d_-]{0,63}$": {"$ref": "#/definitions/flagValue"}},
            "additionalProperties": False,
        },
        "flagValue": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "_createdAt": {"type": "string"},
                "_updatedAt": {"type": "string"},
                "_variants": {
                    "type": "array",
                    "maxLength": 32,
                    "items": {"$ref": "#/definitions/variant"},
                },
            },
            "patternProperties": {
                "^[a-z][a-zA-Z\\d_-]{0,63}$": {
                    "$ref": "#/definitions/attributeValue",
                    "maxProperties": 25,
                }
            },
            "additionalProperties": False,
        },
        "attributeValue": {
            "oneOf": [
                {"type": "string", "maxLength": 1024},
                {"type": "number"},
                {"type": "boolean"},
                {
                    "type": "array",
                    "oneOf": [
                        {"items": {"type": "string", "maxLength": 1024}},
                        {"items": {"type": "number"}},
                    ],
                },
            ],
            "additionalProperties": False,
        },
        "stringConstraints": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["string"]},
                "required": {"type": "boolean"},
                "pattern": {"type": "string", "maxLength": 1024},
                "enum": {
                    "type": "array",
                    "maxLength": 100,
                    "items": {"oneOf": [{"type": "string", "maxLength": 1024}, {"type": "integer"}]},
                },
            },
            "required": ["type"],
            "not": {"required": ["pattern", "enum"]},
            "additionalProperties": False,
        },
        "numberConstraints": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["number"]},
                "required": {"type": "boolean"},
                "minimum": {"type": "integer"},
                "maximum": {"type": "integer"},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
        "arrayConstraints": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["array"]},
                "required": {"type": "boolean"},
                "elements": {"$ref": "#/definitions/elementConstraints"},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
        "boolConstraints": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["boolean"]},
                "required": {"type": "boolean"},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
        "elementConstraints": {
            "oneOf": [{"$ref": "#/definitions/numberConstraints"}, {"$ref": "#/definitions/stringConstraints"}]
        },
        "variant": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "name": {"$ref": "#/definitions/customerDefinedName"},
                "rule": {"type": "string", "maxLength": 16384},
                "attributeValues": {
                    "type": "object",
                    "patternProperties": {"^[a-z][a-zA-Z\\d_-]{0,63}$": {"$ref": "#/definitions/attributeValue"}},
                    "maxProperties": 25,
                    "additionalProperties": False,
                },
            },
            "required": ["name", "enabled"],
            "additionalProperties": False,
        },
        "customerDefinedName": {"type": "string", "pattern": "^[^\\n]{1,64}$"},
        "customerDefinedDescription": {"type": "string", "maxLength": 1024},
        "flagSchemaVersions": {"type": "string", "enum": ["1"]},
    },
    "type": "object",
    "$ref": "#/definitions/flagSetDefinition",
    "additionalProperties": False,
}


def validate_feature_flags(content: dict[str, Any]) -> None:
    """Validate `content` against the AWS.AppConfig.FeatureFlags schema.

    Raises `jsonschema.exceptions.ValidationError` if `content` doesn't conform, so this fails
    fast with a clear error instead of AWS rejecting it mid-deployment.
    """
    jsonschema.validate(instance=content, schema=FEATURE_FLAGS_SCHEMA)
