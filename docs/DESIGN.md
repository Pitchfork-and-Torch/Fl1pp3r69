# FLIPPER69 — Design Specification

**Codename:** FL1PP3R69 // **ARGUS VEIL**  
**Classification:** UNCLASSIFIED // FIELD RESEARCH ONLY  
**Version:** 4.0.0  
**Date:** 2026-07-11  
**Supersedes:** Design 3.0.0 VEIL LEDGER  
**Full v4 vision:** [`VISION-v4.md`](VISION-v4.md) · **Audit:** [`AUDIT-v3.md`](AUDIT-v3.md)

---

## Mission Statement

Flipper69 is a custom Flipper Zero firmware distribution and FAP suite for **physical-layer security research**. It is a **field instrument** with manifest integrity, staged operations, and chain-of-custody — synced to a first-class desktop toolkit that audits, visualizes, and reports without ever requiring the network.

> *"The dolphin grew teeth. The veil still holds. Argus opens every eye."*

---

## Design Principles (v3 refined)

| Principle | Implementation |
|-----------|----------------|
| **Manifest everything** | SHA-256 on every capture before it leaves the device; desktop re-verifies |
| **Staged ops only** | No raw tool sprawl — everything runs inside a CASEFILE operation |
| **Exploits excluded** | Field captures and metadata only; zero exploit code on device or in plugins |
| **Exfil is deliberate** | VERIFY → EXFIL → CLOSE; nothing auto-uploads |
| **OPSEC by default** | BT advertising off during ops; TX audit; two-step panic wipe (metadata only) |
| **Badass without felony** | Aggressive UX, restrained legal surface |
| **Ledger continuity** | schemaVersion, chainPrev, checkpoints, multi-session timeline |
| **Desktop is first-class** | Offline Python toolkit: sync, audit, report, migrate, templates |
| **Safe extensibility** | Probe plugin *contract* for metadata sidecars — never dynamic exploit loaders |
| **Fail closed** | Hash mismatch → quarantine flag, never silent trust |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              FLIPPER69 FIRMWARE LAYER (optional overlay)      │
│  Boot: glitch splash │ theme: obsidian/red │ OPSEC defaults    │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                     FAP SUITE v3                              │
│  casefile_ops (hub) · ACTIVE_OP · CHECKPOINT · phase HUD     │
│  DEWDROP (NFC) · DAMP_CROWD (Sub-GHz) · EMBER_TRACE (IR)     │
│  crypttool (manifest viewer)                                  │
└────────────────────────────┬─────────────────────────────────┘
                             │ SD + USB serial (deliberate)
┌────────────────────────────▼─────────────────────────────────┐
│              DESKTOP: flipper69 Python package                 │
│  sync · audit · report · migrate · templates · search · TUI  │
│  vault: ~/.flipper69/ops/  (or FLIPPER69_OPS_ROOT)            │
└──────────────────────────────────────────────────────────────┘
```

### Deployment Strategy (v3)

1. **FAP suite (primary)** — CASEFILE + probes; runs on stock / Unleashed / Momentum.
2. **Momentum overlay** — `firmware/flipper69/` patches, theme, OPSEC (optional).
3. **Desktop toolkit** — Python `flipper69` package (+ legacy PowerShell bridge retained).
4. **Templates on SD/desktop** — `examples/templates/` and optional `/ext/flipper69/templates/`.

---

## Operation Model

### Op Types (field-native)

| Type | Code | Use |
|------|------|-----|
| `proximity` | PX | Single-target RF/NFC/IR capture at range |
| `survey` | SV | Passive scan sweep |
| `replay` | RP | Authorized replay test against owned hardware |
| `inject` | IN | BadUSB / GPIO script run (lab targets only) |
| `unified` | UN | Multi-phase: survey → capture → verify → exfil |

### Phases (unchanged spine)

```
INTAKE → OP_PREP → PROBE → CAPTURE → VERIFY → EXFIL → CLOSE
```

| Phase | Device behavior |
|-------|-----------------|
| **INTAKE** | Name op, select type / PATHNUM / optional template |
| **OP_PREP** | Generate `opId`, write `OPERATION.json`, ACTIVE_OP, CHECKPOINT; OPSEC on |
| **PROBE** | Launch domain plugin (NFC / Sub-GHz / IR / stock apps) |
| **CAPTURE** | Raw + `.meta.json` into `captures/` |
| **VERIFY** | SHA-256 all items → `CASEFILE-MANIFEST.json` (schemaVersion 3, chainPrev) |
| **EXFIL** | USB serial push or SD export marker |
| **CLOSE** | Seal op, clear ACTIVE_OP if matching, update `index.json`, timeline |

### PATHNUM profiles

| Code | Intent |
|------|--------|
| `imps` | Careful / high OPSEC |
| `ds` | Default standard |
| `slow` | Deliberate multi-step |
| `fast` | Time-boxed field window |
| `emerg` | Minimal ceremony, still staged |

### Storage Layout (SD card)

```
/ext/flipper69/
  index.json
  ACTIVE_OP.json          # v3: pointer to current opId
  templates/              # optional device-side templates
  operations/
    op-20260711-veil-ledger-demo/
      OPERATION.json      # schemaVersion 3
      CHECKPOINT.json     # phase + updatedAt for recovery
      TIMELINE.jsonl
      CASEFILE-MANIFEST.json
      notes.txt
      captures/
        *.nfc / *.sub / *.ir / *.meta.json
