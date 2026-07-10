#include "flipper69_ui.h"
#include "flipper69_fieldops.h"

#include <stdio.h>
#include <string.h>

#define MENU_VISIBLE 4
#define MENU_COUNT   8

static const char* menu_labels[] = {
    "[1] NEW OPERATION",
    "[2] RESUME OPERATION",
    "[3] RUN PHASE (auto)",
    "[4] VERIFY MANIFEST",
    "[5] EXFIL TO DESKTOP",
    "[6] AUDIT / ORPHAN SCAN",
    "[7] OPSEC TOGGLE",
    "[8] PANIC WIPE",
};

static void f69_ui_header(Canvas* canvas, const char* title) {
    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 2, 9, title);
    canvas_draw_line(canvas, 0, 11, 127, 11);
}

static void f69_ui_phase_strip(Canvas* canvas, F69Phase phase, int y) {
    static const char* marks[] = {"I", "P", "B", "C", "V", "E", "X"};
    int x = 2;
    for(uint8_t i = 0; i < 7; i++) {
        bool active = ((F69Phase)i == phase);
        bool done = ((F69Phase)i < phase);
        if(active) {
            canvas_draw_box(canvas, x, y - 7, 15, 9);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_str(canvas, x + 4, y, marks[i]);
            canvas_set_color(canvas, ColorBlack);
        } else if(done) {
            canvas_draw_frame(canvas, x, y - 7, 15, 9);
            canvas_draw_str(canvas, x + 4, y, marks[i]);
            canvas_draw_dot(canvas, x + 12, y - 5);
        } else {
            canvas_draw_str(canvas, x + 4, y, marks[i]);
        }
        x += 18;
    }
}

static void f69_ui_footer_op(Canvas* canvas, const F69Operation* op) {
    canvas_draw_line(canvas, 0, 52, 127, 52);
    canvas_set_font(canvas, FontSecondary);
    if(op && op->op_id[0]) {
        char left[56];
        char code[24];
        strncpy(code, op->codename, sizeof(code) - 1);
        code[sizeof(code) - 1] = '\0';
        snprintf(left, sizeof(left), "%.20s %s", code, f69_phase_short(op->phase));
        canvas_draw_str(canvas, 2, 61, left);
        if(op->opsec) {
            canvas_draw_str(canvas, 92, 61, "OPSEC");
        } else {
            canvas_draw_str(canvas, 98, 61, "OPEN");
        }
    } else {
        canvas_draw_str(canvas, 2, 61, "NO ACTIVE OPERATION");
    }
}

void f69_ui_draw_splash(Canvas* canvas, uint8_t frame) {
    canvas_clear(canvas);

    if(frame < 4) {
        for(int i = 0; i < 48; i++) {
            int x = (frame * 23 + i * 5) % 128;
            int y = (i * 11 + frame * 3) % 64;
            canvas_draw_dot(canvas, x, y);
            if((i + frame) % 3 == 0) canvas_draw_dot(canvas, (x + 1) % 128, y);
        }
        return;
    }

    if(frame == 5 || frame == 9) {
        for(int y = 0; y < 64; y += 2) {
            canvas_draw_line(canvas, 0, y, 127, y);
        }
        return;
    }

    canvas_set_font(canvas, FontPrimary);
    int slide = frame < 10 ? (int)(frame - 4) * 8 - 40 : 4;
    if(slide > 4) slide = 4;
    canvas_draw_str(canvas, slide, 18, "FL1PP3R");

    canvas_set_font(canvas, FontBigNumbers);
    canvas_draw_str(canvas, 78, 24, "69");

    canvas_draw_line(canvas, 4, 28, 124, 28);

    canvas_set_font(canvas, FontSecondary);
    if(frame > 10) {
        canvas_draw_str(canvas, 2, 40, F69_CLASSIFICATION);
    }
    if(frame > 13) {
        canvas_draw_str(canvas, 2, 50, "VER=" F69_VER "  CASEFILE OPS");
    }
    if(frame > 16) {
        if((frame / 2) % 2 == 0) {
            canvas_draw_str(canvas, 2, 62, "the dolphin grew teeth");
        }
    }

    /* mini viper eye */
    if(frame > 12) {
        canvas_draw_frame(canvas, 118, 4, 8, 6);
        canvas_draw_line(canvas, 120, 7, 124, 7);
    }
}

