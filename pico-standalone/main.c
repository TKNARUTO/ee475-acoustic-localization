#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/rand.h"
#include "pico/unique_id.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/pio.h"
#include "hardware/sync.h"
#include "hardware/uart.h"
#include "tusb.h"
#include "sen0325_i2s.pio.h"
#include "standalone_link.h"
#include "dsp/gap_dsp.h"

#if GAP_INTEGER_FFT && GAP_INTEGER_FAST
#define GAP_BACKEND_BASE "integer_q15_fast"
#elif GAP_INTEGER_FFT
#define GAP_BACKEND_BASE "integer_q15"
#else
#define GAP_BACKEND_BASE "float"
#endif
#if GAP_WHITEN_FLOAT && GAP_MAG_CACHE
#define GAP_BACKEND_LABEL GAP_BACKEND_BASE "_w1c1"
#elif GAP_WHITEN_FLOAT
#define GAP_BACKEND_LABEL GAP_BACKEND_BASE "_w1c0"
#elif GAP_MAG_CACHE
#define GAP_BACKEND_LABEL GAP_BACKEND_BASE "_w0c1"
#else
#define GAP_BACKEND_LABEL GAP_BACKEND_BASE
#endif

enum { DATA_BASE = 6, BCLK_PIN = 10, WS_PIN = 11, LED_CLK = 12, LED_DATA = 13 };
enum { SAMPLE_RATE = 48000, CAPTURE_BLOCK_FRAMES = 512, WORDS_PER_FRAME = 8,
       DMA_WORDS = CAPTURE_BLOCK_FRAMES * WORDS_PER_FRAME, WINDOW_FRAMES = 4096, MIC_COUNT = 7 };
enum { LINK_TX = 0, LINK_RX = 1, LINK_BAUD = 115200, RX_RING_SIZE = 1024 };

static PIO capture_pio = pio0;
static uint capture_sm, capture_offset;
static int dma_channels[2];
static uint32_t dma_buffers[2][DMA_WORDS];
static int16_t pcm[WINDOW_FRAMES][MIC_COUNT];
static volatile bool capture_running, window_active, block_ready[2], capture_fault;
static volatile bool processing_corrupted, skip_boundary;
static volatile int processing_buffer = -1;
static volatile uint32_t dma_sequence, block_sequence[2], capture_drop_count;
static volatile uint64_t block_end_us[2], accept_after_us;
static uint32_t pcm_frames, previous_block_sequence;
static uint64_t first_block_start_us, window_requested_us;
static uint32_t window_unpack_us, window_max_unpack_us;
static uint64_t last_result_ready_us;

static volatile uint8_t rx_ring[RX_RING_SIZE];
static volatile uint16_t rx_head, rx_tail;
static volatile bool rx_overflow;
static volatile uint32_t rx_byte_drops, uart_errors;
static char tx_frame[SL_FRAME_MAX];
static volatile uint16_t tx_length, tx_position;
static char rx_line[SL_FRAME_MAX];
static size_t rx_used;
static bool rx_discard, uart_ready;
static uint32_t session, uart_sequence, last_bearing_sequence, ack_status = UINT32_MAX;
static uint32_t tx_result_seq, tx_age_ms, tx_valid, tx_angle_cdeg, tx_quality;
static uint32_t ack_seq, ack_roundtrip_us;
static uint64_t bearing_tx_started_us;
static bool bearing_ack_pending;
static uint32_t ack_count, ack_bad, usb_drops, result_sequence;
static uint64_t last_hello_us, last_ack_us;
static bool hello_sent;
static sl_confirmation_t confirmation;

typedef struct {
    gap_result_t estimate;
    gap_profile_t profile;
    uint32_t sequence, capture_us, dsp_us, unpack_total_us, max_block_us;
    uint32_t capture_wait_us, cycle_us, result_interval_us;
    uint64_t end_us;
    bool confirmed, pending;
    const char *override_reason;
} pending_result_t;
static pending_result_t result;

