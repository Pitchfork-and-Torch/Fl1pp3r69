#include "flipper69_manifest.h"
#include "flipper69_fieldops.h"
#include "flipper69_sha256.h"

#include <furi.h>
#include <furi_hal_rtc.h>
#include <storage/storage.h>

#include <stdio.h>
#include <string.h>

#define MANIFEST_FILENAME "CASEFILE-MANIFEST.json"
/* v4 ARGUS VEIL: raised inline seal capacity; chunked mode for larger ops on desktop */
#define MAX_MANIFEST_ITEMS 64

typedef struct {
    char rel_path[96];
    char hash[65];
    uint32_t size;
    const char* probe;
} ManifestItem;

bool flipper69_sha256_bytes(const uint8_t* data, size_t len, char* out_hex, size_t out_len) {
    if(out_len < 65 || !data) return false;
    F69Sha256Ctx ctx;
    uint8_t hash[32];
    f69_sha256_init(&ctx);
    f69_sha256_update(&ctx, data, len);
    f69_sha256_final(&ctx, hash);
    f69_sha256_hex(hash, out_hex, out_len);
    return true;
}

bool flipper69_sha256_file(Storage* storage, const char* path, char* out_hex, size_t out_len) {
    if(out_len < 65) return false;

    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, path, FSAM_READ, FSOM_OPEN_EXISTING)) {
        storage_file_free(file);
        return false;
    }

    F69Sha256Ctx ctx;
    uint8_t hash[32];
    uint8_t buf[512];
    size_t read = 0;

    f69_sha256_init(&ctx);
    while((read = storage_file_read(file, buf, sizeof(buf))) > 0) {
        f69_sha256_update(&ctx, buf, read);
    }
    f69_sha256_final(&ctx, hash);
    f69_sha256_hex(hash, out_hex, out_len);

    storage_file_close(file);
    storage_file_free(file);
    return true;
}

static bool manifest_add_file(
    Storage* storage,
    ManifestItem* items,
    size_t* count,
    const char* op_path,
    const char* rel,
    const char* probe) {
    if(*count >= MAX_MANIFEST_ITEMS) return false;

    char full[256];
    snprintf(full, sizeof(full), "%s/%s", op_path, rel);

    FileInfo info;
    if(storage_common_stat(storage, full, &info) != FSE_OK) return false;

    ManifestItem* item = &items[*count];
    strncpy(item->rel_path, rel, sizeof(item->rel_path) - 1);
    item->size = info.size;
    item->probe = probe;
    if(!flipper69_sha256_file(storage, full, item->hash, sizeof(item->hash))) return false;
    (*count)++;
    return true;
}

static bool manifest_add_dir_files(
    Storage* storage,
    ManifestItem* items,
    size_t* count,
    const char* op_path,
    const char* subdir,
    const char* probe) {
    char dir_path[192];
    snprintf(dir_path, sizeof(dir_path), "%s/%s", op_path, subdir);

    File* dir = storage_file_alloc(storage);
    if(!storage_dir_open(dir, dir_path)) {
        storage_file_free(dir);
        return false;
    }

    char name[64];
    FileInfo info;
    bool ok = true;
    while(storage_dir_read(dir, &info, name, sizeof(name))) {
        if(info.flags & FSF_DIRECTORY) continue;
        char rel[96];
        snprintf(rel, sizeof(rel), "%s/%s", subdir, name);
        if(!manifest_add_file(storage, items, count, op_path, rel, probe)) {
            ok = false;
            break;
        }
    }

    storage_dir_close(dir);
    storage_file_free(dir);
    return ok;
}

