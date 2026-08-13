/**
 * FL1PP3R69 v4.0 ARGUS VEIL — EMBER_TRACE IR probe sidecar
 * Writes IR session metadata into the active CASEFILE op.
 * Use the stock Infrared app for raw capture/transmit; this seals the chain.
 * Authorized research on owned hardware only. No IR blast packs.
 */
#include <furi.h>
#include <furi_hal_rtc.h>
#include <furi_hal_vibro.h>
#include <gui/gui.h>
#include <storage/storage.h>

#include <stdio.h>
#include <string.h>

#define F69_ROOT     EXT_PATH("flipper69")
#define F69_OPS_ROOT EXT_PATH("flipper69/operations")
#define F69_VER      "4.0.0"

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMutex* mutex;
    bool running;
    uint8_t menu_sel;
    char status[48];
    char detail[48];
    char op_name[64];
    char meta_path[256];
} ProbeIr;

static bool ember_parse_active_op(Storage* storage, char* op_path, size_t op_len, char* name_out, size_t name_len) {
    char active_path[192];
    snprintf(active_path, sizeof(active_path), "%s/ACTIVE_OP.json", F69_ROOT);
    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, active_path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        storage_file_free(file);
        return false;
    }
    char buf[384];
    size_t n = storage_file_read(file, buf, sizeof(buf) - 1);
    buf[n] = '\0';
    storage_file_close(file);
    storage_file_free(file);

    const char* key = "\"opId\":\"";
    const char* start = strstr(buf, key);
    if(!start) return false;
    start += strlen(key);
    const char* end = strchr(start, '"');
    if(!end || end <= start) return false;
    size_t len = (size_t)(end - start);
    if(len >= name_len) len = name_len - 1;
    memcpy(name_out, start, len);
    name_out[len] = '\0';
    snprintf(op_path, op_len, "%s/%s", F69_OPS_ROOT, name_out);
    return true;
}

static bool ember_latest_op(Storage* storage, char* op_path, size_t op_len, char* name_out, size_t name_len) {
    if(ember_parse_active_op(storage, op_path, op_len, name_out, name_len)) {
        return true;
    }

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
    strncpy(op_path, paths[count - 1], op_len - 1);
    op_path[op_len - 1] = '\0';
    const char* slash = strrchr(op_path, '/');
    if(slash && name_out) {
        strncpy(name_out, slash + 1, name_len - 1);
        name_out[name_len - 1] = '\0';
    }
    return true;
}

static bool ember_write_sidecar(ProbeIr* app, const char* protocol) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    char op_path[192];
    if(!ember_latest_op(storage, op_path, sizeof(op_path), app->op_name, sizeof(app->op_name))) {
        strncpy(app->status, "no active op", sizeof(app->status) - 1);
        strncpy(app->detail, "open CASEFILE first", sizeof(app->detail) - 1);
        furi_record_close(RECORD_STORAGE);
        return false;
    }

    char cap[256];
    snprintf(cap, sizeof(cap), "%s/captures", op_path);
    storage_common_mkdir(storage, cap);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char fname[40];
    snprintf(
        fname,
        sizeof(fname),
        "ember_%02u%02u%02u.meta.json",
        (unsigned)dt.hour % 100,
        (unsigned)dt.minute % 100,
        (unsigned)dt.second % 100);

    size_t cap_len = strlen(cap);
    size_t name_len = strlen(fname);
    if(cap_len + 1 + name_len >= sizeof(app->meta_path)) {
        strncpy(app->status, "path too long", sizeof(app->status) - 1);
        furi_record_close(RECORD_STORAGE);
        return false;
    }
    memcpy(app->meta_path, cap, cap_len);
    app->meta_path[cap_len] = '/';
    memcpy(app->meta_path + cap_len + 1, fname, name_len);
    app->meta_path[cap_len + 1 + name_len] = '\0';

    char body[360];
    snprintf(
        body,
        sizeof(body),
        "{\n"
        "  \"probe\":\"ember_trace\",\n"
        "  \"ver\":\"%s\",\n"
        "  \"protocol\":\"%s\",\n"
        "  \"note\":\"use Infrared app for raw capture; sidecar seals chain\",\n"
        "  \"txNote\":\"authorized owned hardware only\",\n"
        "  \"ts\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\"\n"
        "}\n",
        F69_VER,
        protocol,
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second);

    File* file = storage_file_alloc(storage);
    bool ok = false;
    if(storage_file_open(file, app->meta_path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_write(file, body, strlen(body));
        storage_file_close(file);
        ok = true;
    }
    storage_file_free(file);
    furi_record_close(RECORD_STORAGE);

    if(ok) {
        strncpy(app->status, "ember sealed", sizeof(app->status) - 1);
        snprintf(app->detail, sizeof(app->detail), "%.12s @ %.20s", protocol, app->op_name);
        furi_hal_vibro_on(true);
        furi_delay_ms(60);
        furi_hal_vibro_on(false);
    } else {
        strncpy(app->status, "write failed", sizeof(app->status) - 1);
    }
    return ok;
}

static void draw_cb(Canvas* canvas, void* ctx) {
    ProbeIr* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);

    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 2, 9, "EMBER_TRACE");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 90, 9, "v" F69_VER);
    canvas_draw_line(canvas, 0, 11, 127, 11);

    const char* items[] = {
        "[1] Sidecar NEC",
        "[2] Sidecar Samsung",
        "[3] Sidecar RC5/RC6",
        "[4] Sidecar raw/other",
    };
    for(uint8_t i = 0; i < 4; i++) {
        int y = 22 + (i * 9);
        if(i == app->menu_sel) {
            canvas_draw_box(canvas, 0, y - 7, 128, 9);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_str(canvas, 2, y, items[i]);
            canvas_set_color(canvas, ColorBlack);
        } else {
            canvas_draw_str(canvas, 2, y, items[i]);
        }
    }

    canvas_draw_line(canvas, 0, 52, 127, 52);
    canvas_draw_str(canvas, 2, 61, app->status[0] ? app->status : "OK=seal  IR app=capture");

    furi_mutex_release(app->mutex);
}

static void input_cb(InputEvent* event, void* ctx) {
    ProbeIr* app = ctx;
    if(event->type != InputTypeShort) return;

    furi_mutex_acquire(app->mutex, FuriWaitForever);
    if(event->key == InputKeyBack) {
        app->running = false;
    } else if(event->key == InputKeyUp && app->menu_sel > 0) {
        app->menu_sel--;
    } else if(event->key == InputKeyDown && app->menu_sel < 3) {
        app->menu_sel++;
    } else if(event->key == InputKeyOk) {
        static const char* protocols[] = {"NEC", "Samsung", "RC5_RC6", "raw_other"};
        ember_write_sidecar(app, protocols[app->menu_sel]);
    }
    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t probe_ir_main(void* p) {
    UNUSED(p);
    ProbeIr* app = malloc(sizeof(ProbeIr));
    furi_check(app);
    memset(app, 0, sizeof(ProbeIr));
    strncpy(app->status, "ready", sizeof(app->status) - 1);
    app->running = true;
    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    app->mutex = furi_mutex_alloc(FuriMutexTypeNormal);
    view_port_draw_callback_set(app->view_port, draw_cb, app);
    view_port_input_callback_set(app->view_port, input_cb, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);

    while(app->running) {
        view_port_update(app->view_port);
        furi_delay_ms(80);
    }

    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_mutex_free(app->mutex);
    furi_record_close(RECORD_GUI);
    free(app);
    return 0;
}
