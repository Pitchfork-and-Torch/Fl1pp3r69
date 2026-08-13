/**
 * FLIPPER69 — OPSEC default settings patch
 * Apply at boot before any FAP launches.
 *
 * Integration: add to firmware/targets/f7/furi_hal/ or custom settings loader.
 */
#include <furi.h>

typedef struct {
    bool bluetooth_enabled;
    bool bluetooth_adv_enabled;
    bool device_name_generic;
    bool tx_audit_log;
    bool auto_opsec_on_new_op;
} Flipper69OpsecDefaults;

static const Flipper69OpsecDefaults f69_opsec_defaults = {
    .bluetooth_enabled = true,       /* BLE stack on for serial exfil */
    .bluetooth_adv_enabled = false,  /* No advertising during ops */
    .device_name_generic = true,     /* Rename to "Keyboard" or random */
    .tx_audit_log = true,            /* Log every TX to SD */
    .auto_opsec_on_new_op = true,    /* OP_PREP disables adv automatically */
};

const Flipper69OpsecDefaults* flipper69_opsec_defaults_get(void) {
    return &f69_opsec_defaults;
}

/* Called from Flipper69 boot hook — v0.3 */
void flipper69_apply_opsec_defaults(void) {
    /* bt_settings_set_adv_enabled(false); */
    /* storage_tx_log_enable(true); */
}