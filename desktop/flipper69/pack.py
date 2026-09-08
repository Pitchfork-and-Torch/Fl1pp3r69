"""Export operation packs (full or redact/share-safe)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from flipper69.hashutil import sha256_file
from flipper69.vault import read_manifest, read_operation


REDACT_SKIP_NAMES = {"notes.txt"}
REDACT_SKIP_PREFIX = ("captures/",)


def pack_op(
    op_dir: Path,
    out_zip: Path,
    *,
    redact: bool = False,
) -> dict:
    op = read_operation(op_dir) or {}
    man = read_manifest(op_dir) or {}
    files: list[tuple[str, Path]] = []

    for path in op_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(op_dir).as_posix()
        if redact:
            if path.name in REDACT_SKIP_NAMES:
                continue
            if rel.startswith(REDACT_SKIP_PREFIX) and not rel.endswith(".meta.json"):
                # share-safe: keep only meta sidecars from captures
                continue
            if rel == "OPERATION.json":
                # write redacted operation later
                continue
        files.append((rel, path))

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, path in files:
            zf.write(path, arcname=f"{op_dir.name}/{rel}")
        if redact:
            red_op = dict(op)
            if "target" in red_op and isinstance(red_op["target"], dict):
                red_op["target"] = {
                    "label": "[REDACTED]",
                    "notes": "",
                    "authorized": red_op["target"].get("authorized", False),
                }
            zf.writestr(
                f"{op_dir.name}/OPERATION.json",
                json.dumps(red_op, indent=2) + "\n",
            )
            zf.writestr(
                f"{op_dir.name}/REDACT.txt",
                "Share-safe pack: notes and raw captures omitted; hashes preserved where present.\n",
            )
        # root hash of zip contents listing
        listing = "\n".join(sorted(r for r, _ in files))
        zf.writestr(f"{op_dir.name}/PACK.manifest.txt", listing + "\n")

    return {
        "path": str(out_zip),
        "sha256": sha256_file(out_zip),
        "redact": redact,
        "opId": op_dir.name,
        "manifestItems": len(man.get("items") or []),
    }
