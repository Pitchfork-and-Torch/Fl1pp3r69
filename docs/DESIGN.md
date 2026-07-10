# FLIPPER69 — Design Specification

**Codename:** FL1PP3R69  
**Classification:** UNCLASSIFIED // FIELD RESEARCH ONLY  
**Version:** 2.0.0  
**Date:** 2026-07-08

---

## Mission Statement

Flipper69 is a custom Flipper Zero firmware distribution and FAP suite for **physical-layer security research**. It is a **field instrument** with manifest integrity, staged operations, and chain-of-custody — synced to a desktop case-management hub.

> *"The dolphin grew teeth."*

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Manifest everything** | SHA-256 on every capture before it leaves the device |
| **Staged ops only** | No raw tool sprawl — everything runs inside a CASEFILE operation |
| **Exploits excluded** | Field captures and metadata only; zero exploit code on device |
| **Exfil is deliberate** | VERIFY → EXFIL → CLOSE; nothing auto-uploads |
| **OPSEC by default** | BT advertising off during ops; TX audit log; panic wipe |
| **Badass without felony** | Aggressive UX, restrained legal surface |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FLIPPER69 FIRMWARE LAYER                   │
│  Boot: glitch splash │ theme: obsidian/red │ dolphin→viper     │
│  Patches: default OPSEC, CASEFILE home screen, serial bridge   │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                     FAP SUITE (applications)                  │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────────┐ │
│  │ casefile_ops│ │ probe_subghz │ │ probe_nfc / ir / gpio  │ │
│  │  (hub)      │ │              │ │  (phase plugins)       │ │
│  └─────────────┘ └──────────────┘ └────────────────────────┘ │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────────┐ │
│  │manifest_view│ │ op_prep      │ │ panic_wipe             │ │
│  └─────────────┘ └──────────────┘ └────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │ SD + USB serial
┌────────────────────────────▼─────────────────────────────────┐
│              DESKTOP: SYNC BRIDGE                             │
│  flipper69-sync.ps1 → .flipper69/ops/operations/             │
│  manifest verify │ timeline merge │ audit                     │
└──────────────────────────────────────────────────────────────┘
```

### Deployment Strategy (v2)

1. **FAP suite (primary)** — CASEFILE + probes; runs on stock, Unleashed, Momentum, or RogueMaster.
2. **Momentum overlay** — `firmware/flipper69/` patches, theme, OPSEC defaults via scripts.
3. **Desktop bridge** — USB serial exfil + SD import with SHA-256 verify.
4. **Future** — baked boot autostart (P2) and full serial service (P4) still staged in patches/.

---

## Operation Model

Inspired by staged `OP_PREP` workflows and CASEFILE manifest discipline.

### Op Types (field-native)

| Type | Code | Use |
|------|------|-----|
| `proximity` | PX | Single-target RF/NFC/IR capture at range |
| `survey` | SV | Passive scan sweep (Sub-GHz, NFC, BLE advertise) |
| `replay` | RP | Authorized replay test against owned hardware |
| `inject` | IN | BadUSB / GPIO script run (lab targets only) |
| `unified` | UN | Multi-phase: survey → capture → verify → exfil |

### Phases

```
INTAKE → OP_PREP → PROBE → CAPTURE → VERIFY → EXFIL → CLOSE
```

| Phase | Device behavior |
|-------|-----------------|
| **INTAKE** | Name op, select type, set target notes |
| **OP_PREP** | Generate `opId`, write `OPERATION.json`, disable BT adv |
| **PROBE** | Launch domain plugin (Sub-GHz / NFC / IR / BadUSB / GPIO) |
| **CAPTURE** | Save raw + parsed artifact to op folder |
| **VERIFY** | SHA-256 all items → `CASEFILE-MANIFEST.json` |
| **EXFIL** | USB serial push or SD export marker |
| **CLOSE** | Seal op, restore radio defaults, append `TIMELINE.jsonl` |

### Storage Layout (SD card)

```
/ext/flipper69/
  index.json
  operations/
    op-20260706-field-001/
      OPERATION.json
      TIMELINE.jsonl
      CASEFILE-MANIFEST.json
      captures/
        subghz_43392_raw.sub
        nfc_mifare_classic.dump
        ir_signal.ir
      notes.txt
