# Flipper69 Phase Reference

## Operator Card

```
┌─────────────────────────────────────────────────────────┐
│  PHASE        │  YOU DO              │  DEVICE DOES    │
├───────────────┼──────────────────────┼─────────────────┤
│  INTAKE       │  Name target, type   │  Draft opId     │
│  OP_PREP      │  Confirm             │  BT adv OFF     │
│               │                      │  Write OPERATION│
│  PROBE        │  Pick SubGHz/NFC/IR  │  Launch plugin  │
│  CAPTURE      │  Hold / scan / save  │  Raw + .meta    │
│  VERIFY       │  OK to hash           │  CASEFILE-MANIF │
│  EXFIL        │  USB to PC            │  Serial stream  │
│  CLOSE        │  Seal op              │  Timeline final │
└─────────────────────────────────────────────────────────┘
```

## Op Type Matrix

| Type | Sub-GHz | NFC | IR | BadUSB | BLE survey |
|------|---------|-----|----|--------|------------|
| proximity | ● | ● | ● | ○ | ○ |
| survey | ● | ● | ○ | ○ | ● |
| replay | ● | ● | ● | ○ | ○ |
| inject | ○ | ○ | ○ | ● | ○ |
| unified | ● | ● | ● | ○ | ● |

● = primary phase  ○ = not available

## Confirm Strings

| Action | Required input |
|--------|----------------|
| Replay TX | `AUTHORIZED` |
| BadUSB run | `AUTHORIZED` |
| Panic wipe | `WIPE` + hold Back 2s |

## Desktop merge

Field ops land at:

```
.flipper69/ops/operations/op-YYYYMMDD-*/
```

Default root is `%USERPROFILE%\.flipper69\ops` (override with `FLIPPER69_OPS_ROOT`). The sync script validates manifest SHA-256 on ingest.