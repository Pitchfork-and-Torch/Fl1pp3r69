/**
 * FL1PP3R69 v2 — DAMP_CROWD Sub-GHz probe sidecar
 * Writes manifest metadata into the active CASEFILE op.
 * Use the stock Sub-GHz app for capture; this seals the chain.
 */
#include <furi.h>
#include <furi_hal_rtc.h>
#include <furi_hal_vibro.h>
#include <gui/gui.h>
#include <storage/storage.h>

#include <stdio.h>
#include <string.h>

#define F69_OPS_ROOT EXT_PATH("flipper69/operations")
#define F69_VER      "2.0.0"

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMutex* mutex;
    bool running;
    uint8_t menu_sel;
    uint8_t anim;
    char status[48];
    char detail[48];
    char op_name[64];
    char meta_path[256];
} ProbeSubGhz;

static bool damp_latest_op(Storage* storage, char* op_path, size_t op_len, char* name_out, size_t name_len) {
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

static bool damp_write_sidecar(ProbeSubGhz* app, const char* band) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    char op_path[192];
    if(!damp_latest_op(storage, op_path, sizeof(op_path), app->op_name, sizeof(app->op_name))) {
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
    char fname[32];
    snprintf(
        fname,
        sizeof(fname),
        "dampcrowd_%02u%02u%02u.meta.json",
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

    char body[320];
    snprintf(
        body,
        sizeof(body),
        "{\n"
        "  \"probe\":\"dampcrowd\",\n"
        "  \"ver\":\"%s\",\n"
        "  \"band\":\"%s\",\n"
        "  \"note\":\"use Sub-GHz app for raw capture; sidecar seals chain\",\n"
        "  \"ts\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\"\n"
        "}\n",
        F69_VER,
        band,
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
        strncpy(app->status, "sidecar sealed", sizeof(app->status) - 1);
        snprintf(app->detail, sizeof(app->detail), "%.12s @ %.20s", band, app->op_name);
        furi_hal_vibro_on(true);
        furi_delay_ms(60);
        furi_hal_vibro_on(false);
    } else {
        strncpy(app->status, "write failed", sizeof(app->status) - 1);
    }
    return ok;
}

static void draw_cb(Canvas* canvas, void* ctx) {
    ProbeSubGhz* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);

    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 2, 9, "DAMP_CROWD");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 90, 9, "v" F69_VER);
    canvas_draw_line(canvas, 0, 11, 127, 11);

    const char* items[] = {
        "[1] Sidecar 433.92",
        "[2] Sidecar 315.00",
        "[3] Sidecar 868.35",
        "[4] Sidecar generic",
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
    canvas_draw_str(canvas, 2, 61, app->status[0] ? app->status : "OK=seal  SubGHz=capture");

    furi_mutex_release(app->mutex);
}

static void input_cb(InputEvent* event, void* ctx) {
    ProbeSubGhz* app = ctx;
    if(event->type != InputTypeShort) return;

    furi_mutex_acquire(app->mutex, FuriWaitForever);
    if(event->key == InputKeyBack) {
        app->running = false;
    } else if(event->key == InputKeyUp && app->menu_sel > 0) {
        app->menu_sel--;
    } else if(event->key == InputKeyDown && app->menu_sel < 3) {
        app->menu_sel++;
    } else if(event->key == InputKeyOk) {
        static const char* bands[] = {"433.92", "315.00", "868.35", "generic"};
        damp_write_sidecar(app, bands[app->menu_sel]);
    }
    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t probe_subghz_main(void* p) {
    UNUSED(p);
    ProbeSubGhz* app = malloc(sizeof(ProbeSubGhz));
    furi_check(app);
    memset(app, 0, sizeof(ProbeSubGhz));
    strncpy(app->status, "ready", sizeof(app->status) - 1);
    app->running = true;
    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    app->mutex = furi_mutex_alloc(FuriMutexTypeNormal);
    view_port_draw_callback_set(app->view_port, draw_cb, app);
    view_port_input_callback_set(app->view_port, input_cb, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);

    while(app->running) {
        app->anim++;
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
