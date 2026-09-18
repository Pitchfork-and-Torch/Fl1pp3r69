# Fl1pp3r69 Firmware Overlay (v2.0.0)

Momentum-based firmware distro overlay. Canonical FAP sources live in `../../fap/`.

## Quick Start

```powershell
# From repo root
.\scripts\init-firmware-fork.ps1
.\scripts\sync-faps-to-firmware.ps1
.\scripts\apply-flipper69-patches.ps1
.\scripts\build-firmware.ps1
```

## Layout

| Path | Purpose |
|------|---------|
| `MANIFEST.json` | Upstream pin, FAP registry, patch map (v2.0.0) |
| `patches/` | OPSEC defaults, serial stubs, autostart scaffold |
| `theme/` | Obsidian/red theme pack (v2.0.0) |

## Upstream

Pinned to [Next-Flip/Momentum-Firmware](https://github.com/Next-Flip/Momentum-Firmware) `dev` branch.

Do not edit `../momentum/` by hand — use scripts in `../../scripts/`.

## Spec

- Design: `docs/superpowers/specs/2026-07-07-flipper69-momentum-fork-design.md`
- Plan: `docs/superpowers/plans/2026-07-07-flipper69-momentum-fork.md`
- Product docs: `docs/DESIGN.md` · `docs/OPS-DISCIPLINE.md`