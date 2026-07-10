/**
 * FL1PP3R69 v2 DEWDROP — NFC read / write / emulate probe
 * Copy tags you own to SD, print to blank writable tags, or emulate to readers.
 * Captures land in the active CASEFILE op with .meta.json sidecars.
 */
#include <furi.h>
#include <furi_hal_rtc.h>
#include <furi_hal_vibro.h>
#include <gui/gui.h>
#include <storage/storage.h>

#include <nfc/nfc.h>
#include <nfc/nfc_device.h>
#include <nfc/nfc_listener.h>
#include <nfc/nfc_scanner.h>
#include <nfc/protocols/iso14443_3a/iso14443_3a.h>
#include <nfc/protocols/iso14443_3a/iso14443_3a_poller_sync.h>
#include <nfc/protocols/mf_classic/mf_classic.h>
#include <nfc/protocols/mf_classic/mf_classic_poller_sync.h>
#include <nfc/protocols/mf_ultralight/mf_ultralight.h>
#include <nfc/protocols/mf_ultralight/mf_ultralight_poller_sync.h>
#include <nfc/protocols/nfc_protocol.h>
#include <nfc/protocols/st25tb/st25tb.h>
#include <nfc/protocols/st25tb/st25tb_poller_sync.h>

#include <stdio.h>
#include <string.h>

#define F69_OPS_ROOT  EXT_PATH("flipper69/operations")
#define F69_NFC_CACHE EXT_PATH("nfc")
#define F69_VER       "2.0.0"

typedef enum {
    F69NfcMenu,
    F69NfcRead,
    F69NfcWriteArm,
    F69NfcWrite,
    F69NfcEmulate,
} F69NfcMode;

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMutex* mutex;
    bool running;
    F69NfcMode mode;
    uint8_t menu_sel;
    char status[64];
    char detail[64];
    char saved_path[256];
    bool write_armed;
    Nfc* nfc;
    NfcDevice* device;
    NfcScanner* scanner;
    NfcListener* listener;
    FuriSemaphore* scan_sem;
    NfcProtocol detected[8];
    size_t detected_count;
} ProbeNfc;

typedef struct {
    FuriSemaphore* sem;
    NfcProtocol protocols[8];
    size_t count;
} ScanCtx;

static bool probe_join_path(char* out, size_t out_len, const char* dir, const char* name) {
    size_t dir_len = strlen(dir);
    size_t name_len = strlen(name);
    if(dir_len + 1 + name_len >= out_len) return false;
    memcpy(out, dir, dir_len);
    out[dir_len] = '/';
    memcpy(out + dir_len + 1, name, name_len);
    out[dir_len + 1 + name_len] = '\0';
    return true;
}

static void probe_status(ProbeNfc* app, const char* status, const char* detail) {
    strncpy(app->status, status, sizeof(app->status) - 1);
    if(detail) {
        strncpy(app->detail, detail, sizeof(app->detail) - 1);
    } else {
        app->detail[0] = '\0';
    }
}

static bool probe_latest_op_captures(Storage* storage, char* out, size_t out_len) {
    char paths[16][192];
    size_t count = 0;

    File* dir = storage_file_alloc(storage);
    if(storage_dir_open(dir, F69_OPS_ROOT)) {
        char name[64];
        FileInfo info;
        while(storage_dir_read(dir, &info, name, sizeof(name))) {
            if((info.flags & FSF_DIRECTORY) && strncmp(name, "op-", 3) == 0) {
                snprintf(paths[count], 192, "%s/%s", F69_OPS_ROOT, name);
                count++;
                if(count >= 16) break;
            }
        }
        storage_dir_close(dir);
    }
    storage_file_free(dir);

    if(count == 0) return false;
    snprintf(out, out_len, "%s/captures", paths[count - 1]);
    return true;
}

static bool probe_find_latest_nfc(Storage* storage, char* out, size_t out_len) {
    char captures[256];
    if(!probe_latest_op_captures(storage, captures, sizeof(captures))) {
        strncpy(captures, F69_NFC_CACHE, sizeof(captures) - 1);
    }
    storage_common_mkdir(storage, captures);

    File* dir = storage_file_alloc(storage);
    if(!storage_dir_open(dir, captures)) {
        storage_file_free(dir);
        return false;
    }

    char best[128] = {0};
    char name[96];
    FileInfo info;
    while(storage_dir_read(dir, &info, name, sizeof(name))) {
        if(info.flags & FSF_DIRECTORY) continue;
        size_t len = strlen(name);
        if(len < 5) continue;
        if(strcmp(name + len - 4, ".nfc") != 0) continue;
        strncpy(best, name, sizeof(best) - 1);
    }
    storage_dir_close(dir);
    storage_file_free(dir);

    if(best[0] == '\0') return false;
    return probe_join_path(out, out_len, captures, best);
}

