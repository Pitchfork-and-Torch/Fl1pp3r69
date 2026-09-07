# Contributing to Fl1pp3r69

Thanks for helping keep the dolphin sharp and the ledger honest.

## Principles

1. **Manifest everything** — new artifacts need hash/sidecar paths.  
2. **Staged ops only** — no free-floating capture tools that ignore CASEFILE.  
3. **No exploits** — see `docs/guides/CONTRIBUTING-PROBES.md` and `SECURITY.md`.  
4. **Fail closed** on integrity errors.  
5. **Docs travel with code** — update DESIGN/OPS-DISCIPLINE/CHANGELOG when behavior changes.

## Development setup

### FAPs (C / ufbt)

```powershell
py -m pip install --upgrade ufbt
.\scripts\build-fap.ps1 -App all
```

### Desktop (Python 3.10+)

```bash
pip install -e "./desktop[dev]"
pytest -q desktop/tests
python -m flipper69 --help
```

### Orchestrator

```bash
python scripts/build_all.py --all
```

## PR checklist

- [ ] Ethics surface unchanged or strengthened  
- [ ] Schemas updated if JSON shapes change  
- [ ] Tests added for desktop logic  
- [ ] Version strings consistent when releasing  
- [ ] No secrets, PII, or real client captures in repo  

## Code style

- C: match existing Flipper/ufbt patterns; free resources; bound strings  
- Python: 3.10+, stdlib-first, optional extras for PDF  
- PowerShell: keep `sync/flipper69-sync.ps1` working as legacy path  

## License

MIT — by contributing you agree your changes are MIT-licensed.
