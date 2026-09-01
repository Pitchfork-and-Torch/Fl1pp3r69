# flipper69 desktop toolkit (v4.0.0 — ARGUS VEIL)

Offline-first Python companion for Fl1pp3r69 CASEFILE operations.

**Authorized ops only.** Use on hardware and systems you own or have explicit permission to test. This toolkit syncs, seals, audits, and reports — it does not ship exploit PoCs or undocumented attack procedures.

## Install

```bash
cd desktop
pip install -e .
# optional PDF:
pip install -e ".[pdf]"
```

## Commands

```bash
python -m flipper69 sync --sd E:\
python -m flipper69 audit
python -m flipper69 audit op-20260711-veil-ledger-demo
python -m flipper69 list
python -m flipper69 timeline op-20260711-veil-ledger-demo
python -m flipper69 report op-20260711-veil-ledger-demo -o report.html
python -m flipper69 migrate
python -m flipper69 template list
python -m flipper69 template apply survey-building --label lab-east
python -m flipper69 pack op-20260711-veil-ledger-demo --redact
python -m flipper69 tui
```

Vault: `%USERPROFILE%\.flipper69\ops` or `FLIPPER69_OPS_ROOT`.

Works fully air-gapped. No network required.
