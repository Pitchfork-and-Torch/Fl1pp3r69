#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint8_t data[64];
    uint32_t datalen;
    uint64_t bitlen;
    uint32_t state[8];
} F69Sha256Ctx;

void f69_sha256_init(F69Sha256Ctx* ctx);
void f69_sha256_update(F69Sha256Ctx* ctx, const uint8_t* data, size_t len);
void f69_sha256_final(F69Sha256Ctx* ctx, uint8_t hash[32]);
void f69_sha256_hex(const uint8_t hash[32], char* out, size_t out_len);