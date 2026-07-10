#include "flipper69_ops.h"
#include "flipper69_manifest.h"
#include "flipper69_timeline.h"

#include <furi_hal_rtc.h>
#include <furi_hal_vibro.h>

#include <stdio.h>
#include <string.h>

static bool f69_write_operation_json(Storage* storage, const F69Operation* op) {
    char path[256];
    snprintf(path, sizeof(path), "%s/OPERATION.json", op->op_path);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);

    char hash_field[80];
    if(op->manifest_hash[0]) {
        snprintf(hash_field, sizeof(hash_field), "\"%s\"", op->manifest_hash);
    } else {
        snprintf(hash_field, sizeof(hash_field), "null");
    }

    char body[900];
    snprintf(
        body,
        sizeof(body),
        "{\n"
        "  \"opId\":\"%s\",\n"
        "  \"codename\":\"%s\",\n"
        "  \"workspace\":\"%s\",\n"
        "  \"opType\":\"%s\",\n"
        "  \"pathnum\":%u,\n"
        "  \"pathLabel\":\"%s\",\n"
        "  \"phase\":\"%s\",\n"
        "  \"openedAt\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\",\n"
        "  \"device\":{\"firmware\":\"flipper69\",\"version\":\"%s\",\"codename\":\"%s\"},\n"
        "  \"permissions\":{\"opsec\":%s,\"authorized\":%s},\n"
        "  \"captureCount\":%u,\n"
        "  \"manifestHash\":%s\n"
        "}\n",
        op->op_id,
        op->codename,
        op->workspace,
        f69_optype_label(op->op_type),
        (unsigned)op->pathnum,
        f69_pathnum_label(op->pathnum),
        f69_phase_label(op->phase),
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second,
        F69_VER,
        F69_CODENAME,
        op->opsec ? "true" : "false",
        op->authorized ? "true" : "false",
        (unsigned)op->capture_count,
        hash_field);

    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_free(file);
        return false;
    }
    storage_file_write(file, body, strlen(body));
    storage_file_close(file);
    storage_file_free(file);
    return true;
}

static bool f69_parse_field(const char* json, const char* key, char* out, size_t out_len) {
    char needle[48];
    snprintf(needle, sizeof(needle), "\"%s\":\"", key);
    const char* start = strstr(json, needle);
    if(!start) return false;
    start += strlen(needle);
    const char* end = strchr(start, '"');
    if(!end) return false;
    size_t len = (size_t)(end - start);
    if(len >= out_len) len = out_len - 1;
    memcpy(out, start, len);
    out[len] = '\0';
    return true;
}

static bool f69_create_scaffold(Storage* storage, const F69Operation* op) {
    char dir[256];
    snprintf(dir, sizeof(dir), "%s/captures", op->op_path);
    storage_common_mkdir(storage, dir);

    char notes[256];
    snprintf(notes, sizeof(notes), "%s/notes.txt", op->op_path);
    char note_body[160];
    snprintf(
        note_body,
        sizeof(note_body),
        "# %s\n# %s // %s\n# path: %s\n",
        op->codename,
        F69_CODENAME,
        F69_VER,
        f69_pathnum_label(op->pathnum));

    File* file = storage_file_alloc(storage);
    if(storage_file_open(file, notes, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_write(file, note_body, strlen(note_body));
        storage_file_close(file);
    }
    storage_file_free(file);

    char marker[256];
    snprintf(marker, sizeof(marker), "%s/captures/.%s.ready", op->op_path, op->workspace);
    char content[128];
    snprintf(
        content,
        sizeof(content),
        "F69/%s/%s/%s\n",
        F69_VER,
        op->codename,
        f69_pathnum_label(op->pathnum));

    file = storage_file_alloc(storage);
    if(!storage_file_open(file, marker, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_free(file);
        return false;
    }
    storage_file_write(file, content, strlen(content));
    storage_file_close(file);
    storage_file_free(file);
    return true;
}

bool f69_ensure_roots(Storage* storage) {
    storage_common_mkdir(storage, F69_ROOT);
    storage_common_mkdir(storage, F69_OPS_ROOT);
    return true;
}

bool f69_update_index(Storage* storage) {
    char paths[F69_MAX_OPS][192];
    size_t count = 0;
    f69_list_ops(storage, paths, &count);

    char path[192];
    snprintf(path, sizeof(path), "%s/index.json", F69_ROOT);

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);

    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_free(file);
        return false;
    }

    char header[160];
    snprintf(
        header,
        sizeof(header),
        "{\n  \"firmware\":\"flipper69\",\n  \"version\":\"%s\",\n  \"updatedAt\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\",\n  \"operations\":[\n",
        F69_VER,
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second);
    storage_file_write(file, header, strlen(header));

    for(size_t i = 0; i < count; i++) {
        const char* slash = strrchr(paths[i], '/');
        const char* name = slash ? slash + 1 : paths[i];
        char short_name[64];
        strncpy(short_name, name, sizeof(short_name) - 1);
        short_name[sizeof(short_name) - 1] = '\0';
        char line[96];
        if(i + 1 < count) {
            snprintf(line, sizeof(line), "    \"%.60s\",\n", short_name);
        } else {
            snprintf(line, sizeof(line), "    \"%.60s\"\n", short_name);
        }
        storage_file_write(file, line, strlen(line));
    }

    const char* footer = "  ]\n}\n";
    storage_file_write(file, footer, strlen(footer));
    storage_file_close(file);
    storage_file_free(file);
    return true;
}

