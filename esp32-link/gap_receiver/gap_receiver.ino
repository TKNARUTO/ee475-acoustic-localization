#include <Arduino.h>
#include "gap_protocol.h"
#include "gap_diagnostics.h"
#include "gap_self_tests.h"

// NodeMCU ESP-32S / classic ESP32 bench receiver. No motor or LED pin is used.
static constexpr int PICO_RX_GPIO = 16; // Pico GP0 TX -> ESP32 P16 RX
static constexpr int PICO_TX_GPIO = 17; // ESP32 P17 TX -> Pico GP1 RX
static HardwareSerial PicoLink(2);
static gaplink::LineReader lines;
static gaplink::Receiver receiver;
static uint32_t malformed = 0, rejected_lines = 0, ack_drops = 0, usb_drops = 0;
static uint32_t last_stats = 0;
static bool self_tests_ok = false;

struct TxLine { char data[gaplink::MAX_FRAME + 1]; size_t size = 0; };
static TxLine tx[4];
static unsigned tx_head = 0, tx_count = 0;

static void usb_line(const char *text) {
    const size_t size = strlen(text);
    if (static_cast<size_t>(Serial.availableForWrite()) >= size)
        Serial.write(reinterpret_cast<const uint8_t *>(text), size);
    else ++usb_drops; // Diagnostic output cannot stall acquisition or freshness.
}

static void queue_ack(const gaplink::Ack &ack) {
    char out[gaplink::MAX_FRAME + 1];
    const size_t n = gaplink::format_ack(ack, out, sizeof out);
    if (!n || tx_count == 4) { ++ack_drops; return; }
    TxLine &slot = tx[(tx_head + tx_count) % 4];
    memcpy(slot.data, out, n + 1); slot.size = n; ++tx_count;
    usb_line(out);
}

static void pump_tx() {
    if (!tx_count) return;
    TxLine &slot = tx[tx_head];
    if (static_cast<size_t>(PicoLink.availableForWrite()) < slot.size) return;
    PicoLink.write(reinterpret_cast<const uint8_t *>(slot.data), slot.size);
    tx_head = (tx_head + 1) % 4; --tx_count;
}

static void handle_line(const char *text, uint32_t now) {
    gaplink::Message message;
    if (!gaplink::parse(text, message)) {
        ++malformed; usb_line(gaplink::BAD_FRAME_DIAGNOSTIC); return;
    }
    if (receiver.expire(now)) usb_line("TARGET invalid reason=measurement_timeout\n");
    gaplink::Ack ack = receiver.process(message, now);
    queue_ack(ack);
    if (message.kind == gaplink::BEARING) {
        char state[gaplink::DIAGNOSTIC_CAPACITY];
        if (gaplink::format_bearing_diagnostic(message, ack, receiver.target_valid, state, sizeof state))
            usb_line(state);
    }
}

void setup() {
    // A whole diagnostic line must fit for the nonblocking best-effort write.
    Serial.setTxBufferSize(512);
    Serial.begin(115200);
    // The tests run only on local temporary objects, before hardware UART init.
    const gaplink::TestResult test = gaplink::self_test();
    self_tests_ok = test.failed == 0;
    Serial.printf("SELFTEST %s checks=%u failed=%u first=%s\n",
        self_tests_ok ? "PASS" : "FAIL", test.checks, test.failed,
        test.first_failure ? test.first_failure : "none");
    if (!self_tests_ok) {
        Serial.println("HALTED: protocol self-test failed; link not enabled");
        return;
    }
    PicoLink.setRxBufferSize(512);
    PicoLink.setTxBufferSize(512);
    PicoLink.begin(115200, SERIAL_8N1, PICO_RX_GPIO, PICO_TX_GPIO);
    Serial.println("READY EE475_GAP_RECEIVER v1.1 link_diag RX=16 TX=17 baud=115200 raw_array_diagnostic no_motor");
}

void loop() {
    if (!self_tests_ok) { delay(10); return; }
    const uint32_t now = millis();
    if (receiver.expire(now)) usb_line("TARGET invalid reason=measurement_timeout\n");
    // Keep all operations bounded. No readStringUntil / waiting for a packet.
    for (unsigned budget = 0; budget < 96 && PicoLink.available() > 0; ++budget) {
        const gaplink::LineReader::Result result = lines.push(static_cast<char>(PicoLink.read()));
        if (result == gaplink::LineReader::READY) handle_line(lines.line(), millis());
        else if (result == gaplink::LineReader::REJECTED) ++rejected_lines;
    }
    pump_tx();
    if (static_cast<uint32_t>(now - last_stats) >= 2000) {
        last_stats = now;
        char stats[200];
        snprintf(stats, sizeof stats,
            "STAT count=%lu valid=%u bad=%lu lines=%lu ack_drop=%lu usb_drop=%lu\n",
            static_cast<unsigned long>(receiver.accepted_count), receiver.target_valid ? 1u : 0u,
            static_cast<unsigned long>(malformed), static_cast<unsigned long>(rejected_lines),
            static_cast<unsigned long>(ack_drops), static_cast<unsigned long>(usb_drops));
        usb_line(stats);
    }
    delay(1);
}
