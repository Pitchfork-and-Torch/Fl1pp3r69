# Fl1pp3r69 v3.0.0

Fl1pp3r69 - manifest-driven Flipper Zero field ops. The dolphin grew teeth.

## Install

```powershell
py -m pip install --upgrade ufbt
.\scripts\build-fap.ps1 -App all
```

Copy FAPs from `dist/` to SD:

- `apps/flipper69_casefile_ops.fap`
- `apps/NFC/flipper69_probe_nfc.fap`
- `apps/flipper69_probe_subghz.fap`
- `apps/flipper69_probe_ir.fap`
- `apps/flipper69_manifest_viewer.fap`

Desktop toolkit (optional):

```bash
pip install -e ./desktop
python -m flipper69 sync --sd E:\
```

MIT License.
