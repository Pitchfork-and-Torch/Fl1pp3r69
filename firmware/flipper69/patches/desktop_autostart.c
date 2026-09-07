/**
 * FLIPPER69 desktop autostart — launch CASEFILE Ops once after boot.
 * Phase P2: hook from desktop service or call from flipper69_service.
 */
#include <furi.h>
#include <applications.h>

#define TAG "Flipper69Desktop"
#define CASEFILE_FAP APP_ASSETS_PATH("apps/flipper69_casefile_ops.fap")

void flipper69_desktop_autostart(void) {
    FURI_LOG_I(TAG, "Autostart CASEFILE Ops");
    /* loader_open(CASEFILE_FAP); — wired in P2 against desktop/loader APIs */
}