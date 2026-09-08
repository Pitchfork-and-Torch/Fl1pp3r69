#include "flipper69_opsec.h"

#include <furi.h>

#define TAG "Flipper69Opsec"
#define F69_VER "2.0.0"

static Flipper69OpsecDefaults f69_opsec_runtime = {
    .bluetooth_enabled = true,
    .bluetooth_adv_enabled = false,
    .device_name_generic = true,
    .tx_audit_log = true,
    .auto_opsec_on_new_op = true,
};

const Flipper69OpsecDefaults* flipper69_opsec_defaults_get(void) {
    return &f69_opsec_runtime;
}

void flipper69_apply_opsec_defaults(void) {
    const Flipper69OpsecDefaults* cfg = flipper69_opsec_defaults_get();
    FURI_LOG_I(
        TAG,
        "OPSEC v%s: adv=%d audit=%d generic_name=%d auto=%d",
        F69_VER,
        cfg->bluetooth_adv_enabled,
        cfg->tx_audit_log,
        cfg->device_name_generic,
        cfg->auto_opsec_on_new_op);
    /* bt_settings_set_adv_enabled(cfg->bluetooth_adv_enabled); — wire in P2 service */
}

void flipper69_opsec_set_adv(bool enabled) {
    f69_opsec_runtime.bluetooth_adv_enabled = enabled;
    FURI_LOG_I(TAG, "BT adv %s", enabled ? "ON" : "OFF");
}

void flipper69_opsec_engage_for_op(void) {
    f69_opsec_runtime.bluetooth_adv_enabled = false;
    f69_opsec_runtime.tx_audit_log = true;
    FURI_LOG_I(TAG, "OPSEC engaged for active CASEFILE op");
    flipper69_apply_opsec_defaults();
}
