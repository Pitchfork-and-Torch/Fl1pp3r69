/**
 * FL1PP3R69 v2 — crypttool / manifest viewer
 * Browse CASEFILE-MANIFEST.json hashes on device.
 */
#include <furi.h>
#include <furi_hal_rtc.h>
#include <gui/gui.h>
#include <storage/storage.h>

#include <stdio.h>
#include <string.h>

#define F69_OPS_ROOT EXT_PATH("flipper69/operations")
#define F69_VER      "2.0.0"
#define F69_MAX_OPS  16

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMutex* mutex;
    Storage* storage;
    char op_paths[F69_MAX_OPS][192];
    size_t op_count;
    uint8_t op_sel;
    char preview[320];
    char hash_line[40];
    char item_count[24];
    char op_id_short[28];
    bool has_manifest;
    bool running;
} ManifestViewer;

static void mv_list_ops(ManifestViewer* app) {
    app->op_count = 0;
    File* dir = storage_file_alloc(app->storage);
    if(!storage_dir_open(dir, F69_OPS_ROOT)) {
        storage_file_free(dir);
        return;
    }
    char name[64];
    FileInfo info;
    while(storage_dir_read(dir, &info, name, sizeof(name))) {
        if(info.flags & FSF_DIRECTORY && strncmp(name, "op-", 3) == 0) {
            snprintf(app->op_paths[app->op_count], 192, "%s/%s", F69_OPS_ROOT, name);
            app->op_count++;
            if(app->op_count >= F69_MAX_OPS) break;
        }
    }
    storage_dir_close(dir);
    storage_file_free(dir);
    if(app->op_sel >= app->op_count && app->op_count > 0) {
        app->op_sel = (uint8_t)(app->op_count - 1);
    }
}

static void mv_load_selected(ManifestViewer* app) {
    app->has_manifest = false;
    app->preview[0] = '\0';
    app->hash_line[0] = '\0';
    app->item_count[0] = '\0';
    app->op_id_short[0] = '\0';

    if(app->op_count == 0) return;

    const char* op_path = app->op_paths[app->op_sel];
    const char* slash = strrchr(op_path, '/');
    const char* name = slash ? slash + 1 : op_path;
    if(strlen(name) > 24) {
        snprintf(app->op_id_short, sizeof(app->op_id_short), "..%.22s", name + strlen(name) - 22);
    } else {
        strncpy(app->op_id_short, name, sizeof(app->op_id_short) - 1);
    }

    char path[256];
    snprintf(path, sizeof(path), "%s/CASEFILE-MANIFEST.json", op_path);

    File* file = storage_file_alloc(app->storage);
    if(!storage_file_open(file, path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        storage_file_free(file);
        strncpy(app->hash_line, "no manifest yet", sizeof(app->hash_line) - 1);
        return;
    }

    size_t read = storage_file_read(file, app->preview, sizeof(app->preview) - 1);
    app->preview[read] = '\0';
    storage_file_close(file);
    storage_file_free(file);
    app->has_manifest = true;

    /* count items roughly */
    size_t items = 0;
    const char* p = app->preview;
    while((p = strstr(p, "\"path\":"))) {
        items++;
        p += 7;
    }
    snprintf(app->item_count, sizeof(app->item_count), "items:%u", (unsigned)items);

    char* hash = strstr(app->preview, "\"hash\":\"");
    if(hash) {
        hash += 8;
        snprintf(app->hash_line, sizeof(app->hash_line), "sha %.16s..", hash);
    } else {
        strncpy(app->hash_line, "manifest present", sizeof(app->hash_line) - 1);
    }
}

static void draw_cb(Canvas* canvas, void* ctx) {
    ManifestViewer* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);

    canvas_clear(canvas);
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 2, 9, "CRYPTTOOL");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 90, 9, "v" F69_VER);
    canvas_draw_line(canvas, 0, 11, 127, 11);

    if(app->op_count == 0) {
        canvas_draw_str(canvas, 2, 30, "NO OPERATIONS");
        canvas_draw_str(canvas, 2, 42, "run CASEFILE first");
    } else {
        canvas_draw_str(canvas, 2, 22, app->op_id_short);
        if(app->has_manifest) {
            canvas_draw_str(canvas, 2, 34, app->hash_line);
            canvas_draw_str(canvas, 2, 44, app->item_count);
            canvas_draw_str(canvas, 70, 44, "VERIFIED");
        } else {
            canvas_draw_str(canvas, 2, 34, app->hash_line);
            canvas_draw_str(canvas, 2, 44, "run VERIFY on hub");
        }
        char nav[32];
        snprintf(nav, sizeof(nav), "op %u/%u", (unsigned)(app->op_sel + 1), (unsigned)app->op_count);
        canvas_draw_str(canvas, 2, 54, nav);
    }

    canvas_draw_line(canvas, 0, 56, 127, 56);
    canvas_draw_str(canvas, 2, 63, "<> ops  OK=reload  BACK");

    furi_mutex_release(app->mutex);
}

static void input_cb(InputEvent* event, void* ctx) {
    ManifestViewer* app = ctx;
    if(event->type != InputTypeShort) return;

    furi_mutex_acquire(app->mutex, FuriWaitForever);
    if(event->key == InputKeyBack) {
        app->running = false;
    } else if(event->key == InputKeyLeft && app->op_sel > 0) {
        app->op_sel--;
        mv_load_selected(app);
    } else if(event->key == InputKeyRight && (size_t)(app->op_sel + 1) < app->op_count) {
        app->op_sel++;
        mv_load_selected(app);
    } else if(event->key == InputKeyUp && app->op_sel > 0) {
        app->op_sel--;
        mv_load_selected(app);
    } else if(event->key == InputKeyDown && (size_t)(app->op_sel + 1) < app->op_count) {
        app->op_sel++;
        mv_load_selected(app);
    } else if(event->key == InputKeyOk) {
        mv_list_ops(app);
        mv_load_selected(app);
    }
    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t manifest_viewer_main(void* p) {
    UNUSED(p);

    ManifestViewer* app = malloc(sizeof(ManifestViewer));
    furi_check(app);
    memset(app, 0, sizeof(ManifestViewer));

    app->storage = furi_record_open(RECORD_STORAGE);
    app->running = true;
    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    app->mutex = furi_mutex_alloc(FuriMutexTypeNormal);

    mv_list_ops(app);
    if(app->op_count > 0) {
        app->op_sel = (uint8_t)(app->op_count - 1);
    }
    mv_load_selected(app);

    view_port_draw_callback_set(app->view_port, draw_cb, app);
    view_port_input_callback_set(app->view_port, input_cb, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);

    while(app->running) {
        view_port_update(app->view_port);
        furi_delay_ms(100);
    }

    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_mutex_free(app->mutex);
    furi_record_close(RECORD_GUI);
    furi_record_close(RECORD_STORAGE);
    free(app);
    return 0;
}
