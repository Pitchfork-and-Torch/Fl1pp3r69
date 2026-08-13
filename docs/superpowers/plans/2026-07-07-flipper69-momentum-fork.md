# Fl1pp3r69 Momentum Fork Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a flashable Fl1pp3r69 v1.0 firmware image based on Momentum with CASEFILE Ops as boot home.

**Architecture:** Git submodule pins `Next-Flip/Momentum-Firmware`; `fap/` sources junction into `firmware/momentum/applications/external/flipper69/`; overlay patches copy via idempotent PowerShell; fbt builds updater package.

**Tech Stack:** Momentum-Firmware, fbt, PowerShell, ufbt (FAP dev), qFlipper

**Spec:** `docs/superpowers/specs/2026-07-07-flipper69-momentum-fork-design.md`

---

## File Map

| Path | Responsibility |
|------|----------------|
| `firmware/flipper69/MANIFEST.json` | Upstream SHA pin, patch list, FAP registry |
| `firmware/flipper69/patches/*.c` | Boot, OPSEC, serial, desktop hooks |
| `firmware/flipper69/theme/flipper69.json` | Momentum theme manifest |
| `scripts/init-firmware-fork.ps1` | Submodule clone + toolchain check |
| `scripts/sync-faps-to-firmware.ps1` | Junction `fap/` into momentum tree |
| `scripts/apply-flipper69-patches.ps1` | Copy patches per MANIFEST |
| `scripts/build-firmware.ps1` | fbt updater_package wrapper |

---

### Task 1: Submodule Scaffold (P0)

**Files:**
- Create: `.gitmodules`, `firmware/flipper69/MANIFEST.json`
- Modify: `.gitignore`

- [ ] **Step 1:** Add `firmware/momentum` submodule entry pointing to `Next-Flip/Momentum-Firmware` branch `dev`
- [ ] **Step 2:** Add `firmware/momentum/` to `.gitignore` if using optional clone (submodule tracked separately)
- [ ] **Step 3:** Commit scaffold

---

### Task 2: Init Script (P0)

**Files:**
- Create: `scripts/init-firmware-fork.ps1`

- [ ] **Step 1:** Script checks for git, fbt prerequisites (Docker or WSL per Momentum docs)
- [ ] **Step 2:** Runs `git submodule update --init firmware/momentum`
- [ ] **Step 3:** Records momentum HEAD in `firmware/flipper69/MANIFEST.json` `upstream.sha`
- [ ] **Step 4:** Test: `.\scripts\init-firmware-fork.ps1` prints momentum path

---

### Task 3: FAP Junction Sync (P1)

**Files:**
- Create: `scripts/sync-faps-to-firmware.ps1`

- [ ] **Step 1:** Create `firmware/momentum/applications/external/flipper69/` if missing
- [ ] **Step 2:** Junction each `fap/{casefile_ops,probe_nfc,probe_subghz,manifest_viewer}` → external tree
- [ ] **Step 3:** Register apps in momentum `applications/settings/application.fam` (external section)
- [ ] **Step 4:** Run `fbt fap_flipper69_casefile_ops` — expect compile success

---

### Task 4: OPSEC Boot Patch (P2)

**Files:**
- Modify: `firmware/flipper69/patches/opsec_defaults.c`
- Create: `firmware/flipper69/patches/flipper69_service.c`, `application.fam` service entry

- [ ] **Step 1:** Wire `flipper69_apply_opsec_defaults()` to BT settings API (Momentum headers)
- [ ] **Step 2:** Register flipper69 service in `application.fam` with `FlipperAppType.STARTUP`
- [ ] **Step 3:** Flash dev build; verify BT advertising off after boot

---

### Task 5: Desktop Autostart (P2)

**Files:**
- Create: `firmware/flipper69/patches/desktop_autostart.c`

- [ ] **Step 1:** Hook desktop `desktop_loader` to open `flipper69_casefile_ops.fap` once per boot
- [ ] **Step 2:** Add setting `Settings → Desktop → Fl1pp3r69 Home` toggle (default on)
- [ ] **Step 3:** Verify boot lands in CASEFILE Ops menu

---

### Task 6: Theme + Boot Animation (P3)

**Files:**
- Create: `firmware/flipper69/theme/flipper69.json`, `assets/boot_anim/`

- [ ] **Step 1:** Package obsidian/red icon overrides for Momentum theme loader
- [ ] **Step 2:** Compile glitch boot from `assets/boot_anim.txt`
- [ ] **Step 3:** Set as default in flipper69 settings file on SD template

---

### Task 7: Serial Exfil Bridge (P4)

**Files:**
- Create: `firmware/flipper69/patches/flipper69_serial.c`
- Modify: `sync/flipper69-sync.ps1`

- [ ] **Step 1:** CDC handler emits JSON-lines on EXFIL phase trigger from casefile_ops
- [ ] **Step 2:** End-to-end test with device COM port + sync script
- [ ] **Step 3:** Manifest SHA-256 verified on desktop

---

### Task 8: probe_subghz Meta Sidecars (P4)

**Files:**
- Modify: `fap/probe_subghz/probe_subghz.c`

- [ ] **Step 1:** On capture, write `.meta.json` with frequency, RSSI, protocol, rolling_code_detected
- [ ] **Step 2:** Use Unleashed protocol name in filename when available
- [ ] **Step 3:** VERIFY phase includes meta files in manifest hash

---

### Task 9: Build & Release (P5)

**Files:**
- Create: `scripts/build-firmware.ps1`
- Modify: `dist/BUILD_MANIFEST.json`

- [ ] **Step 1:** `fbt updater_package` produces `.tgz` in `dist/firmware/`
- [ ] **Step 2:** Record firmware SHA-256 in BUILD_MANIFEST
- [ ] **Step 3:** Tag `flipper69-v1.0.0`, push private repo
- [ ] **Step 4:** Flash device via qFlipper; run `flipper-healthcheck.py`

---

## Testing Checklist

- [ ] Boot → CASEFILE Ops without manual launch
- [ ] New op → DEWDROP read → VERIFY manifest hash
- [ ] Sub-GHz capture in op folder with `.meta.json`
- [ ] EXFIL to `%USERPROFILE%\.flipper69\ops` passes hash verify
- [ ] Panic wipe clears op metadata only
- [ ] `AUTHORIZED` required for replay/inject phases