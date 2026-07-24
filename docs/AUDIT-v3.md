# Fl1pp3r69 v3.0 Audit Report — Pre-v4 Baseline

**Subject:** Fl1pp3r69 @ `Pitchfork-and-Torch/Fl1pp3r69` (v3.0.0 **VEIL LEDGER**)  
**Audit date:** 2026-07-11  
**Method:** Full tree review of docs, schemas, FAP C sources, desktop Python package, firmware overlay, scripts, examples, CI, and landing. Cross-check against Flipper Zero / Momentum capability surface.

---

## 1. Executive judgment

Fl1pp3r69 v3 is a **coherent, ethics-bound CASEFILE instrument** with a real identity, real integrity model, and a real desktop vault path. It is *not* yet “the ultimate Flipper platform.” It is a **high-quality spine** with **thin domain coverage**, **sidecar-level RF/IR depth**, and a **desktop toolkit that is correct but austere**.

**Verdict:** Excellent foundation for a flagship v4. Do not rewrite the spine. **Expand domains into the spine** and move analysis/reporting muscle to desktop.

---

## 2. Inventory (as shipped)

| Layer | Contents | Maturity |
|-------|----------|----------|
| **Hub FAP** | `casefile_ops` — 8-item menu, phase strip, splash, panic 2-step, resume | High |
| **Probes** | DEWDROP (NFC — real stack), DAMP_CROWD (Sub-GHz *sidecar only*), EMBER_TRACE (IR *sidecar only*) | Uneven |
| **Viewer** | `manifest_viewer` (crypttool) multi-op browser | Medium |
| **Integrity** | On-device SHA-256, CASEFILE-MANIFEST, chainPrev, verifyCount | High |
| **Recovery** | ACTIVE_OP.json, CHECKPOINT.json | Medium–High |
| **Schemas** | operation, manifest, active_op, checkpoint, template, probe.plugin, serial | High |
| **Desktop** | Python CLI: sync, audit, report, migrate, template, pack, list, timeline, stub TUI | Medium |
| **Legacy bridge** | PowerShell serial + SD import | Medium |
| **Firmware overlay** | Patches/theme staged; serial/autostart not productized | Low–Medium |
| **Examples** | SD demo ops, 4 templates, 1 plugin descriptor | Medium |
| **CI** | Schema validate + desktop pytest | Medium |
| **Landing** | Static product page | Medium |

### Hard limits observed in code

| Constant | Value | Implication |
|----------|-------|-------------|
| `MAX_MANIFEST_ITEMS` | **24** | Large field days silently truncate sealing |
| `F69_MAX_OPS` | **24** | Index/list cap on device |
| Viewer ops | **16** | Inconsistent with hub |
| Stack (hub) | 4 KB | Healthy for FAP |
| DAMP_CROWD / EMBER | Meta sidecar only | Stock apps do raw capture outside formal probe UX |
| DEWDROP op resolve | **Latest `op-*` dir**, not ACTIVE_OP | Integration gap vs IR probe |
| Serial exfil | Protocol designed; hub EXFIL is readiness marker more than full streamer | Incomplete productization |
| Dist FAPs | Built artifacts may lag source (IR may need rebuild) | Release hygiene gap |

---

## 3. Strengths (protect these)

### 3.1 Philosophy that actually ships

- **Manifest everything** is implemented, not aspirational.
- **Staged phases** are enforced by hub UX, not just docs.
- **Fail-closed** desktop audit is correct (hash mismatch → FAIL).
- **Deliberate exfil** remains manual (USB/SD); no cloud autopilot.
- **Panic wipe** is two-step and metadata-scoped.
- **Ethics surface** is consistent: SECURITY, templates require `--acknowledge-auth`, NFC write gates, no jamming/region bypass in repo.

### 3.2 Operational discipline

- Codename + PATHNUM + op types form a repeatable field ritual.
- Timeline appends create a usable CoC backbone.
- Templates encode professional checklists (survey, badge lab, client physical, academic).

