<p align="center">
  <img src="assets/fl1pp3r69-hero.png" alt="Fl1pp3r69 â€” the dolphin grew teeth" width="520">
</p>

<h1 align="center">Fl1pp3r69</h1>

<p align="center">
  <strong>The dolphin grew teeth.</strong><br>
  Manifest-driven Flipper Zero field ops â€” Momentum base, CASEFILE discipline, chain-of-custody from pocket to desktop.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-c41e1e?style=for-the-badge" alt="v2.0.0">
  <img src="https://img.shields.io/badge/API-87.1-39ff14?style=for-the-badge" alt="API 87.1">
  <img src="https://img.shields.io/badge/base-Momentum%20dev-8ed809f?style=for-the-badge" alt="Momentum dev">
  <img src="https://img.shields.io/badge/classification-UNCLASSIFIED%20%2F%2F%20FRI-0a0a0c?style=for-the-badge" alt="UNCLASSIFIED // FRI">
</p>

<p align="center">
  <code>4 FAPs Â· v2.0.0</code> Â· <code>API 87.3</code> Â· <code>SHA-256 manifest chain</code> Â· <code>phase HUD</code>
</p>

```
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  FL1PP3R69 // CASEFILE OPS              v2.0.0          â•‘
â•‘  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€  â•‘
â•‘  [1] NEW OPERATION    [5] EXFIL TO DESKTOP                â•‘
â•‘  [3] RUN PHASE        [7] OPSEC TOGGLE                    â•‘
â•‘  [I][P][B][C][V][E][X]   MANIFEST âœ“   OPSEC              â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
```

---

## Contents

