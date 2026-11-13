#pragma once
// Hardware-independent, bounded protocol/state logic shared by the firmware
// and its C++ tests. No Arduino, UART, motor, or GPIO access in this header.
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

namespace gaplink {
static constexpr size_t MAX_FRAME = 128; // Includes LF; CRLF is not this protocol.
static constexpr uint32_t UART_ALLOWANCE_MS = 20;
static constexpr uint32_t MAX_MEASUREMENT_AGE_MS = 500;
enum Kind : uint8_t { HELLO = 0, PING = 1, BEARING = 2 };
enum Status : uint8_t { ACCEPTED = 0, INVALID = 1, STALE = 2, DUPLICATE = 3, WRONG_SESSION = 4 };

inline uint16_t crc16(const char *s, size_t n) {
    uint16_t crc = 0xffff;
    for (size_t i = 0; i < n; ++i) {
        crc ^= static_cast<uint16_t>(static_cast<uint8_t>(s[i])) << 8;
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                                : static_cast<uint16_t>(crc << 1);
    }
    return crc;
}

inline int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

inline bool hex_number(const char *s, size_t digits, uint32_t &value) {
    if (strlen(s) != digits) return false;
    value = 0;
    for (size_t i = 0; i < digits; ++i) {
        const int d = hex_digit(s[i]);
        if (d < 0) return false;
        value = (value << 4) | static_cast<unsigned>(d);
    }
    return true;
}

inline bool decimal(const char *s, uint32_t maximum, uint32_t &value) {
    if (!*s) return false;
    value = 0;
    for (; *s; ++s) {
        if (*s < '0' || *s > '9') return false;
        const unsigned d = static_cast<unsigned>(*s - '0');
        if (value > maximum / 10 || (value == maximum / 10 && d > maximum % 10)) return false;
        value = value * 10 + d;
    }
    return true;
}

struct Message {
    Kind kind = HELLO;
    uint32_t session = 0, seq = 0, age_ms = 0;
    uint32_t valid = 0, angle_cdeg = 0, quality = 0;
};

// Input excludes LF, as returned by LineReader. Validated before tokenization.
inline bool parse(const char *line, Message &message) {
    const size_t n = strlen(line);
    if (n < 7 || n + 1 > MAX_FRAME || line[0] != '@') return false;
    const size_t star = n - 5;
    if (line[star] != '*') return false;
    uint32_t supplied_crc = 0;
    if (!hex_number(line + star + 1, 4, supplied_crc)) return false;
    if (crc16(line + 1, star - 1) != supplied_crc) return false;
    char payload[MAX_FRAME];
    memcpy(payload, line + 1, star - 1);
    payload[star - 1] = 0;
    char *fields[8] = {payload};
    size_t count = 1;
    for (char *p = payload; *p; ++p) {
        if (*p == ',') {
            if (count == 8) return false;
            *p = 0;
            fields[count++] = p + 1;
        }
    }
    for (size_t i = 0; i < count; ++i) if (!*fields[i]) return false;
    if (count < 3 || strcmp(fields[1], "1") != 0) return false;
    Message candidate;
    if (!hex_number(fields[2], 8, candidate.session)) return false;
    if (strcmp(fields[0], "H") == 0 && count == 3) candidate.kind = HELLO;
    else if (strcmp(fields[0], "P") == 0 && count == 4) {
        candidate.kind = PING;
        if (!decimal(fields[3], UINT32_MAX, candidate.seq)) return false;
    } else if (strcmp(fields[0], "B") == 0 && count == 8) {
        candidate.kind = BEARING;
        if (!decimal(fields[3], UINT32_MAX, candidate.seq) ||
            !decimal(fields[4], 60000, candidate.age_ms) ||
            !decimal(fields[5], 1, candidate.valid) ||
            !decimal(fields[6], 35999, candidate.angle_cdeg) ||
            !decimal(fields[7], 1000, candidate.quality)) return false;
    } else return false;
    message = candidate;
    return true;
}

inline size_t frame(const char *payload, char *output, size_t capacity) {
    const size_t n = strlen(payload);
    if (n + 7 > MAX_FRAME || capacity < n + 8) return 0;
    const int written = snprintf(output, capacity, "@%s*%04X\n", payload, crc16(payload, n));
    return written > 0 && static_cast<size_t>(written) < capacity ? static_cast<size_t>(written) : 0;
}

// At most 127 non-LF bytes plus terminator. A malformed/overlong line is
// discarded completely through its LF; a valid suffix cannot be accepted.
class LineReader {
public:
    enum Result : uint8_t { NONE, READY, REJECTED };
    Result push(char c) {
        if (c == '\n') {
            const bool bad = discard_ || used_ == 0;
            buffer_[used_] = 0;
            used_ = 0;
            discard_ = false;
            return bad ? REJECTED : READY;
        }
        if (discard_) return NONE;
        if (c < 32 || c > 126 || used_ >= MAX_FRAME - 1) {
            discard_ = true;
            return NONE;
        }
        buffer_[used_++] = c;
        return NONE;
    }
    const char *line() const { return buffer_; }
private:
    char buffer_[MAX_FRAME] = {};
    size_t used_ = 0;
    bool discard_ = false;
};

struct Ack {
    uint32_t session = 0, seq = 0;
    Kind kind = HELLO;
    Status status = ACCEPTED;
    uint32_t count = 0;
};

inline size_t format_ack(const Ack &ack, char *output, size_t capacity) {
    char payload[96];
    const int n = snprintf(payload, sizeof payload, "A,1,%08lX,%lu,%u,%u,%lu",
        static_cast<unsigned long>(ack.session), static_cast<unsigned long>(ack.seq),
        static_cast<unsigned>(ack.kind), static_cast<unsigned>(ack.status),
        static_cast<unsigned long>(ack.count));
    if (n < 0 || static_cast<size_t>(n) >= sizeof payload) return 0;
    return frame(payload, output, capacity);
}

class Receiver {
public:
    bool configured = false, have_seq = false, target_valid = false;
    uint32_t session = 0, last_seq = 0, accepted_count = 0;
    uint32_t received_ms = 0, source_age_ms = 0, angle_cdeg = 0, quality = 0;