/* No printf/puts/fwrite to USB: diagnostics are one bounded, best-effort write.
 * TinyUSB's background task can continue while the single core evaluates DSP. */
static bool usb_line(const char *line) {
    size_t length = strlen(line);
    bool wrote = false;
    uint32_t irq_state = save_and_disable_interrupts();
    if (tud_cdc_connected() && length <= tud_cdc_write_available()) {
        wrote = tud_cdc_write(line, (uint32_t)length) == length;
        tud_cdc_write_flush();
    }
    restore_interrupts(irq_state);
    if (!wrote && tud_cdc_connected()) ++usb_drops;
    return wrote;
}

static void led_byte(uint8_t value) {
    for (int bit = 7; bit >= 0; --bit) {
        gpio_put(LED_CLK, 0);
        gpio_put(LED_DATA, (value >> bit) & 1u);
        sleep_us(1);
        gpio_put(LED_CLK, 1);
        sleep_us(1);
    }
}
static void led_ring_off(void) {
    for (unsigned i = 0; i < 4; ++i) led_byte(0);
    for (unsigned i = 0; i < 12; ++i) {
        led_byte(0xe0); led_byte(0); led_byte(0); led_byte(0);
    }
    for (unsigned i = 0; i < 8; ++i) led_byte(0xff);
    gpio_put(LED_CLK, 0);
    gpio_put(LED_DATA, 0);
}

static void uart_irq(void) {
    for (unsigned budget = 0; budget < 64 && uart_is_readable(uart0); ++budget) {
        uint32_t data = uart_get_hw(uart0)->dr;
        if (data & 0xf00u) {
            ++uart_errors;
            rx_overflow = true;
            uart_get_hw(uart0)->rsr = 0;
            continue;
        }
        uint16_t next = (uint16_t)((rx_head + 1u) & (RX_RING_SIZE - 1u));
        if (next == rx_tail) { ++rx_byte_drops; rx_overflow = true; }
        else { rx_ring[rx_head] = (uint8_t)data; rx_head = next; }
    }
    for (unsigned budget = 0; budget < 32 && tx_position < tx_length && uart_is_writable(uart0); ++budget)
        uart_get_hw(uart0)->dr = (uint8_t)tx_frame[tx_position++];
    if (tx_length && tx_position == tx_length) {
        tx_length = 0;
        uart_set_irqs_enabled(uart0, true, false);
    }
}

static bool uart_idle(void) { return !tx_length && !(uart_get_hw(uart0)->fr & UART_UARTFR_BUSY_BITS); }

/* Only called with a fully formed H or B frame and an empty UART.
 * Start putting bytes on the wire immediately; IRQ sends the remainder. */
static bool uart_send(const char *frame, size_t length, uint64_t *started_us) {
    if (!length || length > sizeof tx_frame) return false;
    uint32_t irq_state = save_and_disable_interrupts();
    if (!uart_idle()) { restore_interrupts(irq_state); return false; }
    memcpy(tx_frame, frame, length);
    tx_position = 0;
    tx_length = (uint16_t)length;
    /* Timestamp immediately before the first FIFO write, not before formatting.
     * ACK timing also includes the later foreground parsing delay. */
    if (started_us) *started_us = time_us_64();
    while (tx_position < tx_length && uart_is_writable(uart0))
        uart_get_hw(uart0)->dr = (uint8_t)tx_frame[tx_position++];
    bool pending = tx_position < tx_length;
    if (!pending) tx_length = 0;
    uart_set_irqs_enabled(uart0, true, pending);
    restore_interrupts(irq_state);
    return true;
}

static void receive_ack(const sl_ack_t *ack) {
    if (ack->session != session) return;
    if (ack->type == 0 && ack->seq == 0 && ack->status == 0) {
        uart_ready = true;
    } else if (ack->type == 2 && bearing_ack_pending && ack->seq == last_bearing_sequence) {
        uint64_t elapsed = time_us_64() - bearing_tx_started_us;
        ack_seq = ack->seq;
        ack_roundtrip_us = elapsed > UINT32_MAX ? UINT32_MAX : (uint32_t)elapsed;
        ack_status = ack->status;
        bearing_ack_pending = false;
        if (ack->status == 4) { uart_ready = false; hello_sent = false; }
    } else return;
    ++ack_count;
    last_ack_us = time_us_64();
}

