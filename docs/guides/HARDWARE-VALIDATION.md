# Hardware Validation Checklist (v3.0)

Use a real Flipper Zero + SD + Momentum/Unleashed/stock with ufbt-built FAPs.

## Configurations

| Config | Firmware | Notes |
|--------|----------|-------|
| A | Momentum dev | Preferred |
| B | Unleashed | FAP-only path |
| C | Stock OFW | FAP-only; limited radio features |

## Scenarios

1. **Happy path unified op**  
   NEW → OP_PREP → DEWDROP read owned tag → VERIFY → SD pull → `flipper69 sync --sd` → audit PASS → report HTML.

2. **Power-loss recovery**  
   Create op, advance to PROBE, hard power off. Reboot, open CASEFILE — ACTIVE_OP resumes, CHECKPOINT present.

3. **Re-VERIFY chain**  
   VERIFY twice; second manifest has non-null `chainPrev` matching prior file hash.

4. **IR sidecar**  
   EMBER_TRACE seals meta; stock IR app captures raw; VERIFY includes both if present.

5. **Panic wipe**  
   ARM → CONFIRM removes operations + ACTIVE_OP; firmware intact.

6. **Interrupted SD copy**  
   Partial folder → audit FAIL/missing → re-copy → PASS.

7. **Multi-day**  
   Resume same op next day; session/timeline continuity; re-VERIFY before EXFIL.

8. **Template desktop**  
   `template apply client-pentest-physical --acknowledge-auth` then copy scaffold notes to device op.

## Pass criteria

- No crash loops on hub  
- Hashes match on desktop  
- No write outside flipper69 tree  
- Ethics gates still present on NFC write  
