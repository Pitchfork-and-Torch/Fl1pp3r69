# Fl1pp3r69 v1.0.0-alpha

Manifest-driven Flipper Zero field ops — Momentum base, CASEFILE discipline, SHA-256 chain from pocket to desktop.

## Install

### FAPs only (fastest)

```powershell
py -m pip install --upgrade ufbt
.\scripts\build-fap.ps1 -App all
```

Copy built `.fap` files from `dist/` to your SD card `apps/` folder. Open **CASEFILE Ops** on device.

### Full Momentum fork

```powershell
.\scripts\init-firmware-fork.ps1
.\scripts\sync-faps-to-firmware.ps1
.\scripts\apply-flipper69-patches.ps1
.\scripts\build-firmware.ps1 -Target all
```

MIT License.