static void uart_poll(void) {
    if (rx_overflow) {
        uint32_t irq_state = save_and_disable_interrupts();
        rx_tail = rx_head;
        rx_overflow = false;
        restore_interrupts(irq_state);
        rx_used = 0;
        rx_discard = true;
        ++ack_bad;
    }
    for (unsigned budget = 0; budget < 256 && rx_tail != rx_head; ++budget) {
        char c = (char)rx_ring[rx_tail];
        rx_tail = (uint16_t)((rx_tail + 1u) & (RX_RING_SIZE - 1u));
        if (c == '\n') {
            if (!rx_discard && rx_used) {
                sl_ack_t ack;
                if (sl_parse_ack(rx_line, rx_used, &ack)) receive_ack(&ack);
                else ++ack_bad;
            }
            rx_used = 0; rx_discard = false;
        } else if (!rx_discard) {
            if (c < 32 || c >= 127 || rx_used + 1 >= sizeof rx_line) { rx_discard = true; ++ack_bad; }
            else rx_line[rx_used++] = c;
        }
    }
    uint64_t now = time_us_64();
    if (uart_ready && now - last_ack_us > 1500000u) { uart_ready = false; hello_sent = false; }
    if (!uart_ready && (!hello_sent || now - last_hello_us >= 250000u) && uart_idle()) {
        char payload[32], frame[SL_FRAME_MAX];
        snprintf(payload, sizeof payload, "H,1,%08" PRIX32, session);
        size_t length = sl_encode(frame, sizeof frame, payload);
        if (uart_send(frame, length, NULL)) { last_hello_us = now; hello_sent = true; }
    }
}

static void link_init(void) {
    pico_unique_board_id_t id;
    pico_get_unique_board_id(&id);
    session = get_rand_32() ^ (uint32_t)time_us_64(); // SDK entropy includes ROSC.
    for (size_t i = 0; i < sizeof id.id; ++i) session = (session * 16777619u) ^ id.id[i];
    if (!session) session = 0xa4750001u;
    uart_init(uart0, LINK_BAUD);
    gpio_set_function(LINK_TX, GPIO_FUNC_UART);
    gpio_set_function(LINK_RX, GPIO_FUNC_UART);
    gpio_pull_up(LINK_RX);
    uart_set_hw_flow(uart0, false, false);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_fifo_enabled(uart0, true);
    irq_set_exclusive_handler(UART0_IRQ, uart_irq);
    irq_set_priority(UART0_IRQ, PICO_DEFAULT_IRQ_PRIORITY);
    irq_set_enabled(UART0_IRQ, true);
    uart_set_irqs_enabled(uart0, true, false);
}

static void capture_irq(void) {
    uint32_t mask = (1u << dma_channels[0]) | (1u << dma_channels[1]);
    uint32_t completed = dma_hw->ints0 & mask;
    dma_hw->ints0 = completed;
    if (!capture_running) return;
    if (completed == mask && window_active) { capture_fault = true; ++capture_drop_count; }
    for (int done = 0; done < 2; ++done) {
        if (!(completed & (1u << dma_channels[done]))) continue;
        int other = done ^ 1;
        uint64_t end = time_us_64();
        ++dma_sequence;
        if (window_active && end >= accept_after_us) {
            if (skip_boundary) skip_boundary = false;
            else {
                if (block_ready[other] || processing_buffer == other) {
                    capture_fault = true; ++capture_drop_count;
                    if (processing_buffer == other) processing_corrupted = true;
                }
                block_sequence[done] = dma_sequence;
                block_end_us[done] = end;
                block_ready[done] = true;
            }
        }
        dma_channel_set_write_addr(dma_channels[done], dma_buffers[done], false);
        dma_channel_set_trans_count(dma_channels[done], DMA_WORDS, false);
    }
    if (!dma_channel_is_busy(dma_channels[0]) && !dma_channel_is_busy(dma_channels[1])) {
        if (window_active) { capture_fault = true; ++capture_drop_count; }
        if (processing_buffer == 0) processing_corrupted = true;
        block_ready[0] = false;
        dma_start_channel_mask(1u << dma_channels[0]);
    }
}