### 3.3 Integrity model (v3 leap)

- `schemaVersion`, `chainPrev`, `verifyCount` enable re-VERIFY continuity.
- Desktop import verifies **before** writing receipts (`DESKTOP-RECEIPTS.jsonl`) — correct design (avoids poisoning TIMELINE hashes).
- Plugin contract (`probe.plugin.json`) bans exploits at schema level (`noExploits: const true`).

### 3.4 Recovery

- ACTIVE_OP + CHECKPOINT + hub auto-resume address real power-loss field risk.

### 3.5 Documentation & identity

- DESIGN / OPS-DISCIPLINE / VISION / MIGRATION / SECURITY / CONTRIBUTING-PROBES form a professional corpus.
- Visual language (obsidian/red, viper dolphin, classification banners) is distinctive and consistent enough to own a brand.

### 3.6 Contributor path

- ufbt FAP-primary deploy works without full firmware fork.
- CI covers schemas + desktop tests (portable).
- Ethical probe contribution guide exists.

---

## 4. Weaknesses (be ruthless)

### 4.1 Protocol coverage is shallow relative to hardware

The Flipper + Momentum surface in 2026 includes deep Sub-GHz protocol packs, NFC suite, 125 kHz RFID, iButton, IR universal remotes, BadUSB/BadKB, GPIO, BLE tools, RFID raw, and expansion-board workflows. Fl1pp3r69 currently **organizes** three domains and **fully implements** roughly one (NFC).

| Domain | Hardware/Momentum capability | Fl1pp3r69 v3 | Gap severity |
|--------|------------------------------|--------------|--------------|
| NFC HF | Read/write/emulate multi-protocol | DEWDROP solid | Medium (no 125 kHz, limited custody UX) |
| Sub-GHz | Capture, decode, rolling flags, TX (regional) | Sidecar band labels only | **Critical** |
| IR | Capture/TX/universal | Sidecar protocol labels only | **High** |
| RFID 125 kHz | LF read/write/emulate | **Absent** | **High** |
| iButton | Read/write/emulate | **Absent** | High |
| BadUSB | DuckyScript / BadKB | Design mention only | High (ethics-gated) |
| GPIO / logic | Pin I/O, expansion | **Absent** | High for lab ops |
| BLE | Scan/advertise tools | **Absent** | Medium–High |
| U2F / misc | Limited device support | Out of scope (ok) | Low |
| WiFi devboard | External | Not integrated | Medium (optional) |

### 4.2 Probe integration is inconsistent

- EMBER_TRACE reads **ACTIVE_OP**.
- DEWDROP and DAMP_CROWD still use **newest directory** heuristics.
- No shared `libf69` for path resolve, meta write, timeline events.
- Probes do not write structured CAPTURE phase events reliably into hub state.
- Stock Sub-GHz / IR apps write outside op folders unless operator is disciplined → **orphan problem by design**.

### 4.3 Manifest ceiling & artifact taxonomy

- 24-item cap is a silent field-day failure mode.
- Item `type` / `probe` enums lag future domains (rfid, ibutton, gpio, ble, screenshot, note-attachment).
- No artifact **kind taxonomy** (raw vs meta vs derived vs note vs evidence-link).
- No Merkle tree / per-directory digests for large ops (desktop could do this; device cannot).
- OPERATION `manifestHash` chicken-egg with re-save after VERIFY remains a subtle integrity footgun.

### 4.4 Phase engine is linear and shallow

- Fixed 7 phases only; no domain-aware checklists on-device.
- `RUN PHASE (auto)` can advance without real captures.
- No conditional gates beyond op type authorized flags.
- Multi-session is a counter field, not a real session object on device.
- Template application is **desktop-only** — device INTAKE does not load templates.

### 4.5 Desktop is correct but not flagship

