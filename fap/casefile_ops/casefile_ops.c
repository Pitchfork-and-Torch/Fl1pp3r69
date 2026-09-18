/**
 * FL1PP3R69 v4.0 ARGUS VEIL — CASEFILE Ops Hub
 * Manifest-driven field operations + CLAIM harness. Authorized research only.
 * The dolphin grew teeth. The veil still holds. Argus opens every eye.
 */
#include "flipper69_fieldops.h"
#include "flipper69_manifest.h"
#include "flipper69_ops.h"
#include "flipper69_timeline.h"
#include "flipper69_ui.h"

#include <furi.h>
#include <furi_hal_rtc.h>
#include <furi_hal_vibro.h>
#include <gui/gui.h>
#include <storage/storage.h>

#include <stdlib.h>
#include <string.h>

typedef struct {
    Gui* gui;
    ViewPort* view_port;
    FuriMutex* mutex;
    Storage* storage;
    F69Scene scene;
    uint8_t menu_sel;
    uint8_t menu_scroll;
    uint8_t splash_frame;
    uint8_t anim_frame;
    F69OpType type_sel;
    F69PathNum path_sel;
    F69Operation op;
    bool has_op;
    bool running;
    uint8_t panic_step;
    char audit[96];
    char status_msg[48];
    char resume_paths[F69_MAX_OPS][192];
    size_t resume_count;
    uint8_t resume_sel;
} CasefileApp;

static void casefile_draw(Canvas* canvas, void* ctx) {
    CasefileApp* app = ctx;
    furi_mutex_acquire(app->mutex, FuriWaitForever);

    switch(app->scene) {
    case F69SceneSplash:
        f69_ui_draw_splash(canvas, app->splash_frame);
        break;
    case F69SceneMenu:
        f69_ui_draw_menu(canvas, app->menu_sel, app->menu_scroll, app->has_op ? &app->op : NULL);
        break;
    case F69SceneOpType:
        f69_ui_draw_optype(canvas, app->type_sel);
        break;
    case F69ScenePathnum:
        f69_ui_draw_pathnum(canvas, app->path_sel);
        break;
    case F69SceneOpPrep:
        f69_ui_draw_op_prep(canvas, &app->op, app->anim_frame);
        break;
    case F69SceneWorking:
        f69_ui_draw_working(canvas, &app->op, f69_phase_label(app->op.phase), app->anim_frame);
        break;
    case F69SceneAudit:
        f69_ui_draw_audit(canvas, app->audit);
        break;
    case F69SceneExfil:
        f69_ui_draw_exfil(canvas, &app->op, app->anim_frame);
        break;
    case F69ScenePanic:
        f69_ui_draw_panic(canvas, app->anim_frame, app->panic_step);
        break;
    case F69SceneResume:
        f69_ui_draw_resume(canvas, app->resume_paths, app->resume_count, app->resume_sel);
        break;
    case F69SceneStatus:
        f69_ui_draw_status(canvas, app->has_op ? &app->op : NULL, app->status_msg);
        break;
    }

    furi_mutex_release(app->mutex);
}

static void casefile_go_menu(CasefileApp* app) {
    app->scene = F69SceneMenu;
    app->anim_frame = 0;
    app->panic_step = 0;
}

static void casefile_toast(CasefileApp* app, const char* msg) {
    strncpy(app->status_msg, msg, sizeof(app->status_msg) - 1);
    app->status_msg[sizeof(app->status_msg) - 1] = '\0';
    app->scene = F69SceneStatus;
    app->anim_frame = 0;
}

static void casefile_start_new_op(CasefileApp* app) {
    app->type_sel = F69OpUnified;
    app->path_sel = F69PathDs;
    app->scene = F69SceneOpType;
}