static void begin_window(uint32_t settle_us) {
    uint32_t irq_state = save_and_disable_interrupts();
    window_active = false;
    block_ready[0] = block_ready[1] = false;
    capture_fault = processing_corrupted = false;
    processing_buffer = -1;
    pcm_frames = 0;
    window_unpack_us = window_max_unpack_us = 0;
    window_requested_us = time_us_64();
    accept_after_us = window_requested_us + settle_us;
    /* Skip the first completion: its DMA block may have begun during DSP.
     * Thus every accepted sample belongs to this newly requested window. */
    skip_boundary = true;
    window_active = true;
    restore_interrupts(irq_state);
}

static void capture_start(void) {
    if (capture_running) return;
    pio_sm_clear_fifos(capture_pio, capture_sm);
    pio_sm_restart(capture_pio, capture_sm);
    pio_sm_clkdiv_restart(capture_pio, capture_sm);
    pio_sm_exec(capture_pio, capture_sm, pio_encode_jmp(capture_offset));
    for (int i = 0; i < 2; ++i) {
        dma_channel_config config = dma_channel_get_default_config(dma_channels[i]);
        channel_config_set_transfer_data_size(&config, DMA_SIZE_32);
        channel_config_set_read_increment(&config, false);
        channel_config_set_write_increment(&config, true);
        channel_config_set_dreq(&config, pio_get_dreq(capture_pio, capture_sm, false));
        channel_config_set_chain_to(&config, dma_channels[i ^ 1]);
        dma_channel_configure(dma_channels[i], &config, dma_buffers[i], &capture_pio->rxf[capture_sm], DMA_WORDS, false);
        dma_channel_set_irq0_enabled(dma_channels[i], true);
    }
    dma_hw->ints0 = (1u << dma_channels[0]) | (1u << dma_channels[1]);
    capture_pio->fdebug = 1u << capture_sm;
    capture_running = true;
    begin_window(100000); // Initial microphone settling only; not a blocking sleep.
    dma_start_channel_mask(1u << dma_channels[0]);
    pio_sm_set_enabled(capture_pio, capture_sm, true);
}

static void capture_stop(void) {
    capture_running = window_active = false;
    pio_sm_set_enabled(capture_pio, capture_sm, false);
    for (int i = 0; i < 2; ++i) dma_channel_set_irq0_enabled(dma_channels[i], false);
    for (int i = 0; i < 2; ++i) dma_channel_abort(dma_channels[i]);
    dma_hw->ints0 = (1u << dma_channels[0]) | (1u << dma_channels[1]);
    block_ready[0] = block_ready[1] = false;
    processing_buffer = -1;
    pio_sm_clear_fifos(capture_pio, capture_sm);
    pio_sm_set_pins_with_mask(capture_pio, capture_sm, 0, (1u << BCLK_PIN) | (1u << WS_PIN));
}

static inline uint32_t gather_byte(uint32_t word, unsigned lane) {
    uint32_t x = (word >> lane) & 0x11111111u;
    x = (x | (x >> 3)) & 0x03030303u;
    x = (x | (x >> 6)) & 0x000f000fu;
    return (x | (x >> 12)) & 0xffu;
}

