"""Vault paths and operation discovery."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator


def default_ops_root() -> Path:
    env = os.environ.get("FLIPPER69_OPS_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".flipper69" / "ops"


def operations_dir(ops_root: Path | None = None) -> Path:
    root = ops_root or default_ops_root()
    return root / "operations"


def ensure_vault(ops_root: Path | None = None) -> Path:
    ops = operations_dir(ops_root)
    ops.mkdir(parents=True, exist_ok=True)
    return ops


def iter_ops(ops_root: Path | None = None) -> Iterator[Path]:
    ops = operations_dir(ops_root)
    if not ops.is_dir():
        return
    for p in sorted(ops.iterdir()):
        if p.is_dir() and p.name.startswith("op-"):
            yield p


def load_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def op_path(op_id: str, ops_root: Path | None = None) -> Path:
    return operations_dir(ops_root) / op_id


def read_operation(op_dir: Path) -> dict[str, Any] | None:
    data = load_json(op_dir / "OPERATION.json")
    return data if isinstance(data, dict) else None


def read_manifest(op_dir: Path) -> dict[str, Any] | None:
    data = load_json(op_dir / "CASEFILE-MANIFEST.json")
    return data if isinstance(data, dict) else None


def read_timeline(op_dir: Path) -> list[dict[str, Any]]:
    path = op_dir / "TIMELINE.jsonl"
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                events.append(obj)
        except json.JSONDecodeError:
            events.append({"raw": line, "event": "parse_error"})
    return events
