"""Operation templates."""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flipper69.vault import ensure_vault, operations_dir

# Built-in templates (also mirrored under examples/templates/)
BUILTIN: dict[str, dict[str, Any]] = {
    "survey-building": {
        "schemaVersion": 3,
        "templateId": "survey-building",
        "name": "Building RF/NFC Survey",
        "description": "Authorized passive survey of a scoped facility footprint.",
        "opType": "survey",
        "pathLabel": "ds",
        "authorizationPrompt": (
            "Confirm you have written authorization to survey this site "
            "and will only capture passive metadata on approved systems."
        ),
        "defaultAuthorized": False,
        "suggestedProbes": ["subghz", "nfc", "ir"],
        "phases": [
            {"phase": "intake", "checklist": ["Scope document ready", "PATHNUM chosen"]},
            {"phase": "op_prep", "checklist": ["OPSEC on", "notes scaffold"]},
            {"phase": "probe", "checklist": ["DEWDROP / DAMP_CROWD / EMBER as needed"]},
            {"phase": "capture", "checklist": ["Files in captures/"]},
            {"phase": "verify", "checklist": ["Manifest PASS"]},
            {"phase": "exfil", "checklist": ["Deliberate SD or USB"]},
            {"phase": "close", "checklist": ["Seal op"]},
        ],
        "notesScaffold": "# Building survey\n# Scope:\n# Auth ref:\n",
    },
    "badge-lab": {
        "schemaVersion": 3,
        "templateId": "badge-lab",
        "name": "Owned Badge Lab",
        "description": "Lab work on badges/tags you own (read/write/emulate).",
        "opType": "proximity",
        "pathLabel": "slow",
        "authorizationPrompt": (
            "Confirm every tag involved is owned by you or explicitly authorized "
            "for destructive/write testing. Bank cards and secure elements are out of scope."
        ),
        "defaultAuthorized": False,
        "suggestedProbes": ["nfc"],
        "phases": [
            {"phase": "intake", "checklist": ["Inventory owned tags"]},
            {"phase": "op_prep", "checklist": ["OPSEC on"]},
            {"phase": "probe", "checklist": ["DEWDROP only"]},
            {"phase": "capture", "checklist": ["UID + meta sidecars"]},
            {"phase": "verify", "checklist": ["Hash seal"]},
            {"phase": "exfil", "checklist": ["Vault import"]},
            {"phase": "close", "checklist": ["Seal"]},
        ],
        "notesScaffold": "# Badge lab\n# Tag inventory:\n",
    },
    "client-pentest-physical": {
        "schemaVersion": 3,
        "templateId": "client-pentest-physical",
        "name": "Client Physical Assessment",
        "description": "Red-team physical engagement with full CoC for client report.",
        "opType": "unified",
        "pathLabel": "imps",
        "authorizationPrompt": (
            "Confirm ROE/SOW authorization for this engagement ID is active, "
            "out-of-scope systems are excluded, and client notification rules are understood."
        ),
        "defaultAuthorized": False,
        "suggestedProbes": ["nfc", "subghz", "ir"],
        "phases": [
            {"phase": "intake", "checklist": ["Engagement ID", "ROE reviewed"]},
            {"phase": "op_prep", "checklist": ["High OPSEC (imps)", "OPSEC badge on"]},
            {"phase": "probe", "checklist": ["Only in-scope domains"]},
            {"phase": "capture", "checklist": ["Minimal necessary artifacts"]},
            {"phase": "verify", "checklist": ["Manifest + chainPrev"]},
            {"phase": "exfil", "checklist": ["Air-gap preferred", "Generate report"]},
            {"phase": "close", "checklist": ["Seal", "Retention note"]},
        ],
        "notesScaffold": "# Client physical assessment\n# Engagement ID:\n# ROE:\n# Out of scope:\n",
    },
    "academic-rf-capture": {
        "schemaVersion": 3,
        "templateId": "academic-rf-capture",
        "name": "Academic RF Capture",
        "description": "Lab RF capture for publication with strong provenance.",
        "opType": "survey",
        "pathLabel": "slow",
        "authorizationPrompt": (
            "Confirm IRB/lab policy allows this capture, transmitters are owned or licensed, "
            "and data retention rules for research subjects are documented."
        ),
        "defaultAuthorized": False,
        "suggestedProbes": ["subghz", "ir"],
        "phases": [
            {"phase": "intake", "checklist": ["Hypothesis / protocol ID"]},
            {"phase": "op_prep", "checklist": ["Device serial noted"]},
            {"phase": "probe", "checklist": ["DAMP_CROWD / EMBER sidecars"]},
            {"phase": "capture", "checklist": ["Raw + meta"]},
            {"phase": "verify", "checklist": ["Manifest for publication appendix"]},
            {"phase": "exfil", "checklist": ["Vault + report HTML"]},
            {"phase": "close", "checklist": ["Seal"]},
        ],
        "notesScaffold": "# Academic RF\n# Protocol:\n# Equipment:\n",
    },
}


