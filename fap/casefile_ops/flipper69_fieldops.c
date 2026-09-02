#include "flipper69_fieldops.h"

#include <furi.h>
#include <furi_hal_random.h>
#include <furi_hal_rtc.h>

#include <stdio.h>

static const char* const f69_tools[] = {
    "charm",
    "dewdrop",
    "watcher",
    "curses",
    "dampcrowd",
    "crypttool",
    "viper",
    "ghost",
    "razor",
    "spectre",
    "obsidian",
    "phosphor",
};
static const char* const f69_animals[] = {
    "penguin",
    "hammer",
    "vortex",
    "hydrant",
    "fiesta",
    "coil",
    "needle",
    "mirror",
    "torch",
    "pitchfork",
    "serpent",
    "falcon",
};

const char* f69_pathnum_label(F69PathNum path) {
    switch(path) {
    case F69PathImps:
        return "imps";
    case F69PathDs:
        return "ds";
    case F69PathSlow:
        return "slow";
    case F69PathFast:
        return "fast";
    case F69PathEmerg:
        return "emerg";
    default:
        return "ds";
    }
}

const char* f69_pathnum_hint(F69PathNum path) {
    switch(path) {
    case F69PathImps:
        return "stealth / quiet";
    case F69PathDs:
        return "default standard";
    case F69PathSlow:
        return "deliberate pace";
    case F69PathFast:
        return "rapid advance";
    case F69PathEmerg:
        return "emergency sprint";
    default:
        return "default";
    }
}

const char* f69_phase_label(F69Phase phase) {
    switch(phase) {
    case F69PhaseIntake:
        return "INTAKE";
    case F69PhaseOpPrep:
        return "OP_PREP";
    case F69PhaseProbe:
        return "PROBE";
    case F69PhaseCapture:
        return "CAPTURE";
    case F69PhaseVerify:
        return "VERIFY";
    case F69PhaseExfil:
        return "EXFIL";
    case F69PhaseClose:
        return "CLOSE";
    default:
        return "UNKNOWN";
    }
}

const char* f69_phase_short(F69Phase phase) {
    switch(phase) {
    case F69PhaseIntake:
        return "IN";
    case F69PhaseOpPrep:
        return "PR";
    case F69PhaseProbe:
        return "PB";
    case F69PhaseCapture:
        return "CP";
    case F69PhaseVerify:
        return "VF";
    case F69PhaseExfil:
        return "EX";
    case F69PhaseClose:
        return "CL";
    default:
        return "??";
    }
}

const char* f69_optype_label(F69OpType type) {
    switch(type) {
    case F69OpProximity:
        return "proximity";
    case F69OpSurvey:
        return "survey";
    case F69OpReplay:
        return "replay";
    case F69OpInject:
        return "inject";
    case F69OpUnified:
        return "unified";
    default:
        return "unified";
    }
}

const char* f69_optype_hint(F69OpType type) {
    switch(type) {
    case F69OpProximity:
        return "single-target RF/NFC";
    case F69OpSurvey:
        return "passive sweep";
    case F69OpReplay:
        return "auth replay test";
    case F69OpInject:
        return "lab inject only";
    case F69OpUnified:
        return "full pipeline";
    default:
        return "full pipeline";
    }
}

void f69_generate_codename(char* out, size_t out_len) {
    uint32_t t = furi_hal_random_get();
    uint32_t a = furi_hal_random_get();
    snprintf(
        out,
        out_len,
        "%s_%s",
        f69_tools[t % (sizeof(f69_tools) / sizeof(f69_tools[0]))],
        f69_animals[a % (sizeof(f69_animals) / sizeof(f69_animals[0]))]);
}

void f69_generate_op_id(char* out, size_t out_len, const char* codename) {
    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    uint32_t salt = furi_hal_random_get();
    snprintf(
        out,
        out_len,
        "op-%04d%02d%02d-%s-%08lx",
        dt.year,
        dt.month,
        dt.day,
        codename,
        (unsigned long)(salt & 0xffffffff));
}

void f69_generate_workspace(char* out, size_t out_len) {
    uint32_t r = furi_hal_random_get();
    snprintf(out, out_len, ".f69_%08lx", (unsigned long)(r & 0xffffffff));
}
