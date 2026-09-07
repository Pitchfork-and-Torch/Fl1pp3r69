/**
 * FL1PP3R69 v4.0 ARGUS VEIL — GPIO LAB probe sidecar
 * Metadata only into active CASEFILE op. Authorized research on owned hardware.
 */
#include <furi.h>
#include <furi_hal_rtc.h>
#include <furi_hal_vibro.h>
#include <gui/gui.h>
#include <storage/storage.h>
#include <stdio.h>
#include <string.h>

#define F69_OPS_ROOT EXT_PATH("flipper69/operations")
#define F69_VER      "4.0.0"

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMutex* mutex;
    bool running;
    uint8_t menu_sel;
    char status[48];
    char op_name[64];
} ProbeApp;

static bool resolve_op(Storage* storage, char* op_path, size_t op_len, char* name_out, size_t name_len) {
    char active_path[192];
    snprintf(active_path, sizeof(active_path), EXT_PATH("flipper69") "/ACTIVE_OP.json");
    File* file = storage_file_alloc(storage);
    if(storage_file_open(file, active_path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        char buf[384];
        size_t n = storage_file_read(file, buf, sizeof(buf) - 1);
        buf[n] = '\0';
        storage_file_close(file);
        storage_file_free(file);
        const char* key = "\"opId\":\"";
        const char* s = strstr(buf, key);
        if(s) {
            s += 8;
            const char* e = strchr(s, '"');
            if(e && e > s) {
                size_t len = (size_t)(e - s);
                if(len >= name_len) len = name_len - 1;
                memcpy(name_out, s, len);
                name_out[len] = '\0';
                snprintf(op_path, op_len, "%s/%s", F69_OPS_ROOT, name_out);
                FileInfo info;
                if(storage_common_stat(storage, op_path, &info) == FSE_OK) return true;
            }
        }
    } else {
        storage_file_free(file);
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
    if(slash) {
        strncpy(name_out, slash + 1, name_len - 1);
        name_out[name_len - 1] = '\0';
    }
    return true;
}

static bool write_sidecar(ProbeApp* app, const char* label) {
    Storage* storage = furi_record_open(RECORD_STORAGE);
    char op_path[192];
    if(!resolve_op(storage, op_path, sizeof(op_path), app->op_name, sizeof(app->op_name))) {
        strncpy(app->status, "no active op", sizeof(app->status) - 1);
        furi_record_close(RECORD_STORAGE);
        return false;
    }
    char cap[256];
    snprintf(cap, sizeof(cap), "%s/captures", op_path);
    storage_common_mkdir(storage, cap);
    char art[256];
    snprintf(art, sizeof(art), "%s/artifacts", op_path);
    storage_common_mkdir(storage, art);
    snprintf(art, sizeof(art), "%s/artifacts/gpio", op_path);
    storage_common_mkdir(storage, art);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char path[288];
    snprintf(
        path,
        sizeof(path),
        "%s/gpio_%02u%02u%02u.meta.json",
        art,
        (unsigned)dt.hour % 100,
        (unsigned)dt.minute % 100,
        (unsigned)dt.second % 100);
    char body[360];
    snprintf(
        body,
        sizeof(body),
        "{\n"
        "  \"probe\":\"gpio\",\n"
        "  \"ver\":\"%s\",\n"
        "  \"label\":\"%s\",\n"
        "  \"note\":\"sidecar seals CASEFILE chain; stock app for raw\",\n"
        "  \"ts\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\"\n"
        "}\n",
        F69_VER,
        label,
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second);
    File* f = storage_file_alloc(storage);
    bool ok = false;
    if(storage_file_open(f, path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_write(f, body, strlen(body));
        storage_file_close(f);
        ok = true;
    }
    storage_file_free(f);
    furi_record_close(RECORD_STORAGE);
    strncpy(app->status, ok ? "sidecar sealed" : "write failed", sizeof(app->status) - 1);
    if(ok) {
        furi_hal_vibro_on(true);
        furi_delay_ms(50);
        furi_hal_vibro_on(false);
    }
    return ok;
}

static void draw_cb(Canvas* canvas, void* ctx) {
    ProbeApp* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);
    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 2, 9, "GPIO LAB");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 90, 9, "v" F69_VER);
    canvas_draw_line(canvas, 0, 11, 127, 11);
    const char* items[] = {"[1] Pin session", "[2] Logic claim", "[3] Script log", "[4] Lab note"};
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
    canvas_draw_str(canvas, 2, 61, app->status[0] ? app->status : "OK=seal meta");
    furi_mutex_release(app->mutex);
}

static void input_cb(InputEvent* event, void* ctx) {
    ProbeApp* app = ctx;
    if(event->type != InputTypeShort) return;
    furi_mutex_acquire(app->mutex, FuriWaitForever);
    if(event->key == InputKeyBack) {
        app->running = false;
    } else if(event->key == InputKeyUp && app->menu_sel > 0) {
        app->menu_sel--;
    } else if(event->key == InputKeyDown && app->menu_sel < 4 - 1) {
        app->menu_sel++;
    } else if(event->key == InputKeyOk) {
        static const char* vals[] = {"pin_session", "logic_claim", "script_log", "lab_note"};
        write_sidecar(app, vals[app->menu_sel]);
    }
    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t probe_gpio_main(void* p) {
    UNUSED(p);
    ProbeApp* app = malloc(sizeof(ProbeApp));
    furi_check(app);
    memset(app, 0, sizeof(ProbeApp));
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