static void unpack_block(int index) {
    const volatile uint32_t *data = dma_buffers[index];
    for (unsigned frame = 0; frame < CAPTURE_BLOCK_FRAMES; ++frame) {
        for (unsigned ch = 0; ch < MIC_COUNT; ++ch) {
            unsigned slot = ch == 6 ? 7 : ch;
            const volatile uint32_t *input = data + frame * 8 + (slot % 2) * 4;
            unsigned lane = slot / 2;
            uint32_t raw = (gather_byte(input[0], lane) << 16) | (gather_byte(input[1], lane) << 8) | gather_byte(input[2], lane);
            pcm[pcm_frames + frame][ch] = (int16_t)(((int32_t)(raw << 8) >> 8) >> 8);
        }
    }
}

static bool result_valid(uint32_t age_ms) {
    return !result.override_reason && result.estimate.valid && result.confirmed && sl_age_is_fresh(age_ms) &&
        isfinite(result.estimate.angle_deg) && isfinite(result.estimate.quality);
}

static const char *result_reason(uint32_t age_ms) {
    if (result.override_reason) return result.override_reason;
    if (result.estimate.valid && !sl_age_is_fresh(age_ms)) return "stale_measurement";
    if (result.estimate.valid && !result.confirmed) return "confirming";
    if (result.estimate.valid && (!isfinite(result.estimate.angle_deg) || !isfinite(result.estimate.quality))) return "dsp_nonfinite";
    return gap_reason_name(result.estimate.reason);
}

static void report_profile(void) {
    char line[384];
    int n = snprintf(line, sizeof line,
        "PROFILE {\"seq\":%" PRIu32 ",\"forward_fft_us\":%" PRIu32 ",\"whitening_us\":%" PRIu32
        ",\"inverse_fft_us\":%" PRIu32 ",\"envelope_peaks_us\":%" PRIu32 ",\"arrival_fit_us\":%" PRIu32
        ",\"dsp_wall_us\":%" PRIu32 "}\n",
        result.sequence, result.profile.forward_fft_us, result.profile.whitening_us,
        result.profile.inverse_fft_us, result.profile.envelope_peaks_us, result.profile.arrival_fit_us, result.dsp_us);
    if (n > 0 && (size_t)n < sizeof line) usb_line(line);
}

static void report_result(uint32_t age_ms) {
    char line[1024];
    float angle = isfinite(result.estimate.angle_deg) ? result.estimate.angle_deg : 0.f;
    float quality = isfinite(result.estimate.quality) ? result.estimate.quality : 0.f;
    int n = snprintf(line, sizeof line,
        "GAP {\"firmware\":\"v0.2-link_diag\",\"backend\":\"" GAP_BACKEND_LABEL "\",\"seq\":%" PRIu32 ",\"valid\":%d,\"fit_valid\":%d,\"confirmed\":%d,\"angle_deg\":%.2f,\"quality\":%.3f,\"code_channels\":%u,"
        "\"capture_us\":%" PRIu32 ",\"capture_wait_us\":%" PRIu32 ",\"unpack_total_us\":%" PRIu32 ",\"max_block_us\":%" PRIu32
        ",\"dsp_us\":%" PRIu32 ",\"dsp_wall_us\":%" PRIu32 ",\"cycle_us\":%" PRIu32 ",\"result_interval_us\":%" PRIu32
        ",\"age_ms\":%" PRIu32 ",\"reason\":\"%s\","
        "\"uart_ready\":%d,\"uart_seq\":%" PRIu32 ",\"tx_result_seq\":%" PRIu32 ",\"tx_age_ms\":%" PRIu32
        ",\"tx_valid\":%" PRIu32 ",\"tx_angle_cdeg\":%" PRIu32 ",\"tx_quality\":%" PRIu32
        ",\"ack_seq\":%" PRIu32 ",\"ack_roundtrip_us\":%" PRIu32 ",\"ack_status\":%" PRIu32
        ",\"dma_drop\":%" PRIu32 ",\"usb_drop\":%" PRIu32 "}\n",
        result.sequence, result_valid(age_ms), result.estimate.valid != 0, result.confirmed, angle, quality, (unsigned)result.estimate.code_channels,
        result.capture_us, result.capture_wait_us, result.unpack_total_us, result.max_block_us,
        result.dsp_us, result.dsp_us, result.cycle_us, result.result_interval_us, age_ms, result_reason(age_ms), uart_ready, last_bearing_sequence,
        tx_result_seq, tx_age_ms, tx_valid, tx_angle_cdeg, tx_quality,
        ack_seq, ack_roundtrip_us, ack_status, capture_drop_count, usb_drops);
    if (n > 0 && (size_t)n < sizeof line && usb_line(line)) report_profile();
}

