"""Lightweight schema presence checks (jsonschema optional)."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"


def test_schemas_parse():
    required = [
        "operation.schema.json",
        "manifest.schema.json",
        "active_op.schema.json",
        "checkpoint.schema.json",
        "probe.plugin.schema.json",
        "template.schema.json",
        "serial_protocol.schema.json",
    ]
    for name in required:
        path = SCHEMAS / name
        assert path.is_file(), name
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "$schema" in data
        assert "title" in data


def test_example_templates_match_shape():
    tdir = REPO / "examples" / "templates"
    for f in tdir.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data.get("templateId")
        assert data.get("authorizationPrompt")
        assert data.get("defaultAuthorized") is False