void f69_ui_draw_menu(Canvas* canvas, uint8_t selected, uint8_t scroll, const F69Operation* op) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "CASEFILE OPS");

    canvas_set_font(canvas, FontSecondary);
    char ver[16];
    snprintf(ver, sizeof(ver), "v%s", F69_VER);
    canvas_draw_str(canvas, 100, 9, ver);

    for(uint8_t row = 0; row < MENU_VISIBLE; row++) {
        uint8_t idx = scroll + row;
        if(idx >= MENU_COUNT) break;
        int y = 22 + (row * 10);
        if(idx == selected) {
            canvas_draw_box(canvas, 0, y - 8, 128, 10);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_str(canvas, 2, y, menu_labels[idx]);
            canvas_set_color(canvas, ColorBlack);
        } else {
            canvas_draw_str(canvas, 2, y, menu_labels[idx]);
        }
    }

    /* scroll hint */
    if(scroll > 0) canvas_draw_str(canvas, 122, 14, "^");
    if(scroll + MENU_VISIBLE < MENU_COUNT) canvas_draw_str(canvas, 122, 50, "v");

    f69_ui_footer_op(canvas, op);
}

void f69_ui_draw_optype(Canvas* canvas, F69OpType selected) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "SELECT OP TYPE");
    canvas_set_font(canvas, FontSecondary);

    for(uint8_t i = 0; i < 5; i++) {
        F69OpType t = (F69OpType)i;
        int y = 20 + (i * 8);
        char line[36];
        snprintf(line, sizeof(line), "[%u] %s", i + 1, f69_optype_label(t));
        if(t == selected) {
            canvas_draw_box(canvas, 0, y - 7, 128, 9);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_str(canvas, 2, y, line);
            canvas_set_color(canvas, ColorBlack);
        } else {
            canvas_draw_str(canvas, 2, y, line);
        }
    }
    canvas_draw_str(canvas, 2, 62, f69_optype_hint(selected));
}

void f69_ui_draw_pathnum(Canvas* canvas, F69PathNum selected) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "SELECT PATHNUM");
    canvas_set_font(canvas, FontSecondary);

    for(uint8_t i = 1; i <= 5; i++) {
        int y = 18 + (i * 8);
        char line[32];
        snprintf(line, sizeof(line), "[%u] %s", i, f69_pathnum_label((F69PathNum)i));
        if((F69PathNum)i == selected) {
            canvas_draw_box(canvas, 0, y - 7, 128, 9);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_str(canvas, 2, y, line);
            canvas_set_color(canvas, ColorBlack);
        } else {
            canvas_draw_str(canvas, 2, y, line);
        }
    }
    canvas_draw_str(canvas, 2, 62, f69_pathnum_hint(selected));
}

void f69_ui_draw_op_prep(Canvas* canvas, const F69Operation* op, uint8_t frame) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "OP_PREP");
    canvas_set_font(canvas, FontSecondary);

    canvas_draw_str(canvas, 2, 22, op->codename);
    canvas_draw_str(canvas, 2, 32, f69_optype_label(op->op_type));

    char path[28];
    snprintf(path, sizeof(path), "PATH:%s", f69_pathnum_label(op->pathnum));
    canvas_draw_str(canvas, 2, 42, path);

    f69_ui_phase_strip(canvas, op->phase, 52);

    if((frame / 3) % 2 == 0) {
        canvas_draw_str(canvas, 2, 62, "SEALING // OPSEC ON");
    } else {
        canvas_draw_str(canvas, 2, 62, "MANIFEST READY");
    }
}

void f69_ui_draw_working(Canvas* canvas, const F69Operation* op, const char* status, uint8_t frame) {
    canvas_clear(canvas);
    f69_ui_header(canvas, f69_phase_label(op->phase));
    canvas_set_font(canvas, FontSecondary);
    canvas_draw_str(canvas, 2, 22, op->codename);
    canvas_draw_str(canvas, 2, 32, status ? status : "...");

    f69_ui_phase_strip(canvas, op->phase, 46);

    /* spinner */
    static const char* spin = "|/-\\";
    char s[4];
    s[0] = spin[(frame / 2) % 4];
    s[1] = '\0';
    canvas_draw_str(canvas, 118, 22, s);
    canvas_draw_str(canvas, 2, 62, "HOLD BACK TO ABORT");
}

void f69_ui_draw_audit(Canvas* canvas, const char* report) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "AUDIT SCAN");
    canvas_set_font(canvas, FontSecondary);

    if(report) {
        /* multi-line report (\\n separated) */
        char buf[96];
        strncpy(buf, report, sizeof(buf) - 1);
        buf[sizeof(buf) - 1] = '\0';
        int y = 24;
        char* line = buf;
        while(line && y < 54) {
            char* nl = strchr(line, '\n');
            if(nl) *nl = '\0';
            canvas_draw_str(canvas, 2, y, line);
            y += 10;
            line = nl ? nl + 1 : NULL;
        }
    } else {
        canvas_draw_str(canvas, 2, 28, "CLEAN");
    }
    canvas_draw_str(canvas, 2, 62, "OK=return");
}

