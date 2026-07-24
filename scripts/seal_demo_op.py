#!/usr/bin/env python3
"""Seal the VEIL LEDGER demo op with consistent SHA-256 items."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OP = ROOT / "examples/sd_card/flipper69/operations/op-20260711-veil-ledger-demo"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OP.mkdir(parents=True, exist_ok=True)
    (OP / "captures").mkdir(exist_ok=True)

    (OP / "notes.txt").write_text(
        "# veil_ledger_demo\n"
        "# FL1PP3R69 // 3.0.0 // VEIL LEDGER\n"
        "# path: ds\n"
        "# Example operation for desktop audit/report demos.\n",
        encoding="utf-8",
        newline="\n",
    )
    (OP / "CHECKPOINT.json").write_text(
        json.dumps(
            {
                "schemaVersion": 3,
                "opId": "op-20260711-veil-ledger-demo",
                "phase": "verify",
                "session": 1,
                "updatedAt": "2026-07-11T10:15:00Z",
                "reason": "verify",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OP / "captures/ember_demo.meta.json").write_text(
        json.dumps(
            {
                "probe": "ember_trace",
                "ver": "3.0.0",
                "protocol": "NEC",
                "note": "example sidecar for VEIL LEDGER demo",
                "txNote": "authorized owned hardware only",
                "ts": "2026-07-11T10:05:00Z",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    events = [
        {
            "ts": "2026-07-11T10:00:00Z",
            "event": "INTAKE",
            "source": "casefile_ops",
            "ver": "3.0.0",
            "data": {"templateId": "survey-building"},
        },
        {
            "ts": "2026-07-11T10:01:00Z",
            "event": "OP_PREP",
            "source": "casefile_ops",
            "ver": "3.0.0",
            "data": {"path": "ds"},
        },
        {
            "ts": "2026-07-11T10:05:00Z",
            "event": "PROBE",
            "source": "ember_trace",
            "ver": "3.0.0",
            "data": {"protocol": "NEC"},
        },
        {
            "ts": "2026-07-11T10:10:00Z",
            "event": "CAPTURE",
            "source": "ember_trace",
            "ver": "3.0.0",
            "data": {"file": "captures/ember_demo.meta.json"},
        },
        {
            "ts": "2026-07-11T10:15:00Z",
            "event": "VERIFY",
            "source": "casefile_ops",
            "ver": "3.0.0",
            "data": {"schemaVersion": 3},
        },
    ]
    (OP / "TIMELINE.jsonl").write_text(
        "".join(json.dumps(e, separators=(",", ":")) + "\n" for e in events),
        encoding="utf-8",
        newline="\n",
    )

    opdoc = {
        "schemaVersion": 3,
        "opId": "op-20260711-veil-ledger-demo",
        "codename": "veil_ledger_demo",
        "workspace": "f69_a1b2c3d4",
        "opType": "unified",
        "pathnum": 2,
        "pathLabel": "ds",
        "phase": "verify",
        "session": 1,
        "templateId": "survey-building",
        "openedAt": "2026-07-11T10:00:00Z",
        "device": {
            "firmware": "flipper69",
            "version": "3.0.0",
            "codename": "FL1PP3R69",
            "serial": "DEMO-V3",
            "region": "US",
        },
        "releaseCodename": "VEIL LEDGER",
        "target": {
            "label": "veil-ledger-demo",
            "authorized": True,
            "notes": "Example v3 operation for schema and desktop toolkit demos",
        },
        "permissions": {
            "opsec": True,
            "authorized": True,
            "txEnabled": False,
            "replayConfirmed": False,
        },
        "captureCount": 1,
        "manifestHash": None,
    }
    (OP / "OPERATION.json").write_text(
        json.dumps(opdoc, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    rels = [
        ("operation", "OPERATION.json", None),
        ("timeline", "TIMELINE.jsonl", None),
        ("notes", "notes.txt", None),
        ("checkpoint", "CHECKPOINT.json", None),
        ("capture", "captures/ember_demo.meta.json", "ember_trace"),
    ]
    items = []
    for typ, rel, probe in rels:
        p = OP / rel
        item = {
            "type": typ,
            "path": rel,
            "hash": sha256(p),
            "sizeBytes": p.stat().st_size,
        }
        if probe:
            item["probe"] = probe
        items.append(item)

    man = {
        "schemaVersion": 3,
        "generatedAt": "2026-07-11T10:15:00Z",
        "opId": "op-20260711-veil-ledger-demo",
        "firmware": "flipper69",
        "firmwareVersion": "3.0.0",
        "releaseCodename": "VEIL LEDGER",
        "classification": "UNCLASSIFIED//FRI",
        "verifyCount": 1,
        "chainPrev": None,
        "items": items,
    }
    man_path = OP / "CASEFILE-MANIFEST.json"
    man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8", newline="\n")

    # self-check
    bad = [i["path"] for i in items if sha256(OP / i["path"]) != i["hash"]]
    print("sealed", OP)
    print("manifest_sha256", sha256(man_path))
    print("mismatches", bad)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
