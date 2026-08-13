"""Lightweight vault browser TUI (stdlib only). Falls back gracefully."""

from __future__ import annotations

from flipper69.audit import audit_vault
from flipper69.vault import default_ops_root, iter_ops, read_operation


def run_tui() -> int:
    root = default_ops_root()
    print()
    print("  +----------------------------------------------+")
    print("  |  FL1PP3R69 VEIL LEDGER  vault browser        |")
    print(f"  |  {str(root)[:42]:<42} |")
    print("  +----------------------------------------------+")
    print()

    ops = list(iter_ops(root))
    if not ops:
        print("  (empty vault — run: flipper69 sync --sd <path>)")
        return 0

    for i, op_dir in enumerate(ops, 1):
        op = read_operation(op_dir) or {}
        phase = op.get("phase", "?")
        otype = op.get("opType", "?")
        print(f"  [{i:02d}] {op_dir.name}")
        print(f"       type={otype}  phase={phase}  schema={op.get('schemaVersion', 2)}")

    print()
    summary = audit_vault(root)
    print(f"  AUDIT  ops={summary['ops']}  PASS={summary['passed']}  FAIL={summary['failed']}")
    print("  Tip: flipper69 audit | flipper69 report <opId>")
    print()
    return 0
