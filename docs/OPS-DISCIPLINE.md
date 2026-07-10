# Operational Discipline (v2.0)

Fl1pp3r69 applies **manifest-first field ops** to physical-layer security research on Flipper Zero. Exploit code and offensive payloads are out of scope.

## Design patterns

| Pattern | Fl1pp3r69 implementation |
|---------|--------------------------|
| PATHNUM profiles (`imps/ds/slow/fast/emerg`) | New-op ritual: type → speed/OPSEC profile before seal |
| Tool codenames (`charm_penguin`, `dewdrop`, `viper_coil`…) | Random `{tool}_{animal}` per operation |
| Hidden workspace dirs | Per-op `.f69_{hex8}` capture markers |
| Integrity manifests | `CASEFILE-MANIFEST.json` with path, size, SHA-256, opId |
| Timeline logging | `TIMELINE.jsonl` append on every phase + OPSEC events |
| Version stamps | `F69_VER=2.0.0` on timeline + manifest + OPERATION |
| Staged phases | INTAKE → OP_PREP → PROBE → CAPTURE → VERIFY → EXFIL → CLOSE |
| Classification banner | `UNCLASSIFIED//FRI` on boot + manifest |
| Index | `/ext/flipper69/index.json` lists all op ids |

## Guardrails

- No exploit binaries on SD or in firmware
- Replay/inject ops start with `authorized:false` until explicitly gated
- Panic wipe is **two-step** (ARM → CONFIRM); removes op metadata only
- TX respects regional band restrictions
- Write/print NFC requires on-screen ownership confirmation

## On-device flow (v2)

1. Glitch boot splash (`FL1PP3R` + `69` + viper eye)
2. **[1] NEW OPERATION** → op type → PATHNUM
3. OP_PREP: codename, op id, workspace, notes.txt, phase strip
4. Run probes (**DEWDROP** / **DAMP_CROWD**) into `captures/`
5. **[4] VERIFY** → SHA-256 seal + haptic + toast
6. **[5] EXFIL** → USB + `flipper69-sync.ps1` (or SD pull + `-SdImport`)
7. OK on EXFIL → **CLOSE** seals op + updates index

### Quick gestures

| Input | Action |
|-------|--------|
| Right (menu) | Live status toast |
| Long Left (menu) | Live status toast |
| OK ×2 on panic | ARM then wipe |

## Probe apps

| FAP | Codename | Role |
|-----|----------|------|
| `flipper69_casefile_ops` | CASEFILE | Command hub |
| `flipper69_probe_nfc` | DEWDROP | NFC read / write / emulate |
| `flipper69_probe_subghz` | DAMP_CROWD | Sub-GHz meta sidecar |
| `flipper69_manifest_viewer` | crypttool | Multi-op manifest browser |

## Desktop merge

```
%USERPROFILE%\.flipper69\ops\operations\op-YYYYMMDD-*/
```

```powershell
# USB serial
.\sync\flipper69-sync.ps1 -ComPort auto

# SD card bulk import + hash verify
.\sync\flipper69-sync.ps1 -SdImport E:\
```
