"""SD import and vault sync with hash verification."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flipper69.hashutil import sha256_file
from flipper69.vault import ensure_vault, operations_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_timeline(op_path: Path, event: str, data: dict[str, Any] | None = None) -> None:
    line = {
        "ts": _utc_now(),
        "event": event,
        "source": "flipper69-desktop",
        "ver": "3.0.0",
        "data": data or {},
    }
    with (op_path / "TIMELINE.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, separators=(",", ":")) + "\n")


def verify_manifest_items(op_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    ok = 0
    mismatch: list[str] = []
    missing: list[str] = []
    items = manifest.get("items") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        rel = item.get("path")
        expected = item.get("hash")
        if not rel or not expected:
            continue
        art = op_path / rel
        if not art.is_file():
            missing.append(rel)
            continue
        actual = sha256_file(art)
        if actual.lower() == str(expected).lower():
            ok += 1
        else:
            mismatch.append(rel)
    return {
        "ok": ok,
        "mismatch": mismatch,
        "missing": missing,
        "pass": not mismatch and not missing,
    }


def find_sd_ops_root(sd_root: Path) -> Path:
    """Accept SD root, flipper69 root, or operations parent."""
    candidates = [
        sd_root / "flipper69" / "operations",
        sd_root / "operations",
        sd_root,
    ]
    for c in candidates:
        if c.is_dir() and any(p.name.startswith("op-") for p in c.iterdir() if p.is_dir()):
            return c
    # nested examples/sd_card/flipper69/operations
    nested = sd_root / "flipper69" / "operations"
    if nested.is_dir():
        return nested
    raise FileNotFoundError(f"No flipper69/operations under {sd_root}")


def import_sd(
    sd_root: Path,
    ops_root: Path | None = None,
    *,
    overwrite: bool = True,
) -> dict[str, Any]:
    ensure_vault(ops_root)
    src_ops = find_sd_ops_root(sd_root)
    dest_ops = operations_dir(ops_root)

    imported = 0
    verified_hashes = 0
    results: list[dict[str, Any]] = []

    for op_dir in sorted(src_ops.iterdir()):
        if not op_dir.is_dir() or not op_dir.name.startswith("op-"):
            continue
        target = dest_ops / op_dir.name
        if target.exists() and overwrite:
            shutil.rmtree(target)
        if not target.exists():
            shutil.copytree(op_dir, target)

        # Verify BEFORE appending any desktop timeline receipts (preserves TIMELINE hash).
        man_path = target / "CASEFILE-MANIFEST.json"
        vresult: dict[str, Any] = {"ok": 0, "mismatch": [], "missing": [], "pass": True}
        if man_path.is_file():
            try:
                manifest = json.loads(man_path.read_text(encoding="utf-8"))
                vresult = verify_manifest_items(target, manifest)
                verified_hashes += vresult["ok"]
            except json.JSONDecodeError:
                vresult["pass"] = False
                append_timeline(target, "manifest_parse_error", {})

        # Receipts go to DESKTOP-RECEIPTS.jsonl so CASEFILE TIMELINE hashes stay valid.
        receipt_path = target / "DESKTOP-RECEIPTS.jsonl"
        receipt = {
            "ts": _utc_now(),
            "event": "sd_import",
            "source": "flipper69-desktop",
            "ver": "3.0.0",
            "data": {
                "source": str(sd_root),
                "verify_pass": vresult.get("pass", False),
                "ok": vresult.get("ok", 0),
                "mismatch": vresult.get("mismatch", []),
                "missing": vresult.get("missing", []),
            },
        }
        with receipt_path.open("a", encoding="utf-8") as rf:
            rf.write(json.dumps(receipt, separators=(",", ":")) + "\n")

        imported += 1
        results.append({"opId": op_dir.name, "path": str(target), **vresult})

    # copy index if present
    index_src = src_ops.parent / "index.json"
    if index_src.is_file() and ops_root:
        shutil.copy2(index_src, Path(ops_root) / "index.json")
    elif index_src.is_file():
        from flipper69.vault import default_ops_root

        shutil.copy2(index_src, default_ops_root() / "index.json")

    return {
        "imported": imported,
        "hashes_ok": verified_hashes,
        "results": results,
        "vault": str(dest_ops),
    }