static void send_pending_result(void) {
    if (!result.pending || !uart_ready || !uart_idle()) return;
    char payload[112], frame[SL_FRAME_MAX];
    /* A stale/unconfirmed fit is diagnostic data, never a valid control target.
     * Invalid capture, no fit or nonfinite fields must still transmit zeroes. */
    bool diagnostic_fit = !result.override_reason && result.estimate.valid &&
        isfinite(result.estimate.angle_deg) && isfinite(result.estimate.quality);
    float angle = diagnostic_fit ? result.estimate.angle_deg : 0.f;
    if (angle < 0.f || angle >= 360.f) angle = fmodf(angle, 360.f);
    if (angle < 0.f) angle += 360.f;
    uint32_t angle_cdeg = (uint32_t)(angle * 100.f + 0.5f) % 36000u;
    float quality = diagnostic_fit ? result.estimate.quality : 0.f;
    if (quality < 0.f) quality = 0.f;
    if (quality > 1.f) quality = 1.f;
    uint32_t q = (uint32_t)(quality * 1000.f + 0.5f);
    uint32_t sequence = uart_sequence + 1u;
    for (unsigned attempt = 0; attempt < 3; ++attempt) {
        uint32_t age = sl_measurement_age_ms(result.end_us, time_us_64());
        bool valid = result_valid(age);
        uint32_t encoded_age = age > 60000u ? 60000u : age;
        snprintf(payload, sizeof payload, "B,1,%08" PRIX32 ",%" PRIu32 ",%" PRIu32 ",%d,%" PRIu32 ",%" PRIu32,
            session, sequence, encoded_age, valid, angle_cdeg, q);
        size_t length = sl_encode(frame, sizeof frame, payload);
        /* Re-encode if formatting crossed an age-ms boundary. There is no
         * queued old bearing ahead of this one; uart_send starts immediately. */
        if (sl_measurement_age_ms(result.end_us, time_us_64()) != age) continue;
        uint64_t started_us;
        if (uart_send(frame, length, &started_us)) {
            uart_sequence = last_bearing_sequence = sequence;
            tx_result_seq = result.sequence;
            tx_age_ms = encoded_age;
            tx_valid = valid;
            tx_angle_cdeg = angle_cdeg;
            tx_quality = q;
            bearing_tx_started_us = started_us;
            bearing_ack_pending = true;
            result.pending = false;
        }
        return;
    }
}

static void invalid_result(const char *reason) {
    memset(&result, 0, sizeof result);
    result.sequence = ++result_sequence;
    result.end_us = time_us_64();
    result.unpack_total_us = window_unpack_us;
    result.max_block_us = window_max_unpack_us;
    result.cycle_us = (uint32_t)(result.end_us - window_requested_us);
    result.result_interval_us = last_result_ready_us ? (uint32_t)(result.end_us - last_result_ready_us) : 0;
    last_result_ready_us = result.end_us;
    result.override_reason = reason;
    result.pending = true;
    sl_confirmation_reset(&confirmation);
    gap_reset();
    send_pending_result();
    report_result(sl_measurement_age_ms(result.end_us, time_us_64()));
}

