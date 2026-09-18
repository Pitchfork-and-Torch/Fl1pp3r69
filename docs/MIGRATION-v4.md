# Migration Guide: v3.0 → v4.0 (ARGUS VEIL)

## What changes

| Area | v3 | v4 |
|------|----|----|
| Codename | VEIL LEDGER | **ARGUS VEIL** |
| Version | 3.0.0 | 4.0.0 |
| schemaVersion | 3 | **4** |
| Captures | `captures/` only | `artifacts/<domain>/` + captures alias |
| Hub menu | 8 items | **9** — CLAIM ARTIFACT |
| Manifest cap | 24 | **64** inline (+ desktop chunk/merkle) |
| Probes | NFC, Sub-GHz, IR | + LODGE, BITKEY, HAZE, GPIO LAB, INKWELL |
| Desktop | sync audit report | + seal, serial, dashboard |

## Device

```powershell
.\scripts\build-fap.ps1 -App all
```

Copy all FAPs from `dist/`. Open CASEFILE — create or resume; CLAIM imports stock files into the active op.

## Desktop vault

```bash
pip install -e ./desktop
python -m flipper69 migrate
python -m flipper69 seal <opId>   # optional merkle re-seal
python -m flipper69 audit
```

Idempotent. Artifact hashes unchanged unless you re-seal.

## Compatibility

- Desktop reads schemaVersion 2–4.
- v3 ops remain valid; migrate stamps v4 fields and creates `artifacts/`.
