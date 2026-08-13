/**
 * Fl1pp3r69 libf69 — shared ACTIVE_OP resolve + artifact paths (ARGUS VEIL)
 * Header-only for ufbt FAPs (include via relative path).
 */
#pragma once

#include <furi.h>
#include <storage/storage.h>
#include <stdio.h>
#include <string.h>

#define F69_LIB_ROOT     EXT_PATH("flipper69")
#define F69_LIB_OPS      EXT_PATH("flipper69/operations")
#define F69_LIB_VER      "4.0.0"
#define F69_LIB_RELEASE  "ARGUS VEIL"

/** Resolve active op directory into op_path. Prefer ACTIVE_OP.json, else newest op-*. */
static inline bool f69_resolve_active_op(
    Storage* storage,
    char* op_path,
    size_t op_len,
    char* name_out,
    size_t name_len) {
    if(!storage || !op_path || op_len < 8) return false;
    op_path[0] = '\0';
    if(name_out && name_len) name_out[0] = '\0';

    char active_path[192];
    snprintf(active_path, sizeof(active_path), "%s/ACTIVE_OP.json", F69_LIB_ROOT);
    File* file = storage_file_alloc(storage);
    if(storage_file_open(file, active_path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        char buf[384];
        size_t n = storage_file_read(file, buf, sizeof(buf) - 1);
        buf[n] = '\0';
        storage_file_close(file);
        storage_file_free(file);
        const char* key = "\"opId\":\"";
        const char* start = strstr(buf, key);
        if(start) {
            start += strlen(key);
            const char* end = strchr(start, '"');
            if(end && end > start) {
                size_t len = (size_t)(end - start);
                char id[64];
                if(len >= sizeof(id)) len = sizeof(id) - 1;
                memcpy(id, start, len);
                id[len] = '\0';
                snprintf(op_path, op_len, "%s/%s", F69_LIB_OPS, id);
                if(name_out && name_len) {
                    strncpy(name_out, id, name_len - 1);
                    name_out[name_len - 1] = '\0';
                }
                FileInfo info;
                if(storage_common_stat(storage, op_path, &info) == FSE_OK) {
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
    if(storage_dir_open(dir, F69_LIB_OPS)) {
        char name[64];
        FileInfo info;
        while(storage_dir_read(dir, &info, name, sizeof(name))) {
            if((info.flags & FSF_DIRECTORY) && strncmp(name, "op-", 3) == 0) {
                snprintf(paths[count], 192, "%s/%s", F69_LIB_OPS, name);
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
    if(name_out && name_len) {
        const char* slash = strrchr(op_path, '/');
        strncpy(name_out, slash ? slash + 1 : op_path, name_len - 1);
        name_out[name_len - 1] = '\0';
    }
    return true;
}

/** Ensure captures/ (v3) and artifacts/<domain>/ (v4) exist; return capture dir for writes. */
static inline bool f69_ensure_capture_dirs(
    Storage* storage,
    const char* op_path,
    const char* domain,
    char* out_dir,
    size_t out_len) {
    if(!storage || !op_path || !out_dir) return false;
    char cap[256];
    snprintf(cap, sizeof(cap), "%s/captures", op_path);
    storage_common_mkdir(storage, cap);
    if(domain && domain[0]) {
        char art[256];
        snprintf(art, sizeof(art), "%s/artifacts", op_path);
        storage_common_mkdir(storage, art);
        snprintf(art, sizeof(art), "%s/artifacts/%s", op_path, domain);
        storage_common_mkdir(storage, art);
        /* Prefer artifacts/domain for new writes when it fits */
        if(strlen(art) < out_len) {
            strncpy(out_dir, art, out_len - 1);
            out_dir[out_len - 1] = '\0';
            return true;
        }
    }
    strncpy(out_dir, cap, out_len - 1);
    out_dir[out_len - 1] = '\0';
    return true;
}
