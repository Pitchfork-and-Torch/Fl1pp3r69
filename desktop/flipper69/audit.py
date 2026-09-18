"""Manifest audit, orphans, chain continuity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flipper69.hashutil import sha256_file
from flipper69.sync import verify_manifest_items
from flipper69.vault import iter_ops, read_manifest, read_operation


def list_capture_files(op_dir: Path) -> list[Path]:
    cap = op_dir / "captures"
    if not cap.is_dir():
        return []
    return [p for p in cap.rglob("*") if p.is_file() and not p.name.startswith(".")]


def audit_op(op_dir: Path) -> dict[str, Any]:
    op = read_operation(op_dir)
    man = read_manifest(op_dir)
    issues: list[str] = []
    warnings: list[str] = []

    if not op:
        issues.append("missing OPERATION.json")
    if not man:
        warnings.append("no CASEFILE-MANIFEST.json (unsealed)")

    verify: dict[str, Any] = {"ok": 0, "mismatch": [], "missing": [], "pass": True}
    if man:
        verify = verify_manifest_items(op_dir, man)
        for m in verify["mismatch"]:
            issues.append(f"hash mismatch: {m}")
        for m in verify["missing"]:
            issues.append(f"missing artifact: {m}")

    # orphan captures not listed in manifest
    listed: set[str] = set()
    if man:
        for item in man.get("items") or []:
            if isinstance(item, dict) and item.get("path"):
                listed.add(str(item["path"]).replace("\\", "/"))

    orphans: list[str] = []
    for f in list_capture_files(op_dir):
        rel = f.relative_to(op_dir).as_posix()
        if rel not in listed:
            orphans.append(rel)
    if orphans:
        warnings.append(f"{len(orphans)} orphan capture(s) not in manifest")

    schema = None
    if man and "schemaVersion" in man:
        schema = man.get("schemaVersion")
    elif op and "schemaVersion" in op:
        schema = op.get("schemaVersion")
    else:
        schema = 2
        warnings.append("legacy v2 document (no schemaVersion)")

    chain_prev = man.get("chainPrev") if man else None
    status = "PASS" if not issues else "FAIL"

    return {
        "opId": op_dir.name,
        "path": str(op_dir),
        "status": status,
        "schemaVersion": schema,
        "phase": (op or {}).get("phase"),
        "opType": (op or {}).get("opType"),
        "manifestHash": (op or {}).get("manifestHash"),
        "verify": verify,
        "orphans": orphans,
        "chainPrev": chain_prev,
        "issues": issues,
        "warnings": warnings,
    }


def audit_vault(ops_root: Path | None = None) -> dict[str, Any]:
    reports = [audit_op(p) for p in iter_ops(ops_root)]
    # conflict detection: same opId only once on disk; check hash collisions across copies N/A
    passed = sum(1 for r in reports if r["status"] == "PASS")
    failed = sum(1 for r in reports if r["status"] == "FAIL")
    return {
        "ops": len(reports),
        "passed": passed,
        "failed": failed,
        "reports": reports,
    }


def recompute_manifest_hash(op_dir: Path) -> str | None:
    man = op_dir / "CASEFILE-MANIFEST.json"
    if not man.is_file():
        return None
    return sha256_file(man)