static void complete_window(uint64_t end_us) {
    uint32_t irq_state = save_and_disable_interrupts();
    window_active = false;
    block_ready[0] = block_ready[1] = false;
    restore_interrupts(irq_state);
    memset(&result, 0, sizeof result);
    result.sequence = ++result_sequence;
    result.end_us = end_us;
    result.capture_us = (uint32_t)(end_us - first_block_start_us);
    result.capture_wait_us = (uint32_t)(end_us - window_requested_us);
    result.unpack_total_us = window_unpack_us;
    result.max_block_us = window_max_unpack_us;
    uint64_t dsp_start = time_us_64();
    gap_estimate((const int16_t (*)[MIC_COUNT])pcm, &result.estimate);
    result.dsp_us = (uint32_t)(time_us_64() - dsp_start);
    result.profile = *gap_get_profile();
    uint64_t ready_us = time_us_64();
    result.cycle_us = (uint32_t)(ready_us - window_requested_us);
    result.result_interval_us = last_result_ready_us ? (uint32_t)(ready_us - last_result_ready_us) : 0;
    last_result_ready_us = ready_us;
    if (result.estimate.reason == GAP_CLIPPING) {
        sl_confirmation_reset(&confirmation);
        gap_reset();
    }
    uint64_t center = end_us >= 42667u ? end_us - 42667u : 0;
    result.confirmed = sl_confirm(&confirmation, center, result.estimate.code_channels >= 4 && result.estimate.reason != GAP_CLIPPING);
    result.pending = true;
    uart_poll(); // ACK reception progressed in IRQ throughout DSP.
    send_pending_result();
    report_result(sl_measurement_age_ms(result.end_us, time_us_64()));
    begin_window(0);
}

static void capture_poll(void) {
    if (!capture_running || !window_active) return;
    if (capture_fault || (capture_pio->fdebug & (1u << capture_sm))) {
        invalid_result("capture_loss");
        capture_pio->fdebug = 1u << capture_sm;
        begin_window(0);
        return;
    }
    if (time_us_64() - window_requested_us > 1000000u) {
        capture_stop();
        invalid_result("capture_timeout");
        capture_start();
        return;
    }
    for (int i = 0; i < 2; ++i) {
        uint32_t irq_state = save_and_disable_interrupts();
        bool take = block_ready[i] && !dma_channel_is_busy(dma_channels[i]);
        uint32_t seq = block_sequence[i];
        uint64_t end = block_end_us[i];
        if (take) { block_ready[i] = false; processing_buffer = i; processing_corrupted = false; }
        restore_interrupts(irq_state);
        if (!take) continue;
        if (pcm_frames && seq != previous_block_sequence + 1u) {
            processing_buffer = -1;
            invalid_result("capture_loss");
            begin_window(0);
            return;
        }
        uint64_t unpack_start_us = time_us_64();
        unpack_block(i);
        uint32_t unpack_elapsed_us = (uint32_t)(time_us_64() - unpack_start_us);
        window_unpack_us += unpack_elapsed_us;
        if (unpack_elapsed_us > window_max_unpack_us) window_max_unpack_us = unpack_elapsed_us;
        irq_state = save_and_disable_interrupts();
        bool valid = !processing_corrupted && !capture_fault && !dma_channel_is_busy(dma_channels[i]);
        processing_buffer = -1;
        restore_interrupts(irq_state);
        if (!valid) { invalid_result("capture_loss"); begin_window(0); return; }
        if (!pcm_frames) first_block_start_us = end - 10667u;
        previous_block_sequence = seq;
        pcm_frames += CAPTURE_BLOCK_FRAMES;
        if (pcm_frames == WINDOW_FRAMES) { complete_window(end); return; }
    }
}

static void report_status(void) {
    char line[384];
    snprintf(line, sizeof line,
        "STATUS {\"running\":%d,\"session\":\"%08" PRIX32 "\",\"uart_ready\":%d,\"acks\":%" PRIu32
        ",\"ack_bad\":%" PRIu32 ",\"rx_drop\":%" PRIu32 ",\"uart_error\":%" PRIu32
        ",\"dma_drop\":%" PRIu32 ",\"usb_drop\":%" PRIu32 ",\"seq\":%" PRIu32 "}\n",
        capture_running, session, uart_ready, ack_count, ack_bad, rx_byte_drops, uart_errors,
        capture_drop_count, usb_drops, result_sequence);
    usb_line(line);
}