```

---

## FAP: casefile_ops (Command Hub)

The home screen replacement. Numbered menu, tactical aesthetic.

```
╔══════════════════════════════════════╗
║  FLIPPER69 // CASEFILE OPS           ║
║  ──────────────────────────────────  ║
║  [1] NEW OPERATION                   ║
║  [2] RESUME OPERATION                ║
║  [3] RUN PHASE (auto)                ║
║  [4] VERIFY MANIFEST                 ║
║  [5] EXFIL TO DESKTOP                ║
║  [6] AUDIT / ORPHAN SCAN             ║
║  [7] OPSEC TOGGLE                    ║
║  [8] PANIC WIPE                      ║
║  ──────────────────────────────────  ║
║  ACTIVE: op-20260706-field-001 [PROBE] ║
║  MANIFEST: a3f8…c21d  ✓               ║
╚══════════════════════════════════════╝
```

### Key bindings

- **OK** — select menu item
- **Back** — abort phase (writes `phase_aborted` to timeline)
- **Up+Down hold 2s** — panic wipe (confirm screen)
- **Left+Right hold 1s** — quick OPSEC toggle

---

## Probe Plugins

Each probe is a FAP that accepts an active `opId` via `storage` and writes captures into the op folder.

### probe_subghz

- Raw capture with frequency, preset, RSSI metadata
- Rolling code detector (flags, does not break)
- `rolling_code_detected: true` in capture metadata JSON sidecar
- Output: `.sub` + `.meta.json`

### probe_nfc

- UID read, type detection, MIFARE Classic dump (authorized)
- Emulation session log (what was emulated, when, duration)
- Output: `.nfc` / `.dump` + `.meta.json`

### probe_ir (v1.1)

- Capture + protocol ID
- Output: `.ir` + `.meta.json`

### probe_badusb (v1.1)

- Runs DuckyScript from `/ext/flipper69/scripts/` only
- Requires op type `inject` + explicit confirm
- Logs script hash in manifest before execution

---

## Serial Sync Protocol

USB CDC serial at 115200 baud. JSON-lines, one message per line.

### Device → Desktop (`exfil`)

```json
{"type":"op_header","opId":"op-20260706-field-001","opType":"proximity","phase":"exfil"}
{"type":"manifest","opId":"op-20260706-field-001","generatedAt":"2026-07-06T14:22:01Z","items":[...]}
{"type":"artifact","opId":"...","path":"captures/subghz_43392_raw.sub","sha256":"...","b64":"..."}
{"type":"op_close","opId":"...","manifestHash":"..."}
```

### Desktop → Device (`ack`)

```json
{"type":"ack","opId":"...","status":"stored","desktopPath":".flipper69/ops/operations/..."}
```

PowerShell bridge: `sync/flipper69-sync.ps1` — listens on COM port, writes to the local ops tree, verifies SHA-256 hashes.

---

## Firmware Patches (Thin Layer)

| Patch | File | Effect |
|-------|------|--------|
| Boot splash | `assets/boot_anim.txt` | Glitch FLIPPER69 logo sequence |
| Icon pack | `assets/icons/` | Obsidian/red dolphin-viper hybrid |
| Default OPSEC | `firmware/patches/opsec_defaults.c` | BT off, name generic, TX log on |
| Home redirect | `firmware/patches/desktop_api.c` | Boot → casefile_ops FAP |
| Serial bridge | `firmware/patches/flipper69_serial.c` | CDC JSON-lines exfil |

---

## Visual Identity

### Palette

- **Obsidian** `#0a0a0c` — backgrounds
- **Blood red** `#c41e1e` — accents, active phase
- **Phosphor green** `#39ff14` — manifest verified
- **Amber** `#ffb000` — warnings, rolling code flags
- **Ghost** `#8b8b8b` — inactive menu items

### Boot sequence (128×64 OLED)

1. Static noise burst (4 frames)
2. `FLIPPER` slams in from left
3. `69` flickers in phosphor green
4. Line: `UNCLASSIFIED // FIELD RESEARCH ONLY`
5. Manifest hash of firmware build scrolls (proves build integrity)
6. Fade to CASEFILE OPS hub

### Mascot

The stock dolphin silhouette with a segmented viper tail, red eye slit. File: `assets/mascot_spec.md`.

---

## Ethics & Legal Guardrails (hard-coded)

1. **No exploit binaries** on SD or in firmware.
2. **No offensive network tooling** — field captures and manifests only.
3. **Replay and inject phases** require typed confirmation string: `AUTHORIZED`.
4. **TX regions** — respect `Region` setting; warn on EU restricted bands.
5. **Panic wipe** — zeroes `/ext/flipper69/operations/` metadata (not base firmware).

---

## Roadmap

### v0.1 — Foundation (current scaffold)
- [x] Design spec
- [x] JSON schemas
- [x] FAP stubs + sync bridge skeleton
- [x] casefile_ops FAP compile via ufbt (SDK 1.4.3, API 87.1)
- [ ] flipper69-sync.ps1 COM listener

### v0.2 — Probes
- [ ] probe_subghz with meta sidecars
- [x] probe_nfc — read / write / emulate with meta sidecars (v0.3)
- [ ] manifest_viewer FAP

### v0.3 — Firmware skin
- [ ] Boot animation asset compile
- [ ] Icon pack
- [ ] OPSEC defaults patch

### v0.4 — Desktop integration
- [ ] Desktop hub `opType: field` registration
- [ ] Auto brief section for Flipper captures
- [ ] Metadata cross-reference (local index only)

### v1.0 — FLIPPER69 Release
- [ ] Full firmware fork tagged `flipper69-v1.0.0`
- [ ] Build reproducibility manifest
- [ ] Field test checklist

---

## Success Criteria

Flipper69 v1.0 is done when:

1. A full **unified** op can run on-device without a PC.
2. EXFIL to desktop produces a valid `CASEFILE-MANIFEST.json` that passes hash verification.
3. Boot + UI are unmistakably Flipper69 — not stock, not generic dark mode.
4. Zero exploit code exists in the repo.

---

*The dolphin grew teeth. The manifest keeps the bite legal.*