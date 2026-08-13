# Fl1pp3r69 v4.0.0

Fl1pp3r69 - manifest-driven Flipper Zero field ops. The dolphin grew teeth.

ARGUS VEIL: CASEFILE hub with CLAIM, multi-domain probes (NFC, Sub-GHz, IR, LF RFID, iButton, BLE, GPIO, BadUSB meta), schema v4 manifests, and offline desktop toolkit (sync, seal, audit, report, dashboard).

## Install

### FAPs (device)

```powershell
py -m pip install --upgrade ufbt
.\scripts\build-fap.ps1 -App all
```

Or download release assets and copy to SD:

| FAP | SD path |
|-----|---------|
| flipper69_casefile_ops.fap | apps/ |
| flipper69_probe_nfc.fap | apps/NFC/ |
| flipper69_probe_subghz.fap | apps/ |
| flipper69_probe_ir.fap | apps/ |
| flipper69_probe_rfid.fap | apps/ |
| flipper69_probe_ibutton.fap | apps/ |
| flipper69_probe_ble.fap | apps/ |
| flipper69_probe_gpio.fap | apps/ |
| flipper69_probe_badusb.fap | apps/ |
| flipper69_manifest_viewer.fap | apps/ |

### Desktop

```bash
pip install -e ./desktop
python -m flipper69 sync --sd E:\
python -m flipper69 migrate
python -m flipper69 seal <opId>
python -m flipper69 audit
python -m flipper69 dashboard
```

Authorized research on owned hardware only. No exploit code.

MIT License.