static void casefile_commit_new_op(CasefileApp* app) {
    f69_op_create(app->storage, &app->op, app->type_sel, app->path_sel);
    app->has_op = true;
    app->scene = F69SceneOpPrep;
    app->anim_frame = 0;
    furi_hal_vibro_on(true);
    furi_delay_ms(50);
    furi_hal_vibro_on(false);
    furi_delay_ms(40);
    furi_hal_vibro_on(true);
    furi_delay_ms(50);
    furi_hal_vibro_on(false);
}

/* CLAIM: copy newest stock-domain file into active op captures/ + claim meta */
static bool casefile_join3(char* out, size_t out_len, const char* a, const char* b, const char* c) {
    size_t la = strlen(a);
    size_t lb = strlen(b);
    size_t lc = c ? strlen(c) : 0;
    size_t need = la + 1 + lb + (c ? (1 + lc) : 0) + 1;
    if(need > out_len) return false;
    memcpy(out, a, la);
    out[la] = '/';
    memcpy(out + la + 1, b, lb);
    if(c) {
        out[la + 1 + lb] = '/';
        memcpy(out + la + 2 + lb, c, lc);
        out[la + 2 + lb + lc] = '\0';
    } else {
        out[la + 1 + lb] = '\0';
    }
    return true;
}