bool f69_op_create(Storage* storage, F69Operation* op, F69OpType type, F69PathNum path) {
    furi_check(op);
    memset(op, 0, sizeof(F69Operation));

    f69_generate_codename(op->codename, sizeof(op->codename));
    f69_generate_op_id(op->op_id, sizeof(op->op_id), op->codename);
    f69_generate_workspace(op->workspace, sizeof(op->workspace));

    op->op_type = type;
    op->pathnum = path;
    op->phase = F69PhaseOpPrep;
    op->opsec = true;
    op->authorized = (type == F69OpReplay || type == F69OpInject) ? false : true;
    op->capture_count = 0;

    snprintf(op->op_path, sizeof(op->op_path), "%s/%s", F69_OPS_ROOT, op->op_id);
    storage_common_mkdir(storage, op->op_path);

    f69_timeline_append(storage, op->op_path, "INTAKE", op->codename);
    f69_timeline_append(storage, op->op_path, "OP_PREP", f69_pathnum_label(path));
    f69_create_scaffold(storage, op);

    bool ok = f69_op_save(storage, op);
    f69_update_index(storage);
    return ok;
}

bool f69_op_save(Storage* storage, const F69Operation* op) {
    return f69_write_operation_json(storage, op);
}

bool f69_op_refresh_captures(Storage* storage, F69Operation* op) {
    if(!op || !op->op_path[0]) return false;
    char dir[256];
    snprintf(dir, sizeof(dir), "%s/captures", op->op_path);

    File* d = storage_file_alloc(storage);
    if(!storage_dir_open(d, dir)) {
        storage_file_free(d);
        op->capture_count = 0;
        return false;
    }

    uint16_t n = 0;
    char name[64];
    FileInfo info;
    while(storage_dir_read(d, &info, name, sizeof(name))) {
        if(info.flags & FSF_DIRECTORY) continue;
        if(name[0] == '.') continue;
        n++;
    }
    storage_dir_close(d);
    storage_file_free(d);
    op->capture_count = n;
    return true;
}

bool f69_op_load(Storage* storage, F69Operation* op, const char* op_path) {
    char json_path[256];
    snprintf(json_path, sizeof(json_path), "%s/OPERATION.json", op_path);

    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, json_path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        storage_file_free(file);
        return false;
    }

    char buf[900];
    size_t read = storage_file_read(file, buf, sizeof(buf) - 1);
    buf[read] = '\0';
    storage_file_close(file);
    storage_file_free(file);

    memset(op, 0, sizeof(F69Operation));
    strncpy(op->op_path, op_path, sizeof(op->op_path) - 1);
    f69_parse_field(buf, "opId", op->op_id, sizeof(op->op_id));
    f69_parse_field(buf, "codename", op->codename, sizeof(op->codename));
    f69_parse_field(buf, "workspace", op->workspace, sizeof(op->workspace));
    f69_parse_field(buf, "manifestHash", op->manifest_hash, sizeof(op->manifest_hash));

    if(strstr(buf, "\"opsec\":true")) op->opsec = true;
    if(strstr(buf, "\"authorized\":true")) op->authorized = true;

    char type_buf[24] = {0};
    if(f69_parse_field(buf, "opType", type_buf, sizeof(type_buf))) {
        if(strcmp(type_buf, "proximity") == 0)
            op->op_type = F69OpProximity;
        else if(strcmp(type_buf, "survey") == 0)
            op->op_type = F69OpSurvey;
        else if(strcmp(type_buf, "replay") == 0)
            op->op_type = F69OpReplay;
        else if(strcmp(type_buf, "inject") == 0)
            op->op_type = F69OpInject;
        else
            op->op_type = F69OpUnified;
    } else {
        op->op_type = F69OpUnified;
    }

    const char* path_lbl = strstr(buf, "\"pathLabel\":\"");
    if(path_lbl) {
        path_lbl += 13;
        if(strncmp(path_lbl, "imps", 4) == 0)
            op->pathnum = F69PathImps;
        else if(strncmp(path_lbl, "slow", 4) == 0)
            op->pathnum = F69PathSlow;
        else if(strncmp(path_lbl, "fast", 4) == 0)
            op->pathnum = F69PathFast;
        else if(strncmp(path_lbl, "emerg", 5) == 0)
            op->pathnum = F69PathEmerg;
        else
            op->pathnum = F69PathDs;
    } else {
        op->pathnum = F69PathDs;
    }

    const char* phase = strstr(buf, "\"phase\":\"");
    if(phase) {
        phase += 9;
        if(strncmp(phase, "OP_PREP", 7) == 0)
            op->phase = F69PhaseOpPrep;
        else if(strncmp(phase, "PROBE", 5) == 0)
            op->phase = F69PhaseProbe;
        else if(strncmp(phase, "CAPTURE", 7) == 0)
            op->phase = F69PhaseCapture;
        else if(strncmp(phase, "VERIFY", 6) == 0)
            op->phase = F69PhaseVerify;
        else if(strncmp(phase, "EXFIL", 5) == 0)
            op->phase = F69PhaseExfil;
        else if(strncmp(phase, "CLOSE", 5) == 0)
            op->phase = F69PhaseClose;
        else
            op->phase = F69PhaseIntake;
    }

    f69_op_refresh_captures(storage, op);
    return op->op_id[0] != '\0';
}

