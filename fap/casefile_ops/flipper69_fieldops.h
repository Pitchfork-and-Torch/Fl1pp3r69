#pragma once

#include <stddef.h>
#include <stdint.h>

#define F69_VER "4.0.0"
#define F69_CODENAME "FL1PP3R69"
#define F69_RELEASE "ARGUS VEIL"
#define F69_CLASSIFICATION "UNCLASSIFIED//FRI"
#define F69_TAGLINE "the dolphin grew teeth"
#define F69_TAGLINE_V3 "veil holds · argus opens every eye"
#define F69_TAGLINE_V4 "argus opens every eye"

/* PATHNUM speed profiles: imps / ds / slow / fast / emerg */
typedef enum {
    F69PathImps = 1,
    F69PathDs = 2,
    F69PathSlow = 3,
    F69PathFast = 4,
    F69PathEmerg = 5,
} F69PathNum;

typedef enum {
    F69PhaseIntake,
    F69PhaseOpPrep,
    F69PhaseProbe,
    F69PhaseCapture,
    F69PhaseVerify,
    F69PhaseExfil,
    F69PhaseClose,
} F69Phase;

typedef enum {
    F69OpProximity,
    F69OpSurvey,
    F69OpReplay,
    F69OpInject,
    F69OpUnified,
} F69OpType;

const char* f69_pathnum_label(F69PathNum path);
const char* f69_pathnum_hint(F69PathNum path);
const char* f69_phase_label(F69Phase phase);
const char* f69_phase_short(F69Phase phase);
const char* f69_optype_label(F69OpType type);
const char* f69_optype_hint(F69OpType type);

void f69_generate_codename(char* out, size_t out_len);
void f69_generate_op_id(char* out, size_t out_len, const char* codename);
void f69_generate_workspace(char* out, size_t out_len);
