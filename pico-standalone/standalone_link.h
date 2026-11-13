#ifndef EE475_STANDALONE_LINK_H
#define EE475_STANDALONE_LINK_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

enum { SL_FRAME_MAX = 128, SL_EXPIRY_MS = 500, SL_ALLOWANCE_MS = 20 };
typedef struct { uint32_t session, seq, type, status, count; } sl_ack_t;
typedef struct { const char *s; size_t n; } sl_field_t;

static inline uint16_t sl_crc16(const char *s, size_t n) {
    uint16_t crc = 0xffffu;
    for (size_t i = 0; i < n; ++i) {
        crc ^= (uint16_t)(uint8_t)s[i] << 8;
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (uint16_t)(((uint32_t)crc << 1) ^ ((crc & 0x8000u) ? 0x1021u : 0u));
    }
    return crc;
}

static inline int sl_hex(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

/* The frame returned here contains LF but is not NUL-terminated. */
static inline size_t sl_encode(char *out, size_t capacity, const char *payload) {
    static const char hex[] = "0123456789ABCDEF";
    size_t n = strlen(payload);
    if (n + 7 > capacity || n + 7 > SL_FRAME_MAX || !n) return 0;
    for (size_t i = 0; i < n; ++i)
        if ((unsigned char)payload[i] < 33 || (unsigned char)payload[i] > 126 || payload[i] == '*') return 0;
    uint16_t crc = sl_crc16(payload, n);
    out[0] = '@';
    memcpy(out + 1, payload, n);
    out[n + 1] = '*';
    for (unsigned i = 0; i < 4; ++i) out[n + 2 + i] = hex[(crc >> (12 - i * 4)) & 15u];
    out[n + 6] = '\n';
    return n + 7;
}

static inline bool sl_decimal(sl_field_t field, uint32_t limit, uint32_t *out) {
    if (!field.n) return false;
    uint32_t value = 0;
    for (size_t i = 0; i < field.n; ++i) {
        if (field.s[i] < '0' || field.s[i] > '9') return false;
        uint32_t digit = (uint32_t)(field.s[i] - '0');
        if (digit > limit || value > (limit - digit) / 10u) return false;
        value = value * 10u + digit;
    }
    *out = value;
    return true;
}

/* Input excludes LF. Strict ACK-only parser, no sscanf/heap/command execution. */
static inline bool sl_parse_ack(const char *s, size_t n, sl_ack_t *out) {
    if (n < 10 || n >= SL_FRAME_MAX || s[0] != '@' || s[n - 5] != '*') return false;
    size_t star = n - 5;
    uint16_t supplied = 0;
    for (size_t i = star + 1; i < n; ++i) {
        int nibble = sl_hex(s[i]);
        if (nibble < 0) return false;
        supplied = (uint16_t)((supplied << 4) | (unsigned)nibble);
    }
    if (supplied != sl_crc16(s + 1, star - 1)) return false;
    sl_field_t f[7];
    size_t count = 0, begin = 1;
    for (size_t i = 1; i <= star; ++i) {
        if (i == star || s[i] == ',') {
            if (i == begin || count == 7) return false;
            f[count++] = (sl_field_t){s + begin, i - begin};
            begin = i + 1;
        } else if ((unsigned char)s[i] < 33 || (unsigned char)s[i] > 126 || s[i] == '*') return false;
    }
    if (count != 7 || f[0].n != 1 || f[0].s[0] != 'A' || f[1].n != 1 || f[1].s[0] != '1' || f[2].n != 8)
        return false;
    uint32_t session = 0;
    for (size_t i = 0; i < 8; ++i) {
        int digit = sl_hex(f[2].s[i]);
        if (digit < 0) return false;
        session = (session << 4) | (unsigned)digit;
    }
    sl_ack_t parsed = { .session = session };
    if (!sl_decimal(f[3], UINT32_MAX, &parsed.seq) || !sl_decimal(f[4], 2, &parsed.type) ||
        !sl_decimal(f[5], 4, &parsed.status) || !sl_decimal(f[6], UINT32_MAX, &parsed.count)) return false;
    *out = parsed;
    return true;
}

/* 4096 samples / 48 kHz has a 42.667 ms half-window duration. */
static inline uint32_t sl_measurement_age_ms(uint64_t window_end_us, uint64_t now_us) {
    uint64_t age_us = (now_us >= window_end_us ? now_us - window_end_us : 0) + 42667u;
    uint64_t age_ms = (age_us + 999u) / 1000u;
    return age_ms > UINT32_MAX ? UINT32_MAX : (uint32_t)age_ms;
}

static inline bool sl_age_is_fresh(uint32_t age_ms) {
    return age_ms <= SL_EXPIRY_MS - SL_ALLOWANCE_MS;
}

typedef struct { uint64_t last_code_us; bool have_code, confirmed; } sl_confirmation_t;
static inline void sl_confirmation_reset(sl_confirmation_t *state) {
    *state = (sl_confirmation_t){0};
}
static inline bool sl_confirm(sl_confirmation_t *state, uint64_t center_us, bool code_hit) {
    if (state->have_code && (center_us <= state->last_code_us || center_us - state->last_code_us >= 750000u))
        sl_confirmation_reset(state);
    if (code_hit) {
        state->confirmed = state->have_code;
        state->have_code = true;
        state->last_code_us = center_us;
    }
    return state->confirmed;
}

#endif
