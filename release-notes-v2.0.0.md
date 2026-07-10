# Fl1pp3r69 v2.0.0

Manifest-driven Flipper Zero field ops — Momentum base, CASEFILE discipline, SHA-256 chain from pocket to desktop.

## Install

```powershell
py -m pip install --upgrade ufbt
.\scripts\build-fap.ps1 -App all
```

Copy FAPs from `dist/` to SD:

- `apps/flipper69_casefile_ops.fap`
- `apps/NFC/flipper69_probe_nfc.fap`
- `apps/flipper69_probe_subghz.fap`
- `apps/flipper69_manifest_viewer.fap`

MIT License.
