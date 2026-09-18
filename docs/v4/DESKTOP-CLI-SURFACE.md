# flipper69 Desktop CLI Surface — v4 (ARGUS VEIL draft)

Air-gapped first. Default bind for any UI: `127.0.0.1` only.

## Core

```bash
flipper69 sync --sd PATH
flipper69 sync --serial auto|COM_PORT
flipper69 audit [opId] [--deep] [--merkle]
flipper69 seal opId [--merkle] [--chunk-size N]
flipper69 list [--type T] [--domain D] [--q STR] [--campaign C]
flipper69 timeline opId [--session N]
flipper69 report opId -o out.html [--pdf out.pdf] [--redact-pii]
flipper69 pack opId [--mode full|share-safe] -o file.f69pack.zip
flipper69 migrate --from 3 --to 4 [--vault PATH]
```

## Workbench

```bash
flipper69 tui
flipper69 dashboard --bind 127.0.0.1 --port 8769
flipper69 export opId --fmt siem-jsonl|csv|inventory-json -o PATH
flipper69 vault list|init|use NAME
flipper69 operator list|add NAME
```

## Authoring

```bash
flipper69 template list|apply ID --acknowledge-auth --label L
flipper69 scaffold probe DOMAIN --codename NAME
flipper69 claim-import --from stock-tree --op opId   # bulk desktop claim
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success / audit PASS |
| 1 | Integrity FAIL |
| 2 | Usage / missing op |
| 3 | Migration conflict |
