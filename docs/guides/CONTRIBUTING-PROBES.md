# Contributing New Probes (Ethically)

Fl1pp3r69 accepts community probes that **capture metadata and seal CASEFILE integrity** — not attack tooling.

## Hard bans

Do **not** submit:

- Exploit code, dumps of commercial keys, or credential stuffing helpers  
- Jamming, flood, or denial-of-service TX packs  
- Region-unlock / TX bypass patches  
- Ungated bruteforce of rolling codes or PINs  
- Anything that lowers the barrier to unauthorized access  

When in doubt: **more auditable, more deliberate, more traceable.**

## Contract

1. Ship a `probe.plugin.json` validated by `schemas/probe.plugin.schema.json`.  
2. `ethics.noExploits` and `ethics.authorizedUseOnly` must be `true`.  
3. Prefer **sidecar FAPs** that write `.meta.json` into the active op `captures/` folder.  
4. Resolve active op via `ACTIVE_OP.json`, then newest `op-*`.  
5. Never write outside `/ext/flipper69/operations/<opId>/`.  
6. If TX-capable: document regional compliance and require on-screen authorization.  
7. No dynamic code loading framework on device.

## Minimal FAP checklist

- [ ] `application.fam` with clear non-weaponized description  
- [ ] Version aligned with suite (`3.x`)  
- [ ] Sidecar includes `probe`, `ver`, `ts`  
- [ ] Ownership/authorization UI when writing or transmitting  
- [ ] Example plugin descriptor under `examples/plugins/`  
- [ ] Docs: what it does / does not do  

## Review bar

Maintainers reject PRs that expand offensive surface even if “optional.”  
Metadata-only improvements and integrity tooling are welcome.
