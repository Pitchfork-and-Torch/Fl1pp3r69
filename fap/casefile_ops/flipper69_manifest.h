#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <storage/storage.h>

bool flipper69_sha256_file(Storage* storage, const char* path, char* out_hex, size_t out_len);
bool flipper69_sha256_bytes(const uint8_t* data, size_t len, char* out_hex, size_t out_len);
bool flipper69_write_manifest(Storage* storage, const char* op_path, char* out_manifest_hash, size_t hash_len);