void f69_ui_draw_exfil(Canvas* canvas, const F69Operation* op, uint8_t frame) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "EXFIL READY");
    canvas_set_font(canvas, FontSecondary);

    canvas_draw_str(canvas, 2, 22, "1. USB to PC");
    canvas_draw_str(canvas, 2, 32, "2. flipper69-sync.ps1");

    if(op->manifest_hash[0]) {
        char hash[24];
        snprintf(hash, sizeof(hash), "SHA %.12s..", op->manifest_hash);
        canvas_draw_str(canvas, 2, 44, hash);
    } else {
        canvas_draw_str(canvas, 2, 44, "hash: run VERIFY first");
    }

    if((frame / 4) % 2 == 0) {
        canvas_draw_str(canvas, 2, 62, "OK=SEAL CLOSE  BACK=menu");
    } else {
        canvas_draw_str(canvas, 2, 62, "waiting for desktop...");
    }
}

void f69_ui_draw_panic(Canvas* canvas, uint8_t frame, uint8_t confirm_step) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "PANIC WIPE");
    canvas_set_font(canvas, FontSecondary);

    if(confirm_step == 0) {
        canvas_draw_str(canvas, 2, 24, "ZEROES ALL OPS");
        canvas_draw_str(canvas, 2, 34, "metadata only");
        canvas_draw_str(canvas, 2, 44, "firmware untouched");
        if((frame / 3) % 2 == 0) {
            canvas_draw_str(canvas, 2, 62, "OK=ARM  BACK=cancel");
        }
    } else {
        canvas_draw_box(canvas, 0, 14, 128, 36);
        canvas_set_color(canvas, ColorWhite);
        canvas_draw_str(canvas, 8, 28, "CONFIRM DESTRUCT");
        canvas_draw_str(canvas, 8, 40, "OK=WIPE NOW");
        canvas_set_color(canvas, ColorBlack);
        if((frame / 2) % 2 == 0) {
            canvas_draw_str(canvas, 2, 62, "BACK=abort wipe");
        }
    }
}

void f69_ui_draw_resume(Canvas* canvas, char paths[][192], size_t count, uint8_t selected) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "RESUME OP");
    canvas_set_font(canvas, FontSecondary);

    if(count == 0) {
        canvas_draw_str(canvas, 2, 30, "NO OPERATIONS");
        canvas_draw_str(canvas, 2, 62, "BACK=menu");
        return;
    }

    size_t start = 0;
    if(selected >= 4) start = selected - 3;

    for(size_t i = 0; i < 4; i++) {
        size_t idx = start + i;
        if(idx >= count) break;
        const char* slash = strrchr(paths[idx], '/');
        const char* name = slash ? slash + 1 : paths[idx];
        int y = 22 + (int)(i * 10);

        char short_name[28];
        /* show codename-ish tail if long */
        if(strlen(name) > 24) {
            snprintf(short_name, sizeof(short_name), "..%.22s", name + strlen(name) - 22);
        } else {
            strncpy(short_name, name, sizeof(short_name) - 1);
            short_name[sizeof(short_name) - 1] = '\0';
        }

        if(idx == selected) {
            canvas_draw_box(canvas, 0, y - 8, 128, 10);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_str(canvas, 2, y, short_name);
            canvas_set_color(canvas, ColorBlack);
        } else {
            canvas_draw_str(canvas, 2, y, short_name);
        }
    }
    canvas_draw_str(canvas, 2, 62, "OK=load BACK=menu");
}

void f69_ui_draw_status(Canvas* canvas, const F69Operation* op, const char* msg) {
    canvas_clear(canvas);
    f69_ui_header(canvas, "STATUS");
    canvas_set_font(canvas, FontSecondary);

    if(op && op->op_id[0]) {
        canvas_draw_str(canvas, 2, 22, op->codename);
        char line[40];
        snprintf(line, sizeof(line), "%s // %s", f69_optype_label(op->op_type), f69_phase_label(op->phase));
        canvas_draw_str(canvas, 2, 32, line);
        snprintf(line, sizeof(line), "caps:%u  %s", (unsigned)op->capture_count, op->opsec ? "OPSEC" : "OPEN");
        canvas_draw_str(canvas, 2, 42, line);
        f69_ui_phase_strip(canvas, op->phase, 52);
    }

    if(msg && msg[0]) {
        canvas_draw_str(canvas, 2, 62, msg);
    } else {
        canvas_draw_str(canvas, 2, 62, "OK=return");
    }
}