- [What's new in v2](#whats-new-in-v2)
- [What makes this different](#what-makes-this-different)
- [The suite](#the-suite)
- [Operation pipeline](#operation-pipeline)
- [Quick start](#quick-start)
- [DEWDROP â€” NFC](#dewdrop--nfc-in-plain-english)
- [Desktop bridge](#desktop-bridge)
- [Identity & boot](#identity--boot)
- [Project map](#project-map)
- [Roadmap](#roadmap)
- [Ethics](#ethics)
- [Docs](#docs)

---

## What's new in v2

> **Product polish.** Same ethics surface, sharper instrument â€” HUD, op-type flow, dual-confirm panic, SD import, full version alignment.

| Area | v2 upgrade |
|------|------------|
| **CASEFILE UI** | Glitch splash, phase strip IÂ·PÂ·BÂ·CÂ·VÂ·EÂ·X, footer OPSEC badge, status toasts |
| **Create flow** | Op type â†’ PATHNUM â†’ seal (with hints) |
| **Panic** | Two-step ARM â†’ CONFIRM DESTRUCT |
| **Engine** | `index.json`, notes scaffold, capture counts, proper manifestHash JSON |
| **DEWDROP** | Ownership gate chrome, LIVE RF frame, ISO meta timestamps |
| **DAMP_CROWD** | Band menu (433 / 315 / 868 / generic) timestamped sidecars |
| **crypttool** | Multi-op browse, item counts, VERIFIED badge |
| **Desktop** | SD import + hash verify, banner, ping/pong |
| **Version** | **2.0.0** end-to-end (FAP, timeline, theme, MANIFEST) |

```mermaid
flowchart TB
  subgraph repo [Fl1pp3r69 Repo]
    FAP[fap/ sources v2]
    SCR[scripts/ pipeline]
    OVL[firmware/flipper69/ overlay]
    SYNC[sync/ desktop bridge]
  end
  subgraph local [Local Build]
    MNT[Momentum dev clone]
    FBT[fbt / ufbt build]
    DIST[dist/ artifacts]
  end
  FAP --> SCR
  SCR --> MNT
  OVL --> MNT
  MNT --> FBT --> DIST
  DIST --> SYNC
```

---

## What makes this different

Stock Flipper apps capture signals. **Fl1pp3r69 captures signals inside an operation** â€” named, typed, phased, hashed, and exfil-ready. No sprawl. No mystery files on your SD card. Every artifact gets a receipt.

| Everyone else | Fl1pp3r69 |
|---------------|-----------|
| Random `.sub` / `.nfc` in folders | Staged ops under `/ext/flipper69/operations/` |
| "I think I saved that Tuesday?" | `TIMELINE.jsonl` + `CASEFILE-MANIFEST.json` + `index.json` |
| Hope the file didn't change | SHA-256 before exfil |
| 200 menu items, no workflow | Numbered CASEFILE hub â†’ probe plugins |
| Generic CFW plugin soup | Momentum power, your ethics guardrails |

**Base firmware:** [Momentum](https://github.com/Next-Flip/Momentum-Firmware) â€” Unleashed protocol depth, polished UI, rolling-code flags.  
**Your layer:** CASEFILE ops, manifest chain, DEWDROP NFC, desktop sync, obsidian/red identity.

### What it is

| Layer | Role |
|-------|------|
| **CASEFILE Ops** | Manifest-driven hub â€” numbered menu, staged phases, dual-confirm panic wipe |
| **Probe plugins** | Sub-GHz, NFC â€” each writes SHA-256-ready `.meta.json` sidecars |
| **Desktop sync** | USB serial exfil **or** SD import with manifest verification |
| **Firmware skin** | Glitch boot, viper dolphin, obsidian/red theme *(overlay staged)* |

### What it is not

- Not a network exploitation platform â€” no WiFi, no kernel tools
- Not a general-purpose attack framework
- Not legal advice â€” authorized research on owned hardware only

### New here? Start in 60 seconds

1. Build FAPs â†’ copy to SD â†’ open **CASEFILE Ops**
2. **[1] NEW OPERATION** â†’ type â†’ pathnum â†’ run phases
3. **DEWDROP** reads your hotel key / Amiibo / access card â†’ saves to the op folder
4. **VERIFY** hashes everything â†’ **EXFIL** pushes to your PC (or pull SD + `-SdImport`)

No device yet? Simulate an op on desktop:

```powershell
cd sync
.\new-field-op.ps1 -OpType unified -Label "garage-test" -Pathnum ds
.\flipper69-sync.ps1 -SdImport ..\examples\sd_card
```

---

## The suite

| Codename | FAP | Role |
|----------|-----|------|
| **CASEFILE Ops** | `flipper69_casefile_ops` | Command hub â€” new/resume op, run phases, verify, exfil, panic wipe |
| **DEWDROP** | `flipper69_probe_nfc` | NFC read Â· write Â· emulate with `.meta.json` sidecars |
| **DAMP_CROWD** | `flipper69_probe_subghz` | Sub-GHz band sidecar (use stock Sub-GHz for raw capture) |
| **crypttool** | `flipper69_manifest_viewer` | On-device multi-op hash viewer |

```mermaid
flowchart LR
  subgraph device [Flipper Zero]
    BOOT[Momentum Boot]
    HUB[CASEFILE Ops]
    NFC[DEWDROP]
    RF[DAMP_CROWD]
    CRY[crypttool]
    BOOT --> HUB
    HUB --> NFC
    HUB --> RF
    HUB --> CRY
  end
  subgraph sd [SD Card]
    OPS["/ext/flipper69/operations/"]
    MAN["CASEFILE-MANIFEST.json"]
    IDX["index.json"]
    OPS --> MAN
    OPS --> IDX
  end
  subgraph pc [Desktop]
    SYNC["flipper69-sync.ps1"]
    VAULT["~/.flipper69/ops/"]
    SYNC --> VAULT
  end
  NFC --> OPS
  RF --> OPS
  HUB -->|USB / SD| SYNC
```

---

## Operation pipeline

Every field session follows the same spine:

```
INTAKE â†’ OP_PREP â†’ PROBE â†’ CAPTURE â†’ VERIFY â†’ EXFIL â†’ CLOSE
```

| Phase | What happens |
|-------|----------------|
| **INTAKE** | Name the op (auto codename), pick type + PATHNUM |
| **OP_PREP** | Generate `opId`, write `OPERATION.json` + `notes.txt`, OPSEC on |
| **PROBE** | Launch DEWDROP, DAMP_CROWD, or stock domain apps |
| **CAPTURE** | Raw + parsed files land in `captures/` |
| **VERIFY** | SHA-256 everything â†’ `CASEFILE-MANIFEST.json` |
| **EXFIL** | USB serial JSON-lines **or** SD pull |
| **CLOSE** | Seal op, update `index.json`, append timeline |

Replay and inject phases expect explicit authorization. Panic wipe clears op metadata â€” not base firmware. **Two OK presses** to arm then wipe.

### Gestures

| Input | Where | Action |
|-------|-------|--------|
| Right / long Left | Main menu | Live status toast |
| OK on EXFIL | Exfil screen | Seal CLOSE |
| OK Ã—2 | Panic | ARM â†’ wipe |

---

## Quick start

### Path A â€” FAPs only (fastest)

Works on stock, Unleashed, or Momentum firmware.

```powershell
py -m pip install --upgrade ufbt
.\scripts\build-fap.ps1 -App all
```

Copy from `dist/` to SD:

| File | SD path |
|------|---------|
| `flipper69_casefile_ops.fap` | `apps/` |
| `flipper69_probe_nfc.fap` | `apps/NFC/` |
| `flipper69_probe_subghz.fap` | `apps/` |
| `flipper69_manifest_viewer.fap` | `apps/` |

Open **CASEFILE Ops** on the device. You're in.

### Path B â€” Full Momentum fork

```powershell
.\scripts\init-firmware-fork.ps1
.\scripts\sync-faps-to-firmware.ps1
.\scripts\apply-flipper69-patches.ps1
.\scripts\build-firmware.ps1 -Target all
```

Flash `dist/firmware/flipper-z-f7-update-mntm-dev-*.tgz` via qFlipper, then deploy FAPs.

### Path C â€” Desktop sync

```powershell
# USB serial (device: [5] EXFIL TO DESKTOP)
.\sync\flipper69-sync.ps1 -ComPort auto

# Or bulk-import from SD after a field day
.\sync\flipper69-sync.ps1 -SdImport E:\
```

Files land under `%USERPROFILE%\.flipper69\ops\`.

### Health check

```powershell
$env:FLIPPER_PORT = "auto"
python .\scripts\flipper-healthcheck.py
```

---

## DEWDROP â€” NFC in plain English

1. **Read** â€” hold tag to Flipper â†’ standard `.nfc` saved to your op folder  
2. **Write** â€” load saved file â†’ confirm ownership â†’ write to blank NTAG / Ultralight / Classic  
3. **Emulate** â€” present saved tag to phones, readers, arcade cabinets  

| Tag type | Read | Write blank | Emulate |
|----------|------|-------------|---------|
| NTAG / Ultralight | âœ“ | âœ“ | âœ“ |
| MIFARE Classic 1K/4K | âœ“* | âœ“* | âœ“ |
| ISO14443-A UID-only | âœ“ | magic card | âœ“ |
| ST25TB | âœ“ | âœ“ | âœ“ |

\*Partial read if keys unknown. Bank cards, DESFire, and secure-element fobs are **not** full-clone targets â€” by design. iPhones and Android phones are **readers**, not blank writable tags â€” use **Emulate** instead.

---

## Desktop bridge

```powershell
.\sync\flipper69-sync.ps1              # auto COM
.\sync\flipper69-sync.ps1 -Once        # one op then exit
.\sync\flipper69-sync.ps1 -SdImport X:\  # verify + vault
.\sync\new-field-op.ps1 -OpType survey -Label lab -Pathnum imps
```

Protocol types: `op_header`, `manifest`, `artifact`, `op_close`, `ping`/`pong`.

---

## Identity & boot

**Viper dolphin** â€” stock Flipper silhouette evolved. Tail splits into three viper coils. One eye: horizontal red slit. Not cute. *Aware.*

```
FRAME 0-3   noise burst
FRAME 5,9   scanline tear
FRAME 6-12  FL1PP3R + 69
FRAME 13+   blood rule Â· classification Â· VER=2.0.0
FRAME 20+   tagline blink Â· viper eye
```

Spec: [`assets/boot_anim.txt`](assets/boot_anim.txt) Â· Mascot: [`assets/mascot_spec.md`](assets/mascot_spec.md) Â· Theme: [`firmware/flipper69/theme/flipper69.json`](firmware/flipper69/theme/flipper69.json)

---

## Project map

```
Fl1pp3r69/
â”œâ”€â”€ fap/                    # Canonical FAP sources (4 apps @ v2)
â”œâ”€â”€ dist/                   # Built .fap + BUILD_MANIFEST.json
â”œâ”€â”€ firmware/
â”‚   â””â”€â”€ flipper69/          # Overlay patches, theme, MANIFEST.json
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ build-fap.ps1
â”‚   â”œâ”€â”€ build-firmware.ps1
â”‚   â”œâ”€â”€ init-firmware-fork.ps1
â”‚   â”œâ”€â”€ sync-faps-to-firmware.ps1
â”‚   â””â”€â”€ flipper-healthcheck.py
â”œâ”€â”€ sync/                   # Desktop exfil + new-field-op + SD import
â”œâ”€â”€ schemas/                # OPERATION + manifest JSON schemas
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ DESIGN.md
â”‚   â”œâ”€â”€ OPS-DISCIPLINE.md
â”‚   â””â”€â”€ superpowers/specs/
â””â”€â”€ assets/                 # Hero, boot anim, mascot, infographic
```

---

## What we inherit vs what we ship

| From Momentum / Unleashed | Fl1pp3r69 unique |
|---------------------------|------------------|
| Extended Sub-GHz protocols | CASEFILE staged ops + phase HUD |
| NFC parsers & rolling-code flags | SHA-256 manifest chain + index |
| Themes, clock, pin lock, BadKB shell | USB + SD desktop bridge |
| Polished desktop UX | DEWDROP read/write/emulate |
| | Obsidian/red identity + OPSEC defaults |
| | Viper dolphin + glitch boot |

**Explicitly excluded:** jamming packs, TX region bypass, ungated bruteforce, exploit binaries.

---

## Roadmap

| Version | Status |
|---------|--------|
| v0.1â€“v0.3 Scaffold + DEWDROP | âœ“ |
| v1.0-alpha Momentum fork + fbt | âœ“ |
| **v2.0.0 Product polish** | âœ“ **you are here** |
| P2 Boot â†’ CASEFILE Ops autostart | â—» |
| P3 Full theme pack assets on device | â—» |
| P4 Serial exfil service in firmware | â—» |
| v2.1 Rolling-code flags in DAMP_CROWD | â—» |

---

## Security

See [SECURITY.md](SECURITY.md) for scope, safe use, and reporting.

---

## Ethics

1. **Field captures and metadata only** â€” no exploit code in repo or on SD  
2. **AUTHORIZED** gate for replay / inject  
3. **Regional TX** respected â€” no region-bypass patches  
4. **Panic wipe** clears op metadata, not firmware  
5. **Authorized research on owned hardware** â€” not legal advice  

---

## Docs

- [`docs/DESIGN.md`](docs/DESIGN.md) â€” architecture  
- [`docs/OPS-DISCIPLINE.md`](docs/OPS-DISCIPLINE.md) â€” phase reference  
- [`CHANGELOG.md`](CHANGELOG.md) â€” full history  
- [`release-notes-v2.0.0.md`](release-notes-v2.0.0.md) â€” this release  
- [`firmware/flipper69/README.md`](firmware/flipper69/README.md) â€” Momentum overlay  

---

## Support the work

Fl1pp3r69 is **free and open source**. Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/Pitchfork-and-Torch/Fl1pp3r69/issues).

---

<p align="center">
  <img src="assets/fl1pp3r69-launch-infographic.svg" alt="Fl1pp3r69 feature overview" width="720">
</p>

<p align="center">
  <sub>MIT License Â· Field research on owned hardware Â· Do not publish exploit derivatives</sub><br><br>
  <strong>The dolphin grew teeth. The manifest keeps the bite legal.</strong>
</p>
