#pragma once

#include "flipper69_fieldops.h"

#include <stdbool.h>
#include <storage/storage.h>

#define F69_ROOT     EXT_PATH("flipper69")
#define F69_OPS_ROOT EXT_PATH("flipper69/operations")
#define F69_MAX_OPS  24

typedef struct {
    char op_id[64];
    char codename[48];
    char workspace[32];
    F69OpType op_type;
    F69PathNum pathnum;
    F69Phase phase;
    bool opsec;
    bool authorized;
    char manifest_hash[65];
    char op_path[192];
    uint16_t capture_count;
} F69Operation;

bool f69_ensure_roots(Storage* storage);
bool f69_op_create(Storage* storage, F69Operation* op, F69OpType type, F69PathNum path);
bool f69_op_save(Storage* storage, const F69Operation* op);
bool f69_op_load(Storage* storage, F69Operation* op, const char* op_path);
bool f69_op_advance_phase(Storage* storage, F69Operation* op);
bool f69_op_run_auto(Storage* storage, F69Operation* op);
bool f69_op_close(Storage* storage, F69Operation* op);
bool f69_op_refresh_captures(Storage* storage, F69Operation* op);
bool f69_list_ops(Storage* storage, char paths[][192], size_t* count);
bool f69_audit_ops(Storage* storage, char* report, size_t report_len);
bool f69_panic_wipe(Storage* storage);
bool f69_update_index(Storage* storage);
