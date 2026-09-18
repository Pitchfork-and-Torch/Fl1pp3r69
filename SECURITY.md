# Security Policy — Fl1pp3r69

## Supported versions

| Version | Codename | Supported |
|---------|----------|-----------|
| 4.x (ARGUS VEIL) | Current | Yes |
| 3.x (VEIL LEDGER) | Prior | Security fixes on best-effort basis |
| 2.x | Legacy | Best-effort only |
| < 2.0 | — | No |

Product version on device FAPs, desktop toolkit, landing JSON-LD, and `llms.txt` is **4.0.0 ARGUS VEIL**. Do not advertise a later product version until it is tagged.

## Authorized use

Fl1pp3r69 is for **authorized physical-layer security research** on hardware you own or have explicit written permission to test.

Operators are solely responsible for compliance with local law and authorization scope. Unauthorized access is out of scope and unsupported.

This project **does not** and **will not** ship:

- Exploit proof-of-concepts or remote exploit frameworks
- Undocumented attack procedures
- Jamming or RF denial tools
- Region TX unlock / bypass
- Credential theft or banking card full-clone pipelines

## Integrity model

- Artifacts are SHA-256 hashed into `CASEFILE-MANIFEST.json` before trusted EXFIL.
- Desktop tools re-verify hashes; mismatches **fail closed**.
- Panic wipe removes operation metadata only — not firmware.
- Local dashboard binds **127.0.0.1 / localhost / ::1** only.

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
