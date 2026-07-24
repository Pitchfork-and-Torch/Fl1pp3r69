/**
 * FL1PP3R69 USB serial exfil bridge — JSON-lines over CDC.
 * Phase P4: triggered by CASEFILE Ops EXFIL phase.
 * Desktop peer: sync/flipper69-sync.ps1
 */
#include <furi.h>
#include <stdio.h>
#include <string.h>

#define TAG "Flipper69Serial"
#define F69_VER "2.0.0"

void flipper69_serial_send_line(const char* json_line) {
    if(!json_line) return;
    FURI_LOG_D(TAG, "exfil: %s", json_line);
    /* CDC write — wired in P4 against furi_hal_usb_cdc */
}

void flipper69_serial_send_ping(void) {
    char line[96];
    snprintf(line, sizeof(line), "{\"type\":\"ping\",\"ver\":\"%s\"}", F69_VER);
    flipper69_serial_send_line(line);
}

void flipper69_serial_send_op_header(const char* op_id, const char* op_type, const char* phase) {
    if(!op_id) return;
    char line[256];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"op_header\",\"opId\":\"%s\",\"opType\":\"%s\",\"phase\":\"%s\",\"ver\":\"%s\"}",
        op_id,
        op_type ? op_type : "unified",
        phase ? phase : "EXFIL",
        F69_VER);
    flipper69_serial_send_line(line);
}

void flipper69_serial_send_op_close(const char* op_id, const char* manifest_hash) {
    if(!op_id) return;
    char line[256];
    snprintf(
        line,
        sizeof(line),
        "{\"type\":\"op_close\",\"opId\":\"%s\",\"manifestHash\":\"%s\",\"ver\":\"%s\"}",
        op_id,
        manifest_hash ? manifest_hash : "",
        F69_VER);
    flipper69_serial_send_line(line);
}