def list_templates(extra_dir: Path | None = None) -> list[dict[str, Any]]:
    items = list(BUILTIN.values())
    if extra_dir and extra_dir.is_dir():
        for f in extra_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("templateId"):
                    items.append(data)
            except json.JSONDecodeError:
                continue
    # dedupe by templateId (extra wins)
    by_id = {t["templateId"]: t for t in items}
    return sorted(by_id.values(), key=lambda t: t["templateId"])


def get_template(template_id: str, extra_dir: Path | None = None) -> dict[str, Any] | None:
    for t in list_templates(extra_dir):
        if t["templateId"] == template_id:
            return t
    return None


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:24] or "op"


def apply_template(
    template_id: str,
    *,
    label: str = "field",
    ops_root: Path | None = None,
    extra_dir: Path | None = None,
    acknowledge_auth: bool = False,
) -> Path:
    tpl = get_template(template_id, extra_dir)
    if not tpl:
        raise KeyError(f"Unknown template: {template_id}")
    if not acknowledge_auth:
        raise PermissionError(
            "Refusing to apply template without --acknowledge-auth. "
            f"You must confirm: {tpl['authorizationPrompt']}"
        )

    ensure_vault(ops_root)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    op_id = f"op-{day}-{_slug(label)}-{secrets.token_hex(3)}"
    op_dir = operations_dir(ops_root) / op_id
    op_dir.mkdir(parents=True)
    (op_dir / "captures").mkdir()

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    operation = {
        "schemaVersion": 4,
        "opId": op_id,
        "codename": f"template_{_slug(template_id)}",
        "workspace": f"f69_{secrets.token_hex(4)}",
        "opType": tpl["opType"],
        "pathLabel": tpl["pathLabel"],
        "phase": "op_prep",
        "session": 1,
        "templateId": template_id,
        "openedAt": now,
        "device": {"firmware": "flipper69", "version": "4.0.0", "codename": "FL1PP3R69"},
        "releaseCodename": "ARGUS VEIL",
        "artifactRoot": "artifacts",
        "gates": {"requireAuthForTx": True, "requireCaptureBeforeVerify": True},
        "target": {"label": label, "notes": "", "authorized": False},
        "permissions": {"opsec": True, "authorized": False},
        "captureCount": 0,
        "manifestHash": None,
    }
    (op_dir / "OPERATION.json").write_text(json.dumps(operation, indent=2) + "\n", encoding="utf-8")
    (op_dir / "notes.txt").write_text(
        tpl.get("notesScaffold", "# notes\n") + f"\n# template: {template_id}\n# auth prompt acknowledged\n",
        encoding="utf-8",
    )
    ckp = {
        "schemaVersion": 4,
        "opId": op_id,
        "phase": "op_prep",
        "session": 1,
        "updatedAt": now,
        "reason": "create",
    }
    (op_dir / "CHECKPOINT.json").write_text(json.dumps(ckp, indent=2) + "\n", encoding="utf-8")
    (op_dir / "artifacts").mkdir(exist_ok=True)
    tl = {
        "ts": now,
        "event": "TEMPLATE_APPLY",
        "source": "flipper69-desktop",
        "ver": "4.0.0",
        "data": {"templateId": template_id, "label": label},
    }
    (op_dir / "TIMELINE.jsonl").write_text(json.dumps(tl) + "\n", encoding="utf-8")
    return op_dir
