#pragma once
// Receive-only USB diagnostics. Never changes Receiver state or drives a motor.
// Call only after parse() succeeds and process() returns the matching ACK.
#include "gap_protocol.h"

namespace gaplink {
static constexpr size_t DIAGNOSTIC_CAPACITY = 192;
static constexpr const char *BAD_FRAME_DIAGNOSTIC = "RX_REJECTED reason=bad_frame\n";

inline const char *bearing_class(const Message &message, const Ack &ack) {
    // A rejected packet must not be promoted to the current diagnostic fit.
    if (ack.status == WRONG_SESSION || ack.status == DUPLICATE) return "RX_REJECTED";
    if (ack.status == STALE || message.age_ms + UART_ALLOWANCE_MS > MAX_MEASUREMENT_AGE_MS)
        return "DIAG_STALE";
    if (ack.status == INVALID || !message.valid) return "DIAG_INVALID";
    return "ACCEPTED";
}

inline size_t format_bearing_diagnostic(const Message &message, const Ack &ack,
                                       bool target_valid, char *output, size_t capacity) {
    if (!capacity) return 0;
    output[0] = 0;
    if (message.kind != BEARING || ack.kind != BEARING ||
        message.session != ack.session || message.seq != ack.seq) return 0;
    const int n = snprintf(output, capacity,
        "BEARING seq=%lu class=%s ack_status=%u source_valid=%u raw_cdeg=%lu raw_q=%lu source_age_ms=%lu target_valid=%u\n",
        static_cast<unsigned long>(message.seq), bearing_class(message, ack),
        static_cast<unsigned>(ack.status), static_cast<unsigned>(message.valid),
        static_cast<unsigned long>(message.angle_cdeg), static_cast<unsigned long>(message.quality),
        static_cast<unsigned long>(message.age_ms), target_valid ? 1u : 0u);
    if (n < 0 || static_cast<size_t>(n) >= capacity) { output[0] = 0; return 0; }
    return static_cast<size_t>(n);
}
} // namespace gaplink