static void probe_write_meta(Storage* storage, const char* op_captures, const char* nfc_path, const char* action) {
    char meta[256];
    snprintf(meta, sizeof(meta), "%s/dewdrop.meta.json", op_captures);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char body[384];
    snprintf(
        body,
        sizeof(body),
        "{\"probe\":\"dewdrop\",\"ver\":\"%s\",\"action\":\"%s\",\"nfc\":\"%s\",\"ts\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\"}\n",
        F69_VER,
        action,
        nfc_path,
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second);

    File* file = storage_file_alloc(storage);
    if(storage_file_open(file, meta, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_write(file, body, strlen(body));
        storage_file_close(file);
    }
    storage_file_free(file);
}

static void probe_mfc_keys_default(MfClassicDeviceKeys* keys) {
    const uint8_t def[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    memset(keys, 0, sizeof(*keys));
    for(uint8_t i = 0; i < MF_CLASSIC_TOTAL_SECTORS_MAX; i++) {
        memcpy(keys->key_a[i].data, def, sizeof(def));
        memcpy(keys->key_b[i].data, def, sizeof(def));
        keys->key_a_mask |= (1ULL << i);
        keys->key_b_mask |= (1ULL << i);
    }
}

static NfcProtocol probe_pick_protocol(NfcProtocol* protos, size_t count) {
    static const NfcProtocol order[] = {
        NfcProtocolMfDesfire,
        NfcProtocolMfPlus,
        NfcProtocolMfClassic,
        NfcProtocolSlix,
        NfcProtocolMfUltralight,
        NfcProtocolSt25tb,
        NfcProtocolFelica,
        NfcProtocolIso15693_3,
        NfcProtocolIso14443_4a,
        NfcProtocolIso14443_4b,
        NfcProtocolIso14443_3a,
        NfcProtocolIso14443_3b,
    };
    for(size_t i = 0; i < COUNT_OF(order); i++) {
        for(size_t j = 0; j < count; j++) {
            if(protos[j] == order[i]) return order[i];
        }
    }
    return protos[0];
}

static void probe_scan_cb(NfcScannerEvent event, void* context) {
    ScanCtx* ctx = context;
    if(event.type != NfcScannerEventTypeDetected) return;
    ctx->count = event.data.protocol_num;
    if(ctx->count > COUNT_OF(ctx->protocols)) ctx->count = COUNT_OF(ctx->protocols);
    memcpy(ctx->protocols, event.data.protocols, ctx->count * sizeof(NfcProtocol));
    furi_semaphore_release(ctx->sem);
}

static bool probe_scan_tag(ProbeNfc* app, uint32_t timeout_ms) {
    ScanCtx ctx = {.sem = app->scan_sem, .count = 0};
    nfc_scanner_start(app->scanner, probe_scan_cb, &ctx);
    FuriStatus status = furi_semaphore_acquire(app->scan_sem, timeout_ms);
    nfc_scanner_stop(app->scanner);
    if(status != FuriStatusOk || ctx.count == 0) return false;
    app->detected_count = ctx.count;
    memcpy(app->detected, ctx.protocols, ctx.count * sizeof(NfcProtocol));
    return true;
}

static bool probe_read_protocol(ProbeNfc* app, NfcProtocol protocol) {
    nfc_device_clear(app->device);

    if(protocol == NfcProtocolMfUltralight) {
        MfUltralightData* data = mf_ultralight_alloc();
        MfUltralightPollerAuthContext auth = {0};
        auth.skip_auth = true;
        MfUltralightError err = mf_ultralight_poller_sync_read_card(app->nfc, data, &auth);
        if(err != MfUltralightErrorNone) {
            mf_ultralight_free(data);
            return false;
        }
        nfc_device_set_data(app->device, NfcProtocolMfUltralight, data);
        mf_ultralight_free(data);
        return true;
    }

    if(protocol == NfcProtocolMfClassic) {
        MfClassicType type;
        if(mf_classic_poller_sync_detect_type(app->nfc, &type) != MfClassicErrorNone) return false;
        MfClassicData* data = mf_classic_alloc();
        MfClassicDeviceKeys keys;
        probe_mfc_keys_default(&keys);
        MfClassicError err = mf_classic_poller_sync_read(app->nfc, &keys, data);
        if(err != MfClassicErrorNone && err != MfClassicErrorPartialRead) {
            mf_classic_free(data);
            return false;
        }
        nfc_device_set_data(app->device, NfcProtocolMfClassic, data);
        mf_classic_free(data);
        return true;
    }

    if(protocol == NfcProtocolSt25tb) {
        St25tbData* data = st25tb_alloc();
        if(st25tb_poller_sync_read(app->nfc, data) != St25tbErrorNone) {
            st25tb_free(data);
            return false;
        }
        nfc_device_set_data(app->device, NfcProtocolSt25tb, data);
        st25tb_free(data);
        return true;
    }

    if(protocol == NfcProtocolIso14443_3a || nfc_protocol_has_parent(protocol, NfcProtocolIso14443_3a)) {
        Iso14443_3aData* data = iso14443_3a_alloc();
        if(iso14443_3a_poller_sync_read(app->nfc, data) != Iso14443_3aErrorNone) {
            iso14443_3a_free(data);
            return false;
        }
        nfc_device_set_data(app->device, NfcProtocolIso14443_3a, data);
        iso14443_3a_free(data);
        return true;
    }

    return false;
}

static bool probe_save_capture(ProbeNfc* app) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    char captures[256];
    if(!probe_latest_op_captures(storage, captures, sizeof(captures))) {
        strncpy(captures, F69_NFC_CACHE, sizeof(captures) - 1);
    }
    storage_common_mkdir(storage, captures);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char stamp[32];
    snprintf(
        stamp,
        sizeof(stamp),
        "nfc_%02d%02d_%02d%02d.nfc",
        (int)dt.month,
        (int)dt.day,
        (int)dt.hour,
        (int)dt.minute);
    if(!probe_join_path(app->saved_path, sizeof(app->saved_path), captures, stamp)) {
        probe_status(app, "Path too long", NULL);
        furi_record_close(RECORD_STORAGE);
        return false;
    }

    bool ok = nfc_device_save(app->device, app->saved_path);
    if(ok) {
        probe_write_meta(storage, captures, app->saved_path, "read");
        const char* name = nfc_device_get_name(app->device, NfcDeviceNameTypeFull);
        probe_status(app, "Saved tag", name ? name : "nfc");
    } else {
        probe_status(app, "Save failed", NULL);
    }
    furi_record_close(RECORD_STORAGE);
    return ok;
}

static bool probe_write_loaded(ProbeNfc* app) {
    NfcProtocol protocol = nfc_device_get_protocol(app->device);
    if(protocol == NfcProtocolInvalid) return false;

    if(protocol == NfcProtocolMfUltralight) {
        const MfUltralightData* src = nfc_device_get_data(app->device, NfcProtocolMfUltralight);
        uint16_t end = src->pages_total ? src->pages_total : mf_ultralight_get_pages_total(src->type);
        uint16_t start = 4;
        if(end > MF_ULTRALIGHT_MAX_PAGE_NUM) end = MF_ULTRALIGHT_MAX_PAGE_NUM;
        for(uint16_t page = start; page < end; page++) {
            if(mf_ultralight_poller_sync_write_page(app->nfc, page, (MfUltralightPage*)&src->page[page]) !=
               MfUltralightErrorNone) {
                return false;
            }
        }
        return true;
    }

    if(protocol == NfcProtocolMfClassic) {
        const MfClassicData* src = nfc_device_get_data(app->device, NfcProtocolMfClassic);
        uint16_t blocks = mf_classic_get_total_block_num(src->type);
        for(uint16_t block = 0; block < blocks; block++) {
            if(!mf_classic_is_block_read(src, block)) continue;
            MfClassicKey key = mf_classic_get_key(src, mf_classic_get_sector_by_block(block), MfClassicKeyTypeA);
            MfClassicBlock blk;
            memcpy(blk.data, src->block[block].data, MF_CLASSIC_BLOCK_SIZE);
            if(mf_classic_poller_sync_write_block(
                   app->nfc, block, &key, MfClassicKeyTypeA, &blk) != MfClassicErrorNone) {
                return false;
            }
        }
        return true;
    }

    if(protocol == NfcProtocolSt25tb) {
        const St25tbData* src = nfc_device_get_data(app->device, NfcProtocolSt25tb);
        uint8_t blocks = st25tb_get_block_count(src->type);
        for(uint8_t block = 0; block < blocks; block++) {
            if(st25tb_poller_sync_write_block(app->nfc, block, src->blocks[block]) != St25tbErrorNone) {
                return false;
            }
        }
        return true;
    }

    return false;
}

static NfcCommand probe_emulate_cb(NfcGenericEvent event, void* context) {
    UNUSED(event);
    ProbeNfc* app = context;
    if(!app->running) return NfcCommandStop;
    return NfcCommandContinue;
}

static void probe_stop_rf(ProbeNfc* app) {
    if(app->listener) {
        nfc_listener_stop(app->listener);
        nfc_listener_free(app->listener);
        app->listener = NULL;
    }
    if(app->scanner) {
        nfc_scanner_stop(app->scanner);
    }
}

static void probe_do_read(ProbeNfc* app) {
    probe_status(app, "Hold tag to Flipper", "Scanning...");
    view_port_update(app->view_port);

    if(!probe_scan_tag(app, 15000)) {
        probe_status(app, "No tag detected", "Try again");
        app->mode = F69NfcMenu;
        return;
    }

    NfcProtocol protocol = probe_pick_protocol(app->detected, app->detected_count);
    probe_status(app, "Reading...", nfc_device_get_protocol_name(protocol));
    view_port_update(app->view_port);

    if(!probe_read_protocol(app, protocol)) {
        probe_status(app, "Read failed", "Keys or type?");
        app->mode = F69NfcMenu;
        return;
    }

    if(probe_save_capture(app)) {
        furi_hal_vibro_on(true);
        furi_delay_ms(80);
        furi_hal_vibro_on(false);
    }
    app->mode = F69NfcMenu;
}

static void probe_do_write(ProbeNfc* app) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    if(app->saved_path[0] == '\0') {
        probe_find_latest_nfc(storage, app->saved_path, sizeof(app->saved_path));
    }
    if(app->saved_path[0] == '\0' || !nfc_device_load(app->device, app->saved_path)) {
        probe_status(app, "No .nfc to write", "Read a tag first");
        furi_record_close(RECORD_STORAGE);
        app->mode = F69NfcMenu;
        return;
    }
    furi_record_close(RECORD_STORAGE);

    probe_status(app, "Hold BLANK tag", "Writing...");
    view_port_update(app->view_port);

    if(!probe_scan_tag(app, 15000)) {
        probe_status(app, "No tag detected", NULL);
        app->mode = F69NfcMenu;
        return;
    }

    bool ok = probe_write_loaded(app);
    if(ok) {
        char captures[256];
        Storage* st = furi_record_open(RECORD_STORAGE);
        if(probe_latest_op_captures(st, captures, sizeof(captures))) {
            probe_write_meta(st, captures, app->saved_path, "write");
        }
        furi_record_close(RECORD_STORAGE);
        probe_status(app, "Write complete", "Tag printed");
        furi_hal_vibro_on(true);
        furi_delay_ms(120);
        furi_hal_vibro_on(false);
    } else {
        probe_status(app, "Write failed", "Writable tag?");
    }
    app->write_armed = false;
    app->mode = F69NfcMenu;
}

