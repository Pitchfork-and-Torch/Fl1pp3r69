"""SD import and vault sync with hash verification."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flipper69 import __version__
from flipper69.hashutil import sha256_file
from flipper69.vault import ensure_vault, operations_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_timeline(op_path: Path, event: str, data: dict[str, Any] | None = None) -> None:
    line = {
        "ts": _utc_now(),
        "event": event,
        "source": "flipper69-desktop",
        "ver": __version__,
        "data": data or {},
    }
    with (op_path / "TIMELINE.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, separators=(",", ":")) + "\n")


def resolve_manifest_items(op_path: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Inline items, or flatten chunked part manifests when items were spilled."""
    raw = manifest.get("items") or []
    items = [i for i in raw if isinstance(i, dict)]
    if items:
        return items
    parts = manifest.get("parts") or []
    resolved: list[dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        rel = part.get("path")
        if not rel:
            continue
        part_file = op_path / str(rel)
        if not part_file.is_file():
            continue
        try:
            data = json.loads(part_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        for item in data.get("items") or []:
            if isinstance(item, dict):
                resolved.append(item)
    return resolved


def verify_manifest_items(op_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    ok = 0
    mismatch: list[str] = []
    missing: list[str] = []
    items = resolve_manifest_items(op_path, manifest)
    for part in manifest.get("parts") or []:
        if not isinstance(part, dict):
            continue
        rel = part.get("path")
        expected = part.get("hash")
        if not rel or not expected:
            continue
        art = op_path / str(rel)
        if not art.is_file():
            missing.append(str(rel))
            continue
        actual = sha256_file(art)
        if actual.lower() == str(expected).lower():
            ok += 1
        else:
            mismatch.append(str(rel))
    for item in items:
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
    if (manifest.get("parts") or []) and not items and ok == 0 and not mismatch and not missing:
        missing.append("(chunked parts unreadable)")
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
            "ver": __version__,
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
