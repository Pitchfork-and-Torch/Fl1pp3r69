#pragma once

#include "flipper69_ops.h"

#include <gui/canvas.h>

typedef enum {
    F69SceneSplash,
    F69SceneMenu,
    F69SceneOpType,
    F69ScenePathnum,
    F69SceneOpPrep,
    F69SceneWorking,
    F69SceneAudit,
    F69SceneExfil,
    F69ScenePanic,
    F69SceneResume,
    F69SceneStatus,
} F69Scene;

void f69_ui_draw_splash(Canvas* canvas, uint8_t frame);
void f69_ui_draw_menu(Canvas* canvas, uint8_t selected, uint8_t scroll, const F69Operation* op);
void f69_ui_draw_optype(Canvas* canvas, F69OpType selected);
void f69_ui_draw_pathnum(Canvas* canvas, F69PathNum selected);
void f69_ui_draw_op_prep(Canvas* canvas, const F69Operation* op, uint8_t frame);
void f69_ui_draw_working(Canvas* canvas, const F69Operation* op, const char* status, uint8_t frame);
void f69_ui_draw_audit(Canvas* canvas, const char* report);
void f69_ui_draw_exfil(Canvas* canvas, const F69Operation* op, uint8_t frame);
void f69_ui_draw_panic(Canvas* canvas, uint8_t frame, uint8_t confirm_step);
void f69_ui_draw_resume(Canvas* canvas, char paths[][192], size_t count, uint8_t selected);
void f69_ui_draw_status(Canvas* canvas, const F69Operation* op, const char* msg);