static void probe_do_emulate(ProbeNfc* app) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    if(app->saved_path[0] == '\0') {
        probe_find_latest_nfc(storage, app->saved_path, sizeof(app->saved_path));
    }
    if(app->saved_path[0] == '\0' || !nfc_device_load(app->device, app->saved_path)) {
        probe_status(app, "No .nfc loaded", "Read a tag first");
        furi_record_close(RECORD_STORAGE);
        app->mode = F69NfcMenu;
        return;
    }
    furi_record_close(RECORD_STORAGE);

    NfcProtocol protocol = nfc_device_get_protocol(app->device);
    const NfcDeviceData* data = nfc_device_get_data(app->device, protocol);
    app->listener = nfc_listener_alloc(app->nfc, protocol, data);
    nfc_listener_start(app->listener, probe_emulate_cb, app);
    probe_status(app, "Emulating tag", "Hold to reader");
    app->mode = F69NfcEmulate;
}

static void probe_draw(Canvas* canvas, void* ctx) {
    ProbeNfc* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);

    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 2, 9, "DEWDROP NFC");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 90, 9, "v" F69_VER);
    canvas_draw_line(canvas, 0, 11, 127, 11);

    if(app->mode == F69NfcMenu) {
        const char* items[] = {
            "[1] Read tag (copy)",
            "[2] Write tag (print)",
            "[3] Emulate tag",
        };
        for(uint8_t i = 0; i < 3; i++) {
            int y = 22 + (i * 10);
            if(i == app->menu_sel) {
                canvas_draw_box(canvas, 0, y - 8, 128, 10);
                canvas_set_color(canvas, ColorWhite);
                canvas_draw_str(canvas, 2, y, items[i]);
                canvas_set_color(canvas, ColorBlack);
            } else {
                canvas_draw_str(canvas, 2, y, items[i]);
            }
        }
        canvas_draw_line(canvas, 0, 52, 127, 52);
        if(app->saved_path[0]) {
            const char* slash = strrchr(app->saved_path, '/');
            canvas_draw_str(canvas, 2, 61, slash ? slash + 1 : app->saved_path);
        } else if(app->status[0]) {
            canvas_draw_str(canvas, 2, 61, app->status);
        } else {
            canvas_draw_str(canvas, 2, 61, "CASEFILE captures/");
        }
    } else if(app->mode == F69NfcWriteArm) {
        canvas_draw_str(canvas, 2, 24, "AUTHORIZED TARGET");
        canvas_draw_str(canvas, 2, 36, "only tags you own");
        canvas_draw_str(canvas, 2, 48, "OK=I own this tag");
        canvas_draw_str(canvas, 2, 62, "BACK=cancel");
    } else {
        canvas_draw_str(canvas, 2, 24, app->status);
        if(app->detail[0]) canvas_draw_str(canvas, 2, 36, app->detail);
        if(app->mode == F69NfcEmulate) {
            canvas_draw_frame(canvas, 40, 42, 48, 10);
            canvas_draw_str(canvas, 48, 50, "LIVE RF");
            canvas_draw_str(canvas, 2, 62, "BACK=stop emulate");
        } else if(app->mode == F69NfcRead || app->mode == F69NfcWrite) {
            canvas_draw_str(canvas, 2, 50, "hold tag steady");
            canvas_draw_str(canvas, 2, 62, "scanning...");
        }
    }

    furi_mutex_release(app->mutex);
}