| Capability | Status |
|------------|--------|
| SD import + hash verify | Good |
| Audit orphans/mismatch | Good basic |
| HTML CoC report | Good skeleton |
| PDF | Optional/thin |
| TUI | Print-list stub, not Textual |
| Serial USB listener | **Missing in Python** (PS1 only) |
| Timeline graphs | No |
| Local web dashboard | No |
| Vault encryption | No |
| Multi-vault / operator profiles | No |
| Export (Wireshark, STIX, SIEM JSON) | No |
| Sub-GHz/NFC visualization | No |
| Redaction pack | Basic |
| chainPrev cryptographic validation chain walk | Partial (fields present; deep walk weak) |

### 4.6 Firmware overlay is aspirational

- OPSEC patches, serial service, autostart remain **staged**.
- Theme not fully baked into device experience for FAP-only users.
- No version alignment check between FAP suite and overlay MANIFEST.

### 4.7 UX / discoverability

- 128×64 OLED menu is usable but sparse (no search, no favorites, no probe launcher matrix).
- crypttool cannot show chainPrev or verify on-device recompute well.
- No “attach orphan from /ext/subghz” workflow.
- No on-device HUD for capture counts / free SD / last hash short form beyond footer.

### 4.8 Scale, resilience, performance

- No streaming VERIFY for >24 files.
- No SD free-space gate before CAPTURE.
- No corruption detection beyond hash fail.
- No concurrent-device conflict beyond desktop notes.
- Large TIMELINE.jsonl never rotated/compacted.
- No fsync discipline documented for power-loss mid-write of JSON.

### 4.9 Maintenance & contributor burden

- Duplicated op-discovery logic across FAPs.
- No shared static library / common source folder.
- No probe scaffold generator implemented (docs only).
- FAP CI not in GHA (SDK-heavy — understandable but gaps remain).
- Docs still mention some v1 roadmap fossils in older superpowers specs.
- Landing / product site coupling to personal domain is product-ops risk (hygiene-sensitive).

### 4.10 Security / compliance gaps (relative to enterprise use)

- No operator identity or signing of manifests.
- No key-based vault seal.
- Authorization is boolean + UI, not structured ROE object.
- Share-safe pack redaction is coarse (path heuristics).
- No retention policy engine (advisory docs only).
- No tamper-evident “sealed close” detached signature.

---

## 5. Technical debt register

| ID | Debt | Severity | Notes |
|----|------|----------|-------|
| TD-01 | Per-FAP op path discovery duplication | High | Fix with shared module |
| TD-02 | DEWDROP ignores ACTIVE_OP | High | One-line class bug vs design |
| TD-03 | MAX_MANIFEST_ITEMS=24 | High | Chunked manifests or desktop-only mega-seal |
| TD-04 | Sidecar probes ≠ raw capture ownership | High | Need “import stock path → op” |
| TD-05 | JSON via snprintf / strstr parsers | Medium | Brittle; fine for embedded until size grows |
| TD-06 | Serial protocol half-implemented | Medium | Desktop Python listener absent |
| TD-07 | Firmware patches not product path | Medium | Keep optional; document FAP-only as primary |
| TD-08 | TUI is not a TUI | Low–Med | Rename or replace |
| TD-09 | verifyCount hardcoded 1/2 in C | Low | Should read prior count+1 |
| TD-10 | Inconsistent F69_MAX_OPS (24 vs 16) | Low | Unify |
| TD-11 | OPERATION hash after VERIFY | Medium | Document or dual-hash strategy |
| TD-12 | No unit tests for C | Medium | Desktop-only tests today |

---

## 6. Ecosystem cross-reference (what “everything the device can do” means)

Legitimate, authorizeable Flipper/Momentum surfaces Fl1pp3r69 should **organize** (not re-implement naively):