bool flipper69_write_manifest(Storage* storage, const char* op_path, char* out_manifest_hash, size_t hash_len) {
    ManifestItem items[MAX_MANIFEST_ITEMS];
    size_t count = 0;

    manifest_add_file(storage, items, &count, op_path, "OPERATION.json", NULL);
    manifest_add_file(storage, items, &count, op_path, "TIMELINE.jsonl", NULL);
    manifest_add_dir_files(storage, items, &count, op_path, "captures", "field");

    DateTime dt;
    furi_hal_rtc_get_datetime(&dt);

    char manifest_path[256];
    snprintf(manifest_path, sizeof(manifest_path), "%s/%s", op_path, MANIFEST_FILENAME);

    /* extract op id from path tail for schema compliance */
    const char* slash = strrchr(op_path, '/');
    const char* op_id = slash ? slash + 1 : op_path;

    /* v3: hash previous manifest for chainPrev BEFORE truncate/write */
    char chain_prev[65] = {0};
    bool has_prev = false;
    if(storage_common_stat(storage, manifest_path, NULL) == FSE_OK) {
        has_prev = flipper69_sha256_file(storage, manifest_path, chain_prev, sizeof(chain_prev));
    }

    File* file = storage_file_alloc(storage);
    if(!storage_file_open(file, manifest_path, FSAM_WRITE, FSOM_CREATE_ALWAYS)) {
        storage_file_free(file);
        return false;
    }

    char header[420];
    if(has_prev && chain_prev[0]) {
        snprintf(
            header,
            sizeof(header),
            "{\n  \"schemaVersion\":4,\n  \"generatedAt\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\",\n  \"opId\":\"%s\",\n  \"firmware\":\"flipper69\",\n  \"firmwareVersion\":\"%s\",\n  \"releaseCodename\":\"%s\",\n  \"classification\":\"%s\",\n  \"sealAlg\":\"sha256\",\n  \"verifyCount\":2,\n  \"chainPrev\":\"%s\",\n  \"items\":[\n",
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            op_id,
            F69_VER,
            F69_RELEASE,
            F69_CLASSIFICATION,
            chain_prev);
    } else {
        snprintf(
            header,
            sizeof(header),
            "{\n  \"schemaVersion\":4,\n  \"generatedAt\":\"%04d-%02d-%02dT%02d:%02d:%02dZ\",\n  \"opId\":\"%s\",\n  \"firmware\":\"flipper69\",\n  \"firmwareVersion\":\"%s\",\n  \"releaseCodename\":\"%s\",\n  \"classification\":\"%s\",\n  \"sealAlg\":\"sha256\",\n  \"verifyCount\":1,\n  \"chainPrev\":null,\n  \"items\":[\n",
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            op_id,
            F69_VER,
            F69_RELEASE,
            F69_CLASSIFICATION);
    }
    storage_file_write(file, header, strlen(header));

    for(size_t i = 0; i < count; i++) {
        char chunk[128];
        storage_file_write(file, "    {", 5);
        if(items[i].probe) {
            storage_file_write(file, "\"type\":\"capture\"", 18);
        } else {
            storage_file_write(file, "\"type\":\"metadata\"", 19);
        }
        snprintf(chunk, sizeof(chunk), ",\"path\":\"%.80s\"", items[i].rel_path);
        storage_file_write(file, chunk, strlen(chunk));
        snprintf(chunk, sizeof(chunk), ",\"hash\":\"%.64s\"", items[i].hash);
        storage_file_write(file, chunk, strlen(chunk));
        snprintf(chunk, sizeof(chunk), ",\"sizeBytes\":%lu", (unsigned long)items[i].size);
        storage_file_write(file, chunk, strlen(chunk));
        if(items[i].probe) {
            snprintf(chunk, sizeof(chunk), ",\"probe\":\"%s\"", items[i].probe);
            storage_file_write(file, chunk, strlen(chunk));
        }
        storage_file_write(file, "}", 1);
        if(i + 1 < count) {
            storage_file_write(file, ",\n", 2);
        } else {
            storage_file_write(file, "\n", 1);
        }
    }

    const char* footer = "  ]\n}\n";
    storage_file_write(file, footer, strlen(footer));
    storage_file_close(file);
    storage_file_free(file);

    if(out_manifest_hash && hash_len >= 65) {
        return flipper69_sha256_file(storage, manifest_path, out_manifest_hash, hash_len);
    }
    return true;
}