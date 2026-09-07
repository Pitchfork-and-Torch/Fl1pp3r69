#include "flipper69_timeline.h"
#include "flipper69_fieldops.h"

#include <furi_hal_rtc.h>

#include <stdio.h>
#include <string.h>

bool f69_timeline_append(Storage* storage, const char* op_path, const char* event, const char* detail) {
    char path[256];
    snprintf(path, sizeof(path), "%s/TIMELINE.jsonl", op_path);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);
    char ts[32];
    snprintf(
        ts,
        sizeof(ts),
        "%04d-%02d-%02dT%02d:%02d:%02dZ",
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second);

    char line[384];
    if(detail && detail[0]) {
        snprintf(
            line,
            sizeof(line),
            "{\"ts\":\"%s\",\"ver\":\"%s\",\"event\":\"%s\",\"detail\":\"%s\"}\n",
            ts,
            F69_VER,
            event,
            detail);
    } else {
        snprintf(
            line,
            sizeof(line),
            "{\"ts\":\"%s\",\"ver\":\"%s\",\"event\":\"%s\"}\n",
            ts,
            F69_VER,
            event);
    }

    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, path, FSAM_WRITE, FSOM_OPEN_APPEND)) {
        storage_file_free(file);
        return false;
    }
    storage_file_write(file, line, strlen(line));
    storage_file_close(file);
    storage_file_free(file);
    return true;
}