# Security Policy — Fl1pp3r69

## Supported versions

| Version | Supported |
|---------|-----------|
| 3.x (VEIL LEDGER) | Yes |
| 2.x | Security fixes on best-effort basis |
| < 2.0 | No |

## Safe use

Fl1pp3r69 is for **authorized physical-layer security research** on hardware you own or have explicit permission to test.

This project **does not** and **will not** ship:

- Remote exploit frameworks  
- Jamming or RF denial tools  
- Region TX unlock / bypass  
- Credential theft or banking card full-clone pipelines  

Operators are solely responsible for compliance with local law and authorization scope.

## Integrity model

- Artifacts are SHA-256 hashed into `CASEFILE-MANIFEST.json` before trusted EXFIL.  
- Desktop tools re-verify hashes; mismatches **fail closed**.  
- Panic wipe removes operation metadata only — not firmware.

## Reporting vulnerabilities

Report security issues that affect:

- Integrity bypass (silent hash accept)  
- Path traversal writing outside op folders  
- Panic wipe destroying non-op data  
- Auth gate bypass for write/TX features  

Prefer private disclosure to the maintainers via GitHub Security Advisories on [Pitchfork-and-Torch/Fl1pp3r69](https://github.com/Pitchfork-and-Torch/Fl1pp3r69).

Do **not** open public issues that include exploit weaponization against third parties.

## Scope exclusions

- Misuse of stock Flipper radio features  
- Social engineering / physical break-in techniques  
- Third-party firmware unrelated to this repo  
