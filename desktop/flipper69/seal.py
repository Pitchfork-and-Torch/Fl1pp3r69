"""v4 merkle / deep seal helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flipper69.hashutil import sha256_file
from flipper69.vault import load_json


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _merkle_root(hashes: list[str]) -> str:
    if not hashes:
        return hashlib.sha256(b"").hexdigest()
    level = [bytes.fromhex(h) for h in hashes]
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(hashlib.sha256(left + right).digest())
        level = nxt
    return level[0].hex()


def collect_sealable_files(op_dir: Path) -> list[Path]:
    files: list[Path] = []
    for name in ("OPERATION.json", "TIMELINE.jsonl", "notes.txt", "CHECKPOINT.json", "ROE.json"):
        p = op_dir / name
        if p.is_file():
            files.append(p)
    for sub in ("captures", "artifacts", "scripts", "claims", "manifests"):
        root = op_dir / sub
        if root.is_dir():
            for p in sorted(root.rglob("*")):
                if p.is_file() and p.name != "CASEFILE-MANIFEST.json":
                    files.append(p)
    return files


def seal_op(op_dir: Path, *, merkle: bool = True, chunk_size: int = 64) -> dict[str, Any]:
    files = collect_sealable_files(op_dir)
    items: list[dict[str, Any]] = []
    leaf_hashes: list[str] = []
    for p in files:
        rel = p.relative_to(op_dir).as_posix()
        h = sha256_file(p)
        leaf_hashes.append(h)
        domain = "field"
        parts = rel.split("/")
        if len(parts) >= 2 and parts[0] == "artifacts":
            domain = parts[1]
        elif rel.startswith("captures/"):
            domain = "field"
        items.append(
            {
                "type": "capture" if "captures" in rel or "artifacts" in rel else "metadata",
                "artifactClass": "meta" if rel.endswith(".meta.json") else "raw" if "/" in rel else "note",
                "domain": domain,
                "path": rel,
                "hash": h,
                "sizeBytes": p.stat().st_size,
            }
        )

    root = _merkle_root(leaf_hashes) if merkle else None
    parts_meta: list[dict[str, Any]] = []
    if len(items) > chunk_size:
        man_dir = op_dir / "manifests" / "parts"
        man_dir.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(items), chunk_size):
            chunk = items[i : i + chunk_size]
            part_path = man_dir / f"part-{i // chunk_size:02d}.json"
            part_path.write_text(json.dumps({"items": chunk}, indent=2) + "\n", encoding="utf-8")
            parts_meta.append(
                {
                    "path": part_path.relative_to(op_dir).as_posix(),
                    "hash": sha256_file(part_path),
                    "itemCount": len(chunk),
                }
            )

    manifest: dict[str, Any] = {
        "schemaVersion": 4,
        "generatedAt": _utc_now(),
        "opId": op_dir.name,
        "firmware": "flipper69",
        "firmwareVersion": "4.0.0",
        "releaseCodename": "ARGUS VEIL",
        "classification": "UNCLASSIFIED//FRI",
        "verifyCount": 1,
        "chainPrev": None,
        "sealAlg": "sha256-merkle-v1" if merkle else ("sha256-chunked-v1" if parts_meta else "sha256"),
        "merkleRoot": root,
        "items": items if not parts_meta else [],
    }
    if parts_meta:
        manifest["parts"] = parts_meta

    prev = op_dir / "CASEFILE-MANIFEST.json"
    if prev.is_file():
        try:
            manifest["chainPrev"] = sha256_file(prev)
            old = load_json(prev)
            if isinstance(old, dict) and isinstance(old.get("verifyCount"), int):
                manifest["verifyCount"] = old["verifyCount"] + 1
        except OSError:
            pass
        manifests_dir = op_dir / "manifests"
        manifests_dir.mkdir(exist_ok=True)
        (manifests_dir / "CASEFILE-MANIFEST.prev.json").write_bytes(prev.read_bytes())

    # Write primary manifest path (v3 compat at root + v4 manifests/)
    body = json.dumps(manifest, indent=2) + "\n"
    (op_dir / "CASEFILE-MANIFEST.json").write_text(body, encoding="utf-8")
    (op_dir / "manifests").mkdir(exist_ok=True)
    (op_dir / "manifests" / "CASEFILE-MANIFEST.json").write_text(body, encoding="utf-8")
    if root:
        (op_dir / "manifests" / "MERKLE.json").write_text(
            json.dumps({"merkleRoot": root, "leaves": len(leaf_hashes), "alg": "sha256-merkle-v1"}, indent=2)
            + "\n",
            encoding="utf-8",
        )

    op = load_json(op_dir / "OPERATION.json")
    if isinstance(op, dict):
        op["schemaVersion"] = 4
        op["releaseCodename"] = "ARGUS VEIL"
        op["manifestHash"] = sha256_file(op_dir / "CASEFILE-MANIFEST.json")
        op["seal"] = {
            "alg": manifest["sealAlg"],
            "manifestPath": "CASEFILE-MANIFEST.json",
            "merkleRoot": root,
            "itemCount": len(items),
        }
        (op_dir / "OPERATION.json").write_text(json.dumps(op, indent=2) + "\n", encoding="utf-8")

    return {
        "opId": op_dir.name,
        "items": len(items),
        "merkleRoot": root,
        "sealAlg": manifest["sealAlg"],
        "chunked": bool(parts_meta),
    }