bool f69_op_advance_phase(Storage* storage, F69Operation* op) {
    if(op->phase < F69PhaseClose) {
        op->phase = (F69Phase)(op->phase + 1);
    }

    switch(op->phase) {
    case F69PhaseProbe:
        f69_timeline_append(storage, op->op_path, "PROBE", f69_optype_label(op->op_type));
        break;
    case F69PhaseCapture:
        f69_op_refresh_captures(storage, op);
        f69_timeline_append(storage, op->op_path, "CAPTURE", op->workspace);
        break;
    case F69PhaseVerify:
        flipper69_write_manifest(storage, op->op_path, op->manifest_hash, sizeof(op->manifest_hash));
        f69_timeline_append(storage, op->op_path, "VERIFY", op->manifest_hash);
        furi_hal_vibro_on(true);
        furi_delay_ms(80);
        furi_hal_vibro_on(false);
        break;
    case F69PhaseExfil:
        f69_timeline_append(storage, op->op_path, "EXFIL", "usb_serial_ready");
        break;
    case F69PhaseClose:
        f69_timeline_append(storage, op->op_path, "CLOSE", op->manifest_hash);
        break;
    default:
        break;
    }

    f69_op_save(storage, op);
    return true;
}

bool f69_op_run_auto(Storage* storage, F69Operation* op) {
    while(op->phase < F69PhaseClose) {
        f69_op_advance_phase(storage, op);
        furi_delay_ms(op->pathnum == F69PathFast ? 100 : (op->pathnum == F69PathEmerg ? 60 : 280));
    }
    return true;
}

bool f69_op_close(Storage* storage, F69Operation* op) {
    if(!op) return false;
    if(op->phase < F69PhaseVerify) {
        flipper69_write_manifest(storage, op->op_path, op->manifest_hash, sizeof(op->manifest_hash));
    }
    op->phase = F69PhaseClose;
    f69_timeline_append(storage, op->op_path, "CLOSE", op->manifest_hash[0] ? op->manifest_hash : "sealed");
    f69_op_save(storage, op);
    f69_update_index(storage);
    return true;
}

bool f69_list_ops(Storage* storage, char paths[][192], size_t* count) {
    *count = 0;

    File* dir = storage_file_alloc(storage);
    if(!storage_dir_open(dir, F69_OPS_ROOT)) {
        storage_file_free(dir);
        return false;
    }

    char name[64];
    FileInfo info;
    while(storage_dir_read(dir, &info, name, sizeof(name))) {
        if(info.flags & FSF_DIRECTORY) {
            if(strncmp(name, "op-", 3) != 0) continue;
            snprintf(paths[*count], 192, "%s/%s", F69_OPS_ROOT, name);
            (*count)++;
            if(*count >= F69_MAX_OPS) break;
        }
    }

    storage_dir_close(dir);
    storage_file_free(dir);
    return true;
}

bool f69_audit_ops(Storage* storage, char* report, size_t report_len) {
    char paths[F69_MAX_OPS][192];
    size_t count = 0;
    f69_list_ops(storage, paths, &count);

    size_t orphans = 0;
    size_t sealed = 0;
    size_t open_ops = 0;
    for(size_t i = 0; i < count; i++) {
        char manifest[256];
        snprintf(manifest, sizeof(manifest), "%s/CASEFILE-MANIFEST.json", paths[i]);
        if(storage_common_stat(storage, manifest, NULL) == FSE_OK) {
            sealed++;
        } else {
            orphans++;
        }

        F69Operation tmp;
        if(f69_op_load(storage, &tmp, paths[i]) && tmp.phase != F69PhaseClose) {
            open_ops++;
        }
    }

    snprintf(
        report,
        report_len,
        "v%s OPS:%u\nSEALED:%u OPEN:%u\nORPHAN:%u",
        F69_VER,
        (unsigned)count,
        (unsigned)sealed,
        (unsigned)open_ops,
        (unsigned)orphans);
    return true;
}

bool f69_panic_wipe(Storage* storage) {
    char paths[F69_MAX_OPS][192];
    size_t count = 0;
    f69_list_ops(storage, paths, &count);

    for(size_t i = 0; i < count; i++) {
        storage_simply_remove_recursive(storage, paths[i]);
    }

    char index[192];
    snprintf(index, sizeof(index), "%s/index.json", F69_ROOT);
    storage_simply_remove(storage, index);
    f69_ensure_roots(storage);
    f69_update_index(storage);
    return true;
}