1. **Sub-GHz** — raw capture, protocol decode, frequency/preset metadata, rolling-code *flags*, regional TX gates, weather/TPMS/pager families as labeled captures.  
2. **NFC** — multi-protocol read, owned-tag write, emulate, dump formats.  
3. **LF RFID** — 125 kHz families.  
4. **IR** — learn/save/TX, universal remote libraries as referenced artifacts.  
5. **iButton** — keys as custody items.  
6. **BadUSB/BadKB** — hash-listed scripts, inject op type, dual confirm.  
7. **GPIO** — scripts, pin logs, logic captures as files.  
8. **BLE** — passive survey metadata; active only with explicit auth.  
9. **Storage tools** — attach external files into op with hash.  
10. **Expansion** — WiFi/camera board outputs imported as linked artifacts (desktop-heavy).

**Explicit non-goals remain:** jamming, region unlock, ungated bruteforce, credential theft pipelines, general network exploit frameworks.

---

## 7. Missed opportunities (high value)

1. **Stock-app harness** — post-capture “claim into CASEFILE” instead of reimplementing every radio stack.  
2. **Shared libf69** — one path for ACTIVE_OP, meta, timeline, auth gate.  
3. **Domain packs as plugins** — RFID, iButton, GPIO, BLE, BadUSB as FAPs under one contract.  
4. **Desktop as forensic workbench** — timeline viz, protocol viewers, multi-op campaigns, local web UI (localhost only).  
5. **Mission templates** that orchestrate multi-probe checklists on-device (read-only checklist) + desktop apply.  
6. **Chunked / Merkle manifests** for large ops (device writes leaf list; desktop builds tree).  
7. **Operator profile + optional signing** for multi-person red teams without online server.  
8. **Attach + rehash** workflow for orphans.  
9. **Python serial exfil** parity with PS1.  
10. **Probe scaffold CLI** (`flipper69 scaffold probe`).

---

## 8. Risk areas for v4 ambition

| Risk | Why it matters | Mitigation direction |
|------|----------------|----------------------|
| Feature creep | Becomes another CFW plugin soup | Domain taxonomy + phase gates + plugin ban list |
| FAP size/RAM | Too many full stacks | Sidecar + stock harness first; deep stacks only where unique (DEWDROP model) |
| Ethics dilution | “Just one more TX tool” | Schema + review + dual confirm + op-type gates |
| Schema break | Vault orphans | schemaVersion 4 + migrate tool + dual-read |
| Maintenance | 10 probes × drift | Shared lib, scaffold, CI schema tests |
| Desktop bloat | Hard to air-gap | Stdlib-first core; optional extras |

---

## 9. Scorecard (1–5)

| Dimension | Score | Comment |
|-----------|-------|---------|
| Integrity / CoC | **4.5** | Strong; scale limits remain |
| Ethics / OPSEC | **5** | Best-in-class posture |
| Protocol depth | **2** | NFC yes; rest thin |
| On-device UX | **3** | Clear, not powerful |
| Desktop power | **3** | Correct CLI; not workbench |
| Recovery | **4** | Good bones |
| Extensibility | **3.5** | Contract exists; few plugins |
| Docs | **4.5** | Excellent for size |
| Build/CI | **3** | Desktop strong; FAP CI weak |
| Coherence | **4.5** | Rare among Flipper projects |

**Overall: 3.7 / 5** — best structured Flipper *ops framework* publicly visible; not yet fullest *capability* platform.

---

## 10. Audit conclusion

v3 **VEIL LEDGER** achieved its mission: deepen the ledger, add recovery, open extensibility, ship desktop CoC.  

v4 must **not** abandon that. It must **fill the capability matrix inside the CASEFILE cage**, fix integration debt (ACTIVE_OP everywhere, shared lib, orphan attach, manifest scaling), and elevate desktop from “verifier” to “forensic workbench” — still air-gapped-first, still deliberate exfil, still zero exploit surface.

→ Design response: **`docs/VISION-v4.md`** (codename **ARGUS VEIL**).
