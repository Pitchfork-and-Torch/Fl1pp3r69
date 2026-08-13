#pragma once

#include <stdbool.h>

typedef struct {
    bool bluetooth_enabled;
    bool bluetooth_adv_enabled;
    bool device_name_generic;
    bool tx_audit_log;
    bool auto_opsec_on_new_op;
} Flipper69OpsecDefaults;

const Flipper69OpsecDefaults* flipper69_opsec_defaults_get(void);
void flipper69_apply_opsec_defaults(void);
void flipper69_opsec_set_adv(bool enabled);
void flipper69_opsec_engage_for_op(void);