    static bool newer(uint32_t value, uint32_t previous) {
        const uint32_t delta = value - previous;
        return delta != 0 && delta < 0x80000000u;
    }
    uint32_t age(uint32_t now) const { return source_age_ms + UART_ALLOWANCE_MS + (now - received_ms); }
    bool expire(uint32_t now) {
        if (target_valid && age(now) > MAX_MEASUREMENT_AGE_MS) {
            target_valid = false;
            return true;
        }
        return false;
    }
    Ack process(const Message &m, uint32_t now) {
        expire(now);
        Ack ack;
        ack.session = m.session; ack.seq = m.seq; ack.kind = m.kind;
        if (m.kind == HELLO) {
            if (!configured || session != m.session) {
                configured = true; session = m.session;
                have_seq = false; target_valid = false;
            }
            ++accepted_count;
        } else if (!configured || session != m.session) ack.status = WRONG_SESSION;
        else if (m.kind == PING) ++accepted_count; // Link only; no measurement renewal.
        else if (have_seq && !newer(m.seq, last_seq)) ack.status = DUPLICATE;
        else {
            have_seq = true; last_seq = m.seq;
            if (!m.valid) {
                target_valid = false; ++accepted_count; ack.status = INVALID;
            } else if (m.age_ms + UART_ALLOWANCE_MS > MAX_MEASUREMENT_AGE_MS) {
                target_valid = false; ack.status = STALE;
            } else {
                target_valid = true; source_age_ms = m.age_ms; received_ms = now;
                angle_cdeg = m.angle_cdeg; quality = m.quality; ++accepted_count;
            }
        }
        ack.count = accepted_count;
        return ack;
    }
};
} // namespace gaplink
