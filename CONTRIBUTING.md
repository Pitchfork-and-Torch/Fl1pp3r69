# Contributing to Fl1pp3r69

## Rules

- **Authorized research only** — owned hardware or written permission  
- No exploit packs, jamming, or TX region bypass in PRs  
- Keep CASEFILE manifest discipline (hashes, phases, no mystery files)  

## Dev

```powershell
git clone https://github.com/Pitchfork-and-Torch/Fl1pp3r69.git
cd Fl1pp3r69
# FAP build (requires ufbt)
.\scripts\build-fap.ps1 -App all
# Desktop sim
cd sync
.\new-field-op.ps1 -OpType survey -Label lab -Pathnum imps
```

## PRs

1. One logical change when possible  
2. Update schemas if OPERATION/manifest shape changes  
3. Run CI expectations: required paths + PowerShell parse  
4. Link ethics notes for anything that touches TX/replay  

See [SECURITY.md](SECURITY.md) and [docs/OPS-DISCIPLINE.md](docs/OPS-DISCIPLINE.md).
