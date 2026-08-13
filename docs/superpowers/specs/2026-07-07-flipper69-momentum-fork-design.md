# Fl1pp3r69 × Momentum Firmware Fork — Design Spec

**Version:** 1.0-draft  
**Date:** 2026-07-07  
**Decision:** Option B — full firmware distro forked from [Next-Flip/Momentum-Firmware](https://github.com/Next-Flip/Momentum-Firmware)  
**Repo:** `Pitchfork-and-Torch/Fl1pp3r69`

---

## Goal

Ship **Fl1pp3r69 v1.0** as a installable firmware image that:

1. Inherits Momentum (OFW + Unleashed protocol/UI wins) without maintaining three separate rebases.
2. Boots into **CASEFILE Ops** as the field instrument home screen.
3. Bakes in all four Fl1pp3r69 FAPs with manifest discipline intact.
4. Keeps hard ethics guardrails from `docs/DESIGN.md` (no exploits, `AUTHORIZED` gates, regional TX respect).

---

## Upstream Map

| Layer | Source | What we inherit |
|-------|--------|-----------------|
| Core | `flipperdevices/flipperzero-firmware` | API stability, HAL |
| Protocols | `DarkFlippers/unleashed-firmware` (via Momentum merges) | Extended Sub-GHz, NFC parsers, rolling-code flags |
| UX | `Next-Flip/Momentum-Firmware` | Themes, animations, pin lock, clock, BadKB shell |
| Identity | **Fl1pp3r69** | CASEFILE ops, SHA-256 manifests, serial exfil, OPSEC defaults |

**Explicitly excluded:** jamming packs, RogueMaster plugin soup, TX region bypass, ungated bruteforce.

---

## Repository Layout

```
Flipper69/
├── fap/                          # FAP sources (canonical)
├── firmware/
│   ├── momentum/                 # git submodule → Next-Flip/Momentum-Firmware (not committed binary)
│   └── flipper69/
│       ├── MANIFEST.json         # upstream pin + patch registry
│       ├── applications/         # junction targets for fbt build
│       ├── patches/              # overlay C patches applied into momentum tree
│       └── theme/                # Momentum-compatible theme pack
├── scripts/
│   ├── init-firmware-fork.ps1    # clone submodule + junctions
│   ├── apply-flipper69-patches.ps1
│   ├── sync-faps-to-firmware.ps1
│   └── build-firmware.ps1
└── dist/                         # FAP artifacts (ufbt) + firmware updater output
```

---

## Boot Flow

```
Power on
  → Momentum boot animation replaced by Fl1pp3r69 glitch splash
  → flipper69_apply_opsec_defaults()  (BT adv off, TX audit on)
  → Desktop loads with Fl1pp3r69 theme (obsidian/red)
  → flipper69_desktop_autostart() launches CASEFILE Ops FAP
  → User runs staged op; probes write to /ext/flipper69/operations/
  → EXFIL over USB serial JSON-lines when user selects [5]
```

---

## Patch Registry

| Patch | Target in Momentum tree | Effect |
|-------|-------------------------|--------|
| `opsec_defaults.c` | `applications/services/flipper69/` (new service) | OPSEC defaults at boot |
| `desktop_autostart.c` | Desktop service hook | Boot → CASEFILE Ops |
| `flipper69_serial.c` | USB CDC handler extension | JSON-lines exfil |
| `boot_anim/` | `assets/animations/` | Glitch FLIPPER69 splash |

Patches are **copied** into the momentum tree by `apply-flipper69-patches.ps1` (idempotent). Never edit momentum/ by hand.

---

## FAP Integration

All four FAPs build **inside** the momentum tree via fbt:

| FAP | Build path | Install in image |
|-----|------------|------------------|
| `flipper69_casefile_ops` | `applications/external/flipper69/casefile_ops/` | Pre-packaged + SD default |
| `flipper69_probe_nfc` | `.../probe_nfc/` | `apps/NFC/` |
| `flipper69_probe_subghz` | `.../probe_subghz/` | `apps/` |
| `flipper69_manifest_viewer` | `.../manifest_viewer/` | `apps/` |

Sources remain canonical in `fap/`; `sync-faps-to-firmware.ps1` mirrors via directory junctions.

---

## Unleashed Features Routed Through CASEFILE

| Native feature | Fl1pp3r69 integration |
|----------------|----------------------|
| Sub-GHz protocol names in filenames | `probe_subghz` writes matching `.meta.json` |
| Rolling code detection | Flag in meta sidecar, amber UI in manifest viewer |
| NFC parsers | Optional parser output appended to DEWDROP meta |
| Frequency analyzer | Linked from survey op phase menu |
| BadKB | Only via `inject` op + `AUTHORIZED` confirm |

---

## Build & Release

```powershell
.\scripts\init-firmware-fork.ps1      # once: clone momentum submodule
.\scripts\sync-faps-to-firmware.ps1  # junction fap/ → momentum tree
.\scripts\apply-flipper69-patches.ps1
.\scripts\build-firmware.ps1         # fbt updater_package + fap_dist
```

Output: `dist/firmware/flipper69-<version>.tgz` + `BUILD_MANIFEST.json` with firmware SHA-256.

Flash via qFlipper development channel or web updater (private hosting).

---

## GPL Compliance

- Fork stays private until deliberate open-source decision.
- Momentum/Unleashed/OFW are GPL-3.0 — distributing binaries requires source availability to recipients.
- `MANIFEST.json` records exact upstream commit SHA for reproducibility.

---

## Success Criteria (v1.0)

1. Flash image boots to CASEFILE Ops without manual FAP install.
2. Full unified op runs on-device without PC.
3. EXFIL produces verifiable `CASEFILE-MANIFEST.json` on desktop.
4. Unleashed Sub-GHz capture works inside op folder with meta sidecars.
5. Zero exploit binaries in repo or image.

---

## Phased Delivery

| Phase | Deliverable |
|-------|-------------|
| **P0** (this commit) | Submodule scaffold, patch registry, build scripts, spec |
| **P1** | First successful `fbt` build with junctioned FAPs |
| **P2** | Boot autostart + OPSEC patch wired |
| **P3** | Theme pack + boot animation |
| **P4** | Serial exfil bridge + desktop sync tested on hardware |
| **P5** | Tagged `flipper69-v1.0.0` private release |