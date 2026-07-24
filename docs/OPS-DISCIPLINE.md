# Operational Discipline (v4.0 — ARGUS VEIL)

Fl1pp3r69 applies **manifest-first field ops** to physical-layer security research on Flipper Zero. Exploit code and offensive payloads are out of scope.

## Design patterns

| Pattern | Implementation |
|---------|----------------|
| PATHNUM | imps / ds / slow / fast / emerg |
| Codename | Random tool_animal per op |
| Manifests | CASEFILE-MANIFEST.json schemaVersion **4**, chainPrev, sealAlg |
| Timeline | TIMELINE.jsonl append-only |
| ACTIVE_OP | `/ext/flipper69/ACTIVE_OP.json` |
| CHECKPOINT | Per-op recovery |
| CLAIM | Stock-app files → op artifacts + meta |
| Version | F69_VER=**4.0.0** / **ARGUS VEIL** |
| Phases | INTAKE → OP_PREP → PROBE → CAPTURE → VERIFY → EXFIL → CLOSE |

## Guardrails

- No exploit binaries, jamming, region bypass, ungated bruteforce
- Replay/inject/write/script start unauthorized until gated
- Panic wipe two-step; metadata only
- TX regional compliance
- Hash mismatch fails closed
- Dashboard binds **127.0.0.1 only**

## On-device flow (v4)

1. Splash ARGUS VEIL  
2. Resume ACTIVE_OP if open  
3. NEW OPERATION → type → PATHNUM  
4. Capture via probes **or** stock apps → **CLAIM**  
5. VERIFY (up to 64 inline items)  
6. EXFIL deliberate (USB / SD)  
7. CLOSE  

### Menu

| Key | Action |
|-----|--------|
| [1] | NEW OPERATION |
| [2] | RESUME |
| [3] | **CLAIM ARTIFACT** |
| [4] | VERIFY |
| [5] | EXFIL |
| [6] | RUN PHASE auto |
| [7] | AUDIT |
| [8] | OPSEC |
| [9] | PANIC |

## Probe suite

| FAP | Codename |
|-----|----------|
| casefile_ops | CASEFILE |
| probe_nfc | DEWDROP |
| probe_subghz | DAMP_CROWD |
| probe_ir | EMBER_TRACE |
| probe_rfid | LODGE |
| probe_ibutton | BITKEY |
| probe_ble | HAZE |
| probe_gpio | GPIO LAB |
| probe_badusb | INKWELL |
| manifest_viewer | crypttool+ |

## Desktop

```bash
pip install -e ./desktop
python -m flipper69 sync --sd E:\
python -m flipper69 sync --serial auto   # needs pyserial
python -m flipper69 seal op-... --merkle
python -m flipper69 audit
python -m flipper69 report op-...
python -m flipper69 dashboard
python -m flipper69 migrate
```

*Discipline is the weapon. Argus keeps the eyes honest.*
