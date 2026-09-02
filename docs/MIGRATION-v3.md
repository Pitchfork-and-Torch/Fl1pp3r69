# Migration Guide: v2.0 → v3.0 (VEIL LEDGER)

## What changes

| Area | v2 | v3 |
|------|----|----|
| Version stamp | 2.0.0 | 3.0.0 |
| Release codename | (none) | **VEIL LEDGER** |
| OPERATION.json | no schemaVersion | `schemaVersion: 3`, `session`, `releaseCodename` |
| CASEFILE-MANIFEST | hash list | + `schemaVersion`, `chainPrev`, `verifyCount` |
| Active op | latest-dir heuristic | `ACTIVE_OP.json` |
| Recovery | none | `CHECKPOINT.json` |
| Probes | NFC + Sub-GHz | + **EMBER_TRACE** IR |
| Desktop | PowerShell only | **Python `flipper69` package** + PS1 retained |

**Unchanged:** phase spine, ethics, panic two-step, deliberate exfil, SHA-256 integrity model.

## Device upgrade

1. Build FAPs: `.\scripts\build-fap.ps1 -App all`
2. Copy to SD:
   - `flipper69_casefile_ops.fap` → `apps/`
   - `flipper69_probe_nfc.fap` → `apps/NFC/`
   - `flipper69_probe_subghz.fap` → `apps/`
   - `flipper69_probe_ir.fap` → `apps/` (or Infrared)
   - `flipper69_manifest_viewer.fap` → `apps/`
3. Open CASEFILE Ops — existing open ops are resumed via OPERATION.json; first save writes ACTIVE_OP + CHECKPOINT.
4. Re-VERIFY ops before EXFIL after upgrade (new manifest fields).

v2 ops remain readable. Probes still fall back to newest `op-*` if ACTIVE_OP missing.

## Desktop vault upgrade

```bash
cd desktop
pip install -e .
python -m flipper69 migrate
python -m flipper69 audit
```

Or with explicit vault:

```bash
python -m flipper69 migrate --vault %USERPROFILE%\.flipper69\ops
```

Migration is **idempotent** and does **not** rewrite capture file hashes.

## PowerShell bridge

`sync/flipper69-sync.ps1` remains supported for USB serial and SD import. Prefer:

```bash
python -m flipper69 sync --sd E:\
```

## Rollback

- Keep v2 FAPs as SD backup.
- Vault files remain JSON; removing schemaVersion fields is optional (v3 tools accept v2).
- Do not mix EXFIL of half-migrated multi-device copies without `audit`.

## Template note

Desktop templates require `--acknowledge-auth` so authorization is never silent.
