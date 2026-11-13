#ifndef EE475_LINK_FRAME_H
#define EE475_LINK_FRAME_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Maximum wire frame includes LF. Input to validation excludes that LF. */
enum { LINK_FRAME_MAX = 128 };

static inline uint16_t link_crc16(const char *data, size_t length) {
    uint16_t crc = 0xffffu;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)(uint8_t)data[i] << 8;
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (uint16_t)((crc & 0x8000u) ? ((uint32_t)crc << 1) ^ 0x1021u : (uint32_t)crc << 1);
    }
    return crc;
}

static inline int link_hex(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

typedef struct { const char *start; size_t length; } link_field;

static inline bool link_uint(link_field field, uint32_t limit) {
    if (!field.length) return false;
    uint32_t number = 0;
    for (size_t i = 0; i < field.length; ++i) {
        char c = field.start[i];
        if (c < '0' || c > '9') return false;
        uint32_t digit = (uint32_t)(c - '0');
        if (digit > limit || number > (limit - digit) / 10u) return false;
        number = number * 10u + digit;
    }
    return true;
}

static inline bool link_frame_valid(const char *frame, size_t length, bool ack) {
    if (length < 10 || length >= LINK_FRAME_MAX || frame[0] != '@' || frame[length - 5] != '*')
        return false;
    const size_t star = length - 5;
    uint16_t supplied = 0;
    for (size_t i = star + 1; i < length; ++i) {
        int nibble = link_hex(frame[i]);
        if (nibble < 0) return false;
        supplied = (uint16_t)((supplied << 4) | nibble);
    }
    if (supplied != link_crc16(frame + 1, star - 1)) return false;
    link_field fields[8];
    size_t count = 0, begin = 1;
    for (size_t i = 1; i <= star; ++i) {
        if (i == star || frame[i] == ',') {
            if (count == 8 || i == begin) return false;
            fields[count++] = (link_field){frame + begin, i - begin};
            begin = i + 1;
        } else if ((unsigned char)frame[i] < 33 || (unsigned char)frame[i] > 126 || frame[i] == '*') {
            return false;
        }
    }
    if (count < 3 || fields[0].length != 1 || fields[1].length != 1 || fields[1].start[0] != '1' || fields[2].length != 8)
        return false;
    for (size_t i = 0; i < 8; ++i) if (link_hex(fields[2].start[i]) < 0) return false;
    char type = fields[0].start[0];
    if (ack)
        return type == 'A' && count == 7 && link_uint(fields[3], UINT32_MAX) &&
            link_uint(fields[4], 2) && link_uint(fields[5], 4) && link_uint(fields[6], UINT32_MAX);
    if (type == 'H') return count == 3;
    if (type == 'P') return count == 4 && link_uint(fields[3], UINT32_MAX);
    return type == 'B' && count == 8 && link_uint(fields[3], UINT32_MAX) &&
        link_uint(fields[4], 60000) && link_uint(fields[5], 1) &&
        link_uint(fields[6], 35999) && link_uint(fields[7], 1000);
}

#endif