static void usb_poll(void) {
    static bool banner_sent;
    static char command[32];
    static size_t used;
    static bool discard;
    if (!tud_cdc_connected()) { banner_sent = false; used = 0; discard = false; return; }
    if (!banner_sent)
        banner_sent = usb_line("PICO_GAP_STANDALONE v0.2-link_diag backend=" GAP_BACKEND_LABEL " fs=48000 channels=7 window=4096 dma=512 UART0=GP0_TX_GP1_RX_115200 auto_scan no_motor\n");
    char bytes[64];
    uint32_t irq_state = save_and_disable_interrupts();
    uint32_t count = tud_cdc_read(bytes, sizeof bytes);
    restore_interrupts(irq_state);
    for (uint32_t i = 0; i < count; ++i) {
        char c = bytes[i];
        if (c == '\r' || c == '\n') {
            if (discard && c != '\n') continue;
            if (!discard && used) {
                command[used] = 0;
                if (!strcmp(command, "STOP")) { capture_stop(); invalid_result("stopped"); }
                else if (!strcmp(command, "START")) {
                    if (!capture_running) { sl_confirmation_reset(&confirmation); gap_reset(); capture_start(); }
                    report_status();
                } else if (!strcmp(command, "STATUS")) report_status();
                else usb_line("COMMAND_ERROR expected_START_STOP_STATUS\n");
            } else if (discard) usb_line("COMMAND_ERROR discarded_line\n");
            used = 0; discard = false;
        } else if (!discard) {
            if (c < 32 || c >= 127 || used + 1 >= sizeof command) { discard = true; used = 0; }
            else command[used++] = c;
        }
    }
}

int main(void) {
    set_sys_clock_khz(120000, true);
    for (unsigned pin = LED_CLK; pin <= LED_DATA; ++pin) {
        gpio_init(pin); gpio_put(pin, 0); gpio_set_dir(pin, GPIO_OUT);
    }
    led_ring_off();
    for (unsigned pin = DATA_BASE; pin < DATA_BASE + 4; ++pin) {
        pio_gpio_init(capture_pio, pin); gpio_pull_down(pin);
    }
    for (unsigned pin = BCLK_PIN; pin <= WS_PIN; ++pin) pio_gpio_init(capture_pio, pin);
    capture_sm = pio_claim_unused_sm(capture_pio, true);
    capture_offset = pio_add_program(capture_pio, &sen0325_i2s_program);
    pio_sm_config config = sen0325_i2s_program_get_default_config(capture_offset);
    sm_config_set_in_pins(&config, DATA_BASE);
    sm_config_set_sideset_pins(&config, BCLK_PIN);
    sm_config_set_in_shift(&config, false, true, 32);
    sm_config_set_fifo_join(&config, PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&config, (float)clock_get_hz(clk_sys) / (SAMPLE_RATE * 128.0f));
    pio_sm_set_consecutive_pindirs(capture_pio, capture_sm, DATA_BASE, 4, false);
    pio_sm_set_consecutive_pindirs(capture_pio, capture_sm, BCLK_PIN, 2, true);
    pio_sm_init(capture_pio, capture_sm, capture_offset, &config);
    pio_sm_set_pins_with_mask(capture_pio, capture_sm, 0, (1u << BCLK_PIN) | (1u << WS_PIN));
    dma_channels[0] = dma_claim_unused_channel(true);
    dma_channels[1] = dma_claim_unused_channel(true);
    irq_set_exclusive_handler(DMA_IRQ_0, capture_irq);
    irq_set_priority(DMA_IRQ_0, PICO_HIGHEST_IRQ_PRIORITY);
    irq_set_enabled(DMA_IRQ_0, true);
    stdio_init_all(); // USB initialization does not wait for a connected host.
    link_init();
    gap_set_clock_us(time_us_32);
    gap_reset();
    capture_start();
    while (true) {
        uart_poll();
        usb_poll();
        send_pending_result();
        capture_poll();
        sleep_us(50);
    }
}
