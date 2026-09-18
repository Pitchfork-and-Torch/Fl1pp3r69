"""Migrate v2/v3 vault operations to schemaVersion 4 ARGUS VEIL (idempotent)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flipper69.vault import iter_ops, load_json


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def migrate_operation_doc(doc: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    changed = False
    if doc.get("schemaVersion") != 4:
        doc["schemaVersion"] = 4
        changed = True
    if "session" not in doc:
        doc["session"] = 1
        changed = True
    if doc.get("releaseCodename") != "ARGUS VEIL":
        doc["releaseCodename"] = "ARGUS VEIL"
        changed = True
    if "artifactRoot" not in doc:
        doc["artifactRoot"] = "artifacts"
        changed = True
    if "gates" not in doc:
        doc["gates"] = {"requireAuthForTx": True, "requireCaptureBeforeVerify": True}
        changed = True
    device = doc.get("device")
    if isinstance(device, dict) and "firmware" not in device:
        device["firmware"] = "flipper69"
        changed = True
    return doc, changed


def migrate_manifest_doc(doc: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    changed = False
    if doc.get("schemaVersion") != 4:
        doc["schemaVersion"] = 4
        changed = True
    if doc.get("releaseCodename") != "ARGUS VEIL":
        doc["releaseCodename"] = "ARGUS VEIL"
        changed = True
    if "verifyCount" not in doc:
        doc["verifyCount"] = 1
        changed = True
    if "chainPrev" not in doc:
        doc["chainPrev"] = None
        changed = True
    if "classification" not in doc:
        doc["classification"] = "UNCLASSIFIED//FRI"
        changed = True
    if "sealAlg" not in doc:
        doc["sealAlg"] = "sha256"
        changed = True
    return doc, changed


def migrate_op_dir(op_dir: Path) -> dict[str, Any]:
    result = {"opId": op_dir.name, "operation": False, "manifest": False, "checkpoint": False}
    op_path = op_dir / "OPERATION.json"
    if op_path.is_file():
        doc = load_json(op_path)
        if isinstance(doc, dict):
            doc, changed = migrate_operation_doc(doc)
            if changed:
                op_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
                result["operation"] = True

    man_path = op_dir / "CASEFILE-MANIFEST.json"
    if man_path.is_file():
        doc = load_json(man_path)
        if isinstance(doc, dict):
            doc, changed = migrate_manifest_doc(doc)
            if changed:
                man_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
                result["manifest"] = True

    ckp = op_dir / "CHECKPOINT.json"
    if not ckp.is_file():
        op = load_json(op_path) if op_path.is_file() else {}
        phase = "close"
        if isinstance(op, dict):
            phase = str(op.get("phase", "close")).lower()
            if phase.isupper():
                phase = phase.lower()
        body = {
            "schemaVersion": 4,
            "opId": op_dir.name,
            "phase": phase if phase in {
                "intake", "op_prep", "probe", "capture", "verify", "exfil", "close"
            } else "close",
            "session": 1,
            "updatedAt": _utc_now(),
            "reason": "resume",
        }
        ckp.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        result["checkpoint"] = True

    # Ensure artifacts/ exists (v4 layout); keep captures/ as alias
    art = op_dir / "artifacts"
    if not art.is_dir():
        art.mkdir(exist_ok=True)
        (art / "field").mkdir(exist_ok=True)
        result["artifacts"] = True
    man_dir = op_dir / "manifests"
    if not man_dir.is_dir():
        man_dir.mkdir(exist_ok=True)
        result["manifests_dir"] = True

    return result


def migrate_vault(ops_root: Path | None = None) -> dict[str, Any]:
    results = [migrate_op_dir(p) for p in iter_ops(ops_root)]
    return {
        "migrated_ops": len(results),
        "results": results,
        "note": "Idempotent. Hashes of artifacts unchanged; re-VERIFY on device if re-sealing.",
    }
