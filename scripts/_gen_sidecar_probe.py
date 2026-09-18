#!/usr/bin/env python3
"""Generate a simple ACTIVE_OP-aware meta sidecar FAP."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEMPLATE = r'''/**
 * FL1PP3R69 v4.0 ARGUS VEIL — __CODENAME__ probe sidecar
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
    snprintf(art, sizeof(art), "%s/artifacts/__DOMAIN__", op_path);
    storage_common_mkdir(storage, art);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char path[288];
    snprintf(
        path,
        sizeof(path),
        "%s/__DOMAIN___%02u%02u%02u.meta.json",
        art,
        (unsigned)dt.hour % 100,
        (unsigned)dt.minute % 100,
        (unsigned)dt.second % 100);
    char body[360];
    snprintf(
        body,
        sizeof(body),
        "{\n"
        "  \"probe\":\"__DOMAIN__\",\n"
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
    canvas_draw_str(canvas, 2, 9, "__CODENAME__");
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 90, 9, "v" F69_VER);
    canvas_draw_line(canvas, 0, 11, 127, 11);
    const char* items[] = {__MENU_ITEMS__};
    for(uint8_t i = 0; i < __N__; i++) {
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
    } else if(event->key == InputKeyDown && app->menu_sel < __N__ - 1) {
        app->menu_sel++;
    } else if(event->key == InputKeyOk) {
        static const char* vals[] = {__VALS__};
        write_sidecar(app, vals[app->menu_sel]);
    }
    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t __ENTRY__(void* p) {
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
'''


def gen(dirname: str, appid: str, codename: str, category: str, domain: str, items: list[tuple[str, str]]):
    d = ROOT / "fap" / dirname
    d.mkdir(parents=True, exist_ok=True)
    entry = f"{dirname}_main"
    fam = f'''App(
    appid="{appid}",
    name="{codename}",
    apptype=FlipperAppType.EXTERNAL,
    entry_point="{entry}",
    requires=["storage", "gui"],
    stack_size=2 * 1024,
    order=30,
    fap_version="4.0",
    fap_description="Fl1pp3r69 {codename} CASEFILE sidecar — metadata into active op",
    fap_author="Fl1pp3r69",
    fap_category="{category}",
)
'''
    (d / "application.fam").write_text(fam, encoding="utf-8")
    menu = ", ".join(f'"{lab}"' for lab, _ in items)
    vals = ", ".join(f'"{v}"' for _, v in items)
    src = (
        TEMPLATE.replace("__CODENAME__", codename[:12])
        .replace("__DOMAIN__", domain)
        .replace("__MENU_ITEMS__", menu)
        .replace("__VALS__", vals)
        .replace("__N__", str(len(items)))
        .replace("__ENTRY__", entry)
    )
    (d / f"{dirname}.c").write_text(src, encoding="utf-8")
    print("generated", d)


def patch_existing():
    # NFC
    p = ROOT / "fap/probe_nfc/probe_nfc.c"
    t = p.read_text(encoding="utf-8")
    t = t.replace('#define F69_VER       "3.0.0"', '#define F69_VER       "4.0.0"')
    t = t.replace('#define F69_VER       "2.0.0"', '#define F69_VER       "4.0.0"')
    start = t.find("static bool probe_latest_op_captures")
    end = t.find("static bool probe_find_latest_nfc", start)
    if start > 0 and end > start:
        new_fn = r'''static bool probe_latest_op_captures(Storage* storage, char* out, size_t out_len) {
    char op_path[192];
    char name[64];
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
                if(len >= sizeof(name)) len = sizeof(name) - 1;
                memcpy(name, s, len);
                name[len] = '\0';
                snprintf(op_path, sizeof(op_path), "%s/%s", F69_OPS_ROOT, name);
                FileInfo info;
                if(storage_common_stat(storage, op_path, &info) == FSE_OK) {
                    snprintf(out, out_len, "%s/captures", op_path);
                    storage_common_mkdir(storage, out);
                    return true;
                }
            }
        }
    } else {
        storage_file_free(file);
    }
    char paths[16][192];
    size_t count = 0;
    File* dir = storage_file_alloc(storage);
    if(storage_dir_open(dir, F69_OPS_ROOT)) {
        char nbuf[64];
        FileInfo info;
        while(storage_dir_read(dir, &info, nbuf, sizeof(nbuf))) {
            if((info.flags & FSF_DIRECTORY) && strncmp(nbuf, "op-", 3) == 0) {
                snprintf(paths[count], 192, "%s/%s", F69_OPS_ROOT, nbuf);
                count++;
                if(count >= 16) break;
            }
        }
        storage_dir_close(dir);
    }
    storage_file_free(dir);
    if(count == 0) return false;
    snprintf(out, out_len, "%s/captures", paths[count - 1]);
    storage_common_mkdir(storage, out);
    return true;
}

'''
        t = t[:start] + new_fn + t[end:]
    p.write_text(t, encoding="utf-8")
    print("patched nfc")

    # SubGHz
    p = ROOT / "fap/probe_subghz/probe_subghz.c"
    t = p.read_text(encoding="utf-8")
    t = t.replace('#define F69_VER      "3.0.0"', '#define F69_VER      "4.0.0"')
    start = t.find("static bool damp_latest_op")
    end = t.find("static bool damp_write_sidecar", start)
    if start > 0 and end > start:
        new_fn = r'''static bool damp_latest_op(Storage* storage, char* op_path, size_t op_len, char* name_out, size_t name_len) {
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
    if(slash && name_out) {
        strncpy(name_out, slash + 1, name_len - 1);
        name_out[name_len - 1] = '\0';
    }
    return true;
}

'''
        t = t[:start] + new_fn + t[end:]
    p.write_text(t, encoding="utf-8")
    print("patched subghz")

    for rel, old, new in [
        ("fap/probe_ir/probe_ir.c", "3.0.0", "4.0.0"),
        ("fap/manifest_viewer/manifest_viewer.c", "3.0.0", "4.0.0"),
    ]:
        p = ROOT / rel
        t = p.read_text(encoding="utf-8")
        t = t.replace(old, new)
        t = t.replace("#define F69_MAX_OPS  16", "#define F69_MAX_OPS  24")
        p.write_text(t, encoding="utf-8")
        print("patched", rel)


def main():
    patch_existing()
    gen(
        "probe_rfid",
        "flipper69_probe_rfid",
        "LODGE",
        "RFID",
        "rfid",
        [("[1] EM4100 meta", "EM4100"), ("[2] HID meta", "HID"), ("[3] Indala meta", "Indala"), ("[4] Generic LF", "generic_lf")],
    )
    gen(
        "probe_ibutton",
        "flipper69_probe_ibutton",
        "BITKEY",
        "iButton",
        "ibutton",
        [("[1] DS1990A", "DS1990A"), ("[2] Cyfral", "Cyfral"), ("[3] Metakom", "Metakom"), ("[4] Generic", "generic")],
    )
    gen(
        "probe_ble",
        "flipper69_probe_ble",
        "HAZE",
        "Bluetooth",
        "ble",
        [("[1] Passive survey", "passive_survey"), ("[2] Adv meta", "advertisement"), ("[3] RSSI log", "rssi_log"), ("[4] Note", "note")],
    )
    gen(
        "probe_gpio",
        "flipper69_probe_gpio",
        "GPIO LAB",
        "GPIO",
        "gpio",
        [("[1] Pin session", "pin_session"), ("[2] Logic claim", "logic_claim"), ("[3] Script log", "script_log"), ("[4] Lab note", "lab_note")],
    )
    gen(
        "probe_badusb",
        "flipper69_probe_badusb",
        "INKWELL",
        "Tools",
        "badusb",
        [("[1] Hash script", "hash_script"), ("[2] Auth gate", "auth_gate"), ("[3] Run log", "run_log"), ("[4] Lab only", "lab_only")],
    )


if __name__ == "__main__":
    main()