static void probe_input(InputEvent* event, void* ctx) {
    ProbeNfc* app = ctx;
    if(event->type != InputTypeShort && event->type != InputTypeLong) return;

    furi_mutex_acquire(app->mutex, FuriWaitForever);

    if(event->type == InputTypeShort && event->key == InputKeyBack) {
        if(app->mode == F69NfcEmulate) {
            probe_stop_rf(app);
            app->mode = F69NfcMenu;
        } else if(app->mode == F69NfcWriteArm) {
            app->write_armed = false;
            app->mode = F69NfcMenu;
        } else if(app->mode != F69NfcMenu) {
            app->mode = F69NfcMenu;
        } else {
            app->running = false;
        }
        furi_mutex_release(app->mutex);
        view_port_update(app->view_port);
        return;
    }

    if(app->mode == F69NfcMenu && event->type == InputTypeShort) {
        if(event->key == InputKeyUp && app->menu_sel > 0) app->menu_sel--;
        if(event->key == InputKeyDown && app->menu_sel < 2) app->menu_sel++;
        if(event->key == InputKeyOk) {
            if(app->menu_sel == 0) {
                app->mode = F69NfcRead;
            } else if(app->menu_sel == 1) {
                app->mode = F69NfcWriteArm;
            } else {
                probe_do_emulate(app);
            }
        }
    } else if(app->mode == F69NfcWriteArm && event->type == InputTypeShort && event->key == InputKeyOk) {
        app->write_armed = true;
        app->mode = F69NfcWrite;
    }

    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t probe_nfc_main(void* p) {
    UNUSED(p);

    ProbeNfc* app = malloc(sizeof(ProbeNfc));
    furi_check(app);
    memset(app, 0, sizeof(ProbeNfc));
    app->running = true;
    app->mode = F69NfcMenu;
    probe_status(app, "Ready", "Read / Write / Emulate");

    app->nfc = nfc_alloc();
    app->device = nfc_device_alloc();
    app->scanner = nfc_scanner_alloc(app->nfc);
    app->scan_sem = furi_semaphore_alloc(1, 0);

    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    app->mutex = furi_mutex_alloc(FuriMutexTypeNormal);
    view_port_draw_callback_set(app->view_port, probe_draw, app);
    view_port_input_callback_set(app->view_port, probe_input, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);

    while(app->running) {
        if(app->mode == F69NfcRead) {
            probe_do_read(app);
        } else if(app->mode == F69NfcWrite && app->write_armed) {
            probe_do_write(app);
        }

        furi_mutex_acquire(app->mutex, FuriWaitForever);
        furi_mutex_release(app->mutex);
        view_port_update(app->view_port);
        furi_delay_ms(50);
    }

    probe_stop_rf(app);
    nfc_scanner_free(app->scanner);
    nfc_device_free(app->device);
    nfc_free(app->nfc);
    furi_semaphore_free(app->scan_sem);

    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_mutex_free(app->mutex);
    furi_record_close(RECORD_GUI);
    free(app);
    return 0;
}