```

### ACTIVE_OP.json

```json
{
  "schemaVersion": 3,
  "opId": "op-20260711-veil-ledger-demo",
  "opPath": "/ext/flipper69/operations/op-20260711-veil-ledger-demo",
  "phase": "probe",
  "updatedAt": "2026-07-11T12:00:00Z"
}
```

### CHECKPOINT.json

```json
{
  "schemaVersion": 3,
  "opId": "op-20260711-veil-ledger-demo",
  "phase": "capture",
  "session": 1,
  "updatedAt": "2026-07-11T12:05:00Z",
  "reason": "phase_advance"
}
```

**Recovery rule:** On hub start, if ACTIVE_OP exists and OPERATION.phase ≠ close, resume that op and surface CHECKPOINT phase. Corrupt ACTIVE_OP → fall back to newest `op-*` directory.

---

## FAP: casefile_ops (Command Hub)

```
╔══════════════════════════════════════╗
║  FL1PP3R69 // VEIL LEDGER    v3.0.0  ║
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
║  ACTIVE: op-… [PROBE]  CKP✓  OPSEC   ║
║  MANIFEST: a3f8…c21d  ✓               ║
╚══════════════════════════════════════╝
```

### Key bindings

- **OK** — select menu item  
- **Back** — abort phase (`phase_aborted` timeline event)  
- **Right / long Left** — live status toast  
- **OK ×2 on panic** — ARM → CONFIRM DESTRUCT  

### Panic wipe

Two-step only. Removes `/ext/flipper69/operations/` metadata + ACTIVE_OP + index entries. **Never** touches base firmware or unrelated SD content.

---

## Probe Plugins

Each probe resolves the active op via:

1. `ACTIVE_OP.json` if valid  
2. Else newest `op-*` under operations  

Writes into `captures/` with `.meta.json` sidecars suitable for VERIFY.

| FAP | Codename | Role |
|-----|----------|------|
| `flipper69_casefile_ops` | CASEFILE | Hub |
| `flipper69_probe_nfc` | DEWDROP | NFC read / write / emulate |
| `flipper69_probe_subghz` | DAMP_CROWD | Sub-GHz meta sidecar |
| `flipper69_probe_ir` | EMBER_TRACE | IR meta sidecar |
| `flipper69_manifest_viewer` | crypttool | Multi-op hash viewer |

### Ownership / authorization gates

- NFC **write** and **emulate** require on-screen ownership confirmation (v2 preserved).  
- Op types `replay` / `inject` start with `authorized: false` until gated.  
- No probe may ship jamming, bruteforce, or region-unlock logic.

### Plugin contract (community)

See `schemas/probe.plugin.schema.json` and `docs/guides/CONTRIBUTING-PROBES.md`.

On-device plugins remain **separate FAPs** (not dynamic loaders). Desktop may validate plugin metadata packages.

---

## Manifest Model (schemaVersion 3)

### CASEFILE-MANIFEST.json (v3)

```json
{
  "schemaVersion": 3,
  "generatedAt": "2026-07-11T14:22:01Z",
  "opId": "op-20260711-veil-ledger-demo",
  "firmware": "flipper69",
  "firmwareVersion": "3.0.0",
  "releaseCodename": "VEIL LEDGER",
  "classification": "UNCLASSIFIED//FRI",
  "verifyCount": 1,
  "chainPrev": null,
  "items": [
    {
      "type": "capture",
      "path": "captures/ember_120501.meta.json",
      "hash": "…64 hex…",
      "probe": "ir",
      "sizeBytes": 128
    }
  ]
}
```

| Field | Rule |
|-------|------|
| `chainPrev` | SHA-256 of previous CASEFILE-MANIFEST body if re-VERIFY; else null |
| `verifyCount` | Increments each VERIFY seal |
| v2 manifests | Lack `schemaVersion` → treated as version 2; still hash-verifiable |

### OPERATION.json (v3 additions)

- `schemaVersion: 3`  
- `session: 1` (multi-day continuity)  
- `templateId` optional  
- `device.serial` when available  
- `releaseCodename: "VEIL LEDGER"`  

---

## Serial Sync Protocol

USB CDC 115200. JSON-lines. Unchanged message types; desktop accepts v2 and v3 payloads.

| Type | Direction | Purpose |
|------|-----------|---------|
| `op_header` | device→desktop | Start op stream |
| `manifest` | device→desktop | Full manifest |
| `artifact` | device→desktop | Path + sha256 + b64 |
| `op_close` | device→desktop | Seal |
| `ping` / `pong` | both | Liveness |
| `ack` | desktop→device | Stored |

Legacy: `sync/flipper69-sync.ps1`  
Primary: `python -m flipper69 sync …`

---

## Desktop Toolkit

Package: `desktop/flipper69` (install editable: `pip install -e desktop/`)

| Command | Purpose |
|---------|---------|
| `flipper69 sync --sd PATH` | Import + verify |
| `flipper69 audit [opId]` | Hash + orphan + chain audit |
| `flipper69 report opId` | HTML (and PDF if available) CoC report |
| `flipper69 list` | Vault search/filter |
| `flipper69 timeline opId` | Timeline view |
| `flipper69 migrate` | v2 → v3 vault upgrade |
| `flipper69 template list\|apply` | Operation templates |
| `flipper69 pack opId` | Safe share / full pack |
| `flipper69 tui` | Optional rich TUI |

Vault default: `%USERPROFILE%\.flipper69\ops` / `~/.flipper69/ops`  
Override: `FLIPPER69_OPS_ROOT`

### Report structure

1. Cover: opId, codename, classification, device  
2. Scope & authorization statement  
3. Phase timeline summary  
4. Artifact inventory with SHA-256  
5. Chain-of-custody (VERIFY / EXFIL / desktop receipts)  
6. Integrity result (PASS/FAIL)  
7. Ethics footer  

---

## Edge Case Matrix

| Scenario | Behavior |
|----------|----------|
| SD corruption mid-capture | Incomplete files excluded until re-VERIFY; orphan scan lists them |
| Power loss mid-phase | CHECKPOINT + ACTIVE_OP restore; VERIFY re-required before EXFIL |
| Interrupted exfil | Desktop incomplete package flag; re-run sync |
| Multi-day op | Increment `session`; append TIMELINE; re-VERIFY before each EXFIL |
| Air-gapped desktop | Fully offline Python toolkit |
| International travel | `pack --redact` strips notes/target labels, keeps hashes |
| Manifest verify fail | Fail closed; timeline `hash_mismatch`; no PASS report |
| User abort | `phase_aborted` event; phase not advanced |
| Large capture sets | Device MAX_MANIFEST_ITEMS; desktop handles large sets |
| Concurrent devices | Separate vault dirs or deviceId filter; conflict report if same opId differs |
| Data retention request | Export pack + retention advisory; no silent delete |

---

## Security / Threat Model (summary)

| Threat | Control |
|--------|---------|
| Tampered capture after seal | SHA-256 mismatch on desktop audit |
| Accidental wipe of firmware | Panic only deletes op metadata |
| Unauthorized replay/inject | authorized:false + UI gates |
| Tool used for crime | Out of scope of software; ethics + legal disclaimers; no exploit aids |
| Plugin supply chain | No on-device dynamic load; human review checklist |
| Exfil eavesdrop USB | Deliberate operator action; air-gap SD path preferred for sensitive work |

Full policy: `SECURITY.md`.

---

## Migration (v2 → v3)

1. Install desktop package.  
2. `flipper69 migrate --vault ~/.flipper69/ops`  
3. Updates OPERATION/MANIFEST with schemaVersion; leaves hashes intact.  
4. Device: flash/copy v3 FAPs; existing ops resume via ACTIVE_OP creation on first open.  

Details: `docs/MIGRATION-v3.md`.

---

## Performance Budgets

| Surface | Budget |
|---------|--------|
| casefile_ops FAP | Prefer ≤ stack 4KB; avoid large static tables |
| Manifest items on-device | ≤ 24 files (v2 limit preserved) |
| Desktop audit 500 files | < 30s on modest laptop |
| Report HTML | < 2s for typical op |

---

## Testing Strategy

| Layer | Method |
|-------|--------|
| Schemas | CI JSON Schema validation of examples |
| Desktop | `pytest desktop/tests` |
| Device | Manual field checklist (docs/guides/HARDWARE-VALIDATION.md) |
| Migration | Round-trip on examples/sd_card + demo vault |

---

## Visual Identity

| Token | Hex | Use |
|-------|-----|-----|
| Obsidian | `#0a0a0c` | Backgrounds |
| Blood red | `#c41e1e` | Accents, active phase |
| Phosphor | `#39ff14` | Manifest verified |
| Amber | `#ffb000` | Warnings |
| Ghost | `#8b8b8b` | Inactive |
| Ledger slate | `#1a1a22` | Desktop panels |

Mascot: viper-coil dolphin — `assets/mascot_spec.md`.

---

## Ethics & Legal Guardrails (hard-coded)

1. **No exploit binaries** on SD, firmware, or plugins.  
2. **No jamming, region bypass, or ungated bruteforce.**  
3. **Replay/inject** require explicit authorization confirmation.  
4. **TX regions** respected.  
5. **Panic wipe** = metadata only.  
6. **Authorized research on owned/authorized hardware only** — not legal advice.  
7. **User responsibility** restated in reports and templates.

---

## Success Criteria

v3.0 is done when the success list in `docs/VISION-v3.md` §8 is met.

---

*The dolphin grew teeth. The veil hides the op. The ledger never lies.*