static bool casefile_claim_from_stock(CasefileApp* app) {
    if(!app->has_op) return false;
    static const char* roots[] = {
        EXT_PATH("subghz"),
        EXT_PATH("nfc"),
        EXT_PATH("infrared"),
        EXT_PATH("lfrfid"),
        EXT_PATH("ibutton"),
    };
    static const char* domains[] = {"subghz", "nfc", "ir", "rfid", "ibutton"};

    char best_src[192] = {0};
    char best_name[48] = {0};
    const char* best_domain = "field";
    uint32_t best_size = 0;

    for(size_t r = 0; r < 5; r++) {
        File* dir = storage_file_alloc(app->storage);
        if(!storage_dir_open(dir, roots[r])) {
            storage_file_free(dir);
            continue;
        }
        char name[48];
        FileInfo info;
        while(storage_dir_read(dir, &info, name, sizeof(name))) {
            if(info.flags & FSF_DIRECTORY) continue;
            if(name[0] == '.') continue;
            if(info.size == 0) continue;
            if(info.size >= best_size) {
                best_size = info.size;
                if(!casefile_join3(best_src, sizeof(best_src), roots[r], name, NULL)) continue;
                strncpy(best_name, name, sizeof(best_name) - 1);
                best_name[sizeof(best_name) - 1] = '\0';
                best_domain = domains[r];
            }
        }
        storage_dir_close(dir);
        storage_file_free(dir);
    }

    if(!best_src[0] || !best_name[0]) return false;

    char cap[192];
    if(!casefile_join3(cap, sizeof(cap), app->op.op_path, "captures", NULL)) return false;
    storage_common_mkdir(app->storage, cap);

    char art_root[192];
    if(!casefile_join3(art_root, sizeof(art_root), app->op.op_path, "artifacts", NULL)) return false;
    storage_common_mkdir(app->storage, art_root);
    char art[192];
    if(!casefile_join3(art, sizeof(art), art_root, best_domain, NULL)) return false;
    storage_common_mkdir(app->storage, art);

    char dest[240];
    if(!casefile_join3(dest, sizeof(dest), art, best_name, NULL)) return false;
    if(storage_common_copy(app->storage, best_src, dest) != FSE_OK) {
        if(!casefile_join3(dest, sizeof(dest), cap, best_name, NULL)) return false;
        if(storage_common_copy(app->storage, best_src, dest) != FSE_OK) return false;
    }

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char meta_name[32];
    snprintf(
        meta_name,
        sizeof(meta_name),
        "claim_%02u%02u%02u.meta.json",
        (unsigned)dt.hour % 100,
        (unsigned)dt.minute % 100,
        (unsigned)dt.second % 100);
    char meta_path[240];
    if(!casefile_join3(meta_path, sizeof(meta_path), cap, meta_name, NULL)) return false;

    char body[320];
    snprintf(
        body,
        sizeof(body),
        "{\n"
        "  \"probe\":\"claim\",\n"
        "  \"ver\":\"%s\",\n"
        "  \"domain\":\"%s\",\n"
        "  \"file\":\"%s\",\n"
        "  \"note\":\"stock claim\",\n"
        "  \"ts\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\"\n"
        "}\n",
        F69_VER,
        best_domain,
        best_name,
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second);
    File* mf = storage_file_alloc(app->storage);
    if(storage_file_open(mf, meta_path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_write(mf, body, strlen(body));
        storage_file_close(mf);
    }
    storage_file_free(mf);

    f69_timeline_append(app->storage, app->op.op_path, "CLAIM", best_name);
    f69_op_refresh_captures(app->storage, &app->op);
    f69_write_checkpoint(app->storage, &app->op, "phase_advance");
    f69_write_active_op(app->storage, &app->op);
    f69_op_save(app->storage, &app->op);
    return true;
}

static void casefile_claim(CasefileApp* app) {
    if(!app->has_op) {
        casefile_toast(app, "no active op");
        return;
    }
    if(casefile_claim_from_stock(app)) {
        char msg[48];
        snprintf(msg, sizeof(msg), "claimed caps:%u", (unsigned)app->op.capture_count);
        casefile_toast(app, msg);
        furi_hal_vibro_on(true);
        furi_delay_ms(60);
        furi_hal_vibro_on(false);
    } else {
        casefile_toast(app, "no stock files");
    }
}

static void casefile_verify(CasefileApp* app) {
    if(!app->has_op) {
        casefile_toast(app, "no active op");
        return;
    }
    app->op.phase = F69PhaseVerify;
    f69_op_refresh_captures(app->storage, &app->op);
    flipper69_write_manifest(
        app->storage, app->op.op_path, app->op.manifest_hash, sizeof(app->op.manifest_hash));
    f69_op_save(app->storage, &app->op);
    f69_timeline_append(app->storage, app->op.op_path, "VERIFY", app->op.manifest_hash);
    furi_hal_vibro_on(true);
    furi_delay_ms(90);
    furi_hal_vibro_on(false);

    char msg[48];
    snprintf(msg, sizeof(msg), "OK %.8s.. caps:%u", app->op.manifest_hash, (unsigned)app->op.capture_count);
    casefile_toast(app, msg);
}

static void casefile_auto_run(CasefileApp* app) {
    if(!app->has_op) {
        casefile_toast(app, "no active op");
        return;
    }
    if(app->op.phase == F69PhaseClose) {
        casefile_toast(app, "op already closed");
        return;
    }
    app->scene = F69SceneWorking;
    app->anim_frame = 0;
    view_port_update(app->view_port);
    f69_op_run_auto(app->storage, &app->op);
    app->scene = F69SceneExfil;
    app->anim_frame = 0;
}

static void casefile_toggle_opsec(CasefileApp* app) {
    if(!app->has_op) {
        casefile_toast(app, "no active op");
        return;
    }
    app->op.opsec = !app->op.opsec;
    f69_op_save(app->storage, &app->op);
    f69_timeline_append(
        app->storage, app->op.op_path, "OPSEC", app->op.opsec ? "engaged" : "relaxed");
    casefile_toast(app, app->op.opsec ? "OPSEC ENGAGED" : "OPSEC RELAXED");
    furi_hal_vibro_on(true);
    furi_delay_ms(40);
    furi_hal_vibro_on(false);
}

static void casefile_input(InputEvent* event, void* ctx) {
    CasefileApp* app = ctx;
    if(event->type != InputTypeShort && event->type != InputTypeLong) return;

    furi_mutex_acquire(app->mutex, FuriWaitForever);

    if(event->type == InputTypeShort && event->key == InputKeyBack) {
        if(app->scene == F69SceneMenu) {
            app->running = false;
        } else if(app->scene == F69ScenePanic && app->panic_step > 0) {
            app->panic_step = 0;
        } else {
            casefile_go_menu(app);
        }
        furi_mutex_release(app->mutex);
        view_port_update(app->view_port);
        return;
    }

    /* long Left = quick status */
    if(event->type == InputTypeLong && event->key == InputKeyLeft && app->scene == F69SceneMenu) {
        if(app->has_op) {
            f69_op_refresh_captures(app->storage, &app->op);
            casefile_toast(app, "live status");
        } else {
            casefile_toast(app, "no active op");
        }
        furi_mutex_release(app->mutex);
        view_port_update(app->view_port);
        return;
    }

    switch(app->scene) {
    case F69SceneMenu:
        if(event->type == InputTypeShort) {
            if(event->key == InputKeyUp && app->menu_sel > 0) {
                app->menu_sel--;
                if(app->menu_sel < app->menu_scroll) app->menu_scroll = app->menu_sel;
            } else if(event->key == InputKeyDown && app->menu_sel < 8) {
                app->menu_sel++;
                if(app->menu_sel >= app->menu_scroll + 4) app->menu_scroll = app->menu_sel - 3;
            } else if(event->key == InputKeyOk) {
                switch(app->menu_sel) {
                case 0:
                    casefile_start_new_op(app);
                    break;
                case 1:
                    f69_list_ops(app->storage, app->resume_paths, &app->resume_count);
                    app->resume_sel = 0;
                    app->scene = F69SceneResume;
                    break;
                case 2:
                    casefile_claim(app);
                    break;
                case 3:
                    casefile_verify(app);
                    break;
                case 4:
                    if(app->has_op) {
                        app->op.phase = F69PhaseExfil;
                        f69_op_save(app->storage, &app->op);
                        f69_timeline_append(app->storage, app->op.op_path, "EXFIL", "ready");
                        app->scene = F69SceneExfil;
                        app->anim_frame = 0;
                    } else {
                        casefile_toast(app, "no active op");
                    }
                    break;
                case 5:
                    casefile_auto_run(app);
                    break;
                case 6:
                    f69_audit_ops(app->storage, app->audit, sizeof(app->audit));
                    app->scene = F69SceneAudit;
                    break;
                case 7:
                    casefile_toggle_opsec(app);
                    break;
                case 8:
                    app->scene = F69ScenePanic;
                    app->panic_step = 0;
                    app->anim_frame = 0;
                    break;
                }
            } else if(event->key == InputKeyRight && app->has_op) {
                f69_op_refresh_captures(app->storage, &app->op);
                casefile_toast(app, "live status");
            }
        }
        break;

    case F69SceneOpType:
        if(event->type == InputTypeShort) {
            if(event->key == InputKeyUp && app->type_sel > F69OpProximity) {
                app->type_sel = (F69OpType)(app->type_sel - 1);
            }
            if(event->key == InputKeyDown && app->type_sel < F69OpUnified) {
                app->type_sel = (F69OpType)(app->type_sel + 1);
            }
            if(event->key == InputKeyOk) {
                app->scene = F69ScenePathnum;
            }
        }
        break;

    case F69ScenePathnum:
        if(event->type == InputTypeShort) {
            if(event->key == InputKeyUp && app->path_sel > F69PathImps) app->path_sel--;
            if(event->key == InputKeyDown && app->path_sel < F69PathEmerg) app->path_sel++;
            if(event->key == InputKeyOk) casefile_commit_new_op(app);
        }
        break;

    case F69SceneOpPrep:
        if(event->type == InputTypeShort && event->key == InputKeyOk) casefile_go_menu(app);
        break;

    case F69SceneAudit:
    case F69SceneStatus:
        if(event->type == InputTypeShort && event->key == InputKeyOk) casefile_go_menu(app);
        break;

    case F69SceneExfil:
        if(event->type == InputTypeShort && event->key == InputKeyOk) {
            f69_op_close(app->storage, &app->op);
            furi_hal_vibro_on(true);
            furi_delay_ms(70);
            furi_hal_vibro_on(false);
            casefile_toast(app, "OP SEALED // CLOSE");
        }
        break;

    case F69ScenePanic:
        if(event->type == InputTypeShort && event->key == InputKeyOk) {
            if(app->panic_step == 0) {
                app->panic_step = 1;
                app->anim_frame = 0;
            } else {
                f69_panic_wipe(app->storage);
                app->has_op = false;
                memset(&app->op, 0, sizeof(app->op));
                app->panic_step = 0;
                furi_hal_vibro_on(true);
                furi_delay_ms(180);
                furi_hal_vibro_on(false);
                casefile_toast(app, "ALL OPS ZEROED");
            }
        }
        break;

    case F69SceneResume:
        if(event->type == InputTypeShort) {
            if(event->key == InputKeyUp && app->resume_sel > 0) app->resume_sel--;
            if(event->key == InputKeyDown && (size_t)(app->resume_sel + 1) < app->resume_count)
                app->resume_sel++;
            if(event->key == InputKeyOk && app->resume_count > 0) {
                if(f69_op_load(app->storage, &app->op, app->resume_paths[app->resume_sel])) {
                    app->has_op = true;
                    casefile_toast(app, "OP LOADED");
                } else {
                    casefile_toast(app, "load failed");
                }
            }
        }
        break;
    default:
        break;
    }

    furi_mutex_release(app->mutex);
    view_port_update(app->view_port);
}

int32_t casefile_ops_main(void* p) {
    UNUSED(p);

    CasefileApp* app = malloc(sizeof(CasefileApp));
    furi_check(app);
    memset(app, 0, sizeof(CasefileApp));

    app->storage = furi_record_open(RECORD_STORAGE);
    f69_ensure_roots(app->storage);
    f69_update_index(app->storage);
    /* v3 recovery: resume ACTIVE_OP if present and not closed */
    if(f69_try_resume_active(app->storage, &app->op)) {
        app->has_op = true;
    }

    app->gui = furi_record_open(RECORD_GUI);
    app->view_port = view_port_alloc();
    app->mutex = furi_mutex_alloc(FuriMutexTypeNormal);
    app->running = true;
    app->scene = F69SceneSplash;
    app->type_sel = F69OpUnified;
    app->path_sel = F69PathDs;

    view_port_draw_callback_set(app->view_port, casefile_draw, app);
    view_port_input_callback_set(app->view_port, casefile_input, app);
    gui_add_view_port(app->gui, app->view_port, GuiLayerFullscreen);

    while(app->running) {
        furi_mutex_acquire(app->mutex, FuriWaitForever);
        if(app->scene == F69SceneSplash) {
            app->splash_frame++;
            if(app->splash_frame > 22) {
                app->scene = F69SceneMenu;
            }
        } else if(app->scene == F69SceneOpPrep) {
            app->anim_frame++;
            if(app->anim_frame > 14) {
                app->scene = F69SceneMenu;
            }
        } else if(
            app->scene == F69ScenePanic || app->scene == F69SceneExfil ||
            app->scene == F69SceneWorking) {
            app->anim_frame++;
        } else if(app->scene == F69SceneStatus) {
            app->anim_frame++;
            if(app->anim_frame > 20) {
                casefile_go_menu(app);
            }
        }
        furi_mutex_release(app->mutex);

        view_port_update(app->view_port);
        furi_delay_ms(70);
    }

    gui_remove_view_port(app->gui, app->view_port);
    view_port_free(app->view_port);
    furi_mutex_free(app->mutex);
    furi_record_close(RECORD_GUI);
    furi_record_close(RECORD_STORAGE);
    free(app);
    return 0;
}
