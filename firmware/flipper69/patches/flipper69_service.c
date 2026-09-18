/**
 * FLIPPER69 startup service — applies OPSEC defaults before desktop.
 * Phase P2: register in applications/services/flipper69/application.fam
 */
#include <furi.h>
#include <flipper69/flipper69_opsec.h>

#define TAG "Flipper69"

static void flipper69_service_startup(void) {
    FURI_LOG_I(TAG, "Applying OPSEC defaults");
    flipper69_apply_opsec_defaults();
}

int32_t flipper69_service_app(void* p) {
    UNUSED(p);
    flipper69_service_startup();
    return 0;
}