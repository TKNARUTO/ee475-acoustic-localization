#ifndef EE475_GAP_DSP_H
#define EE475_GAP_DSP_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum { GAP_FRAMES = 4096, GAP_CHANNELS = 7, GAP_SAMPLE_RATE = 48000 };
enum gap_reason {
    GAP_ESTIMATED = 0,
    GAP_BEACON_NOT_DETECTED = 1,
    GAP_INSUFFICIENT_ARRIVAL_CHANNELS = 2,
    GAP_NO_CONSISTENT_ARRIVAL = 3,
    GAP_CLIPPING = 4,
    GAP_PEAK_OVERFLOW = 5
};

typedef struct {
    int valid, reason, code_channels;
    float angle_deg, quality, rms_samples, projection;
    float pnr_db[GAP_CHANNELS], arrival_samples[GAP_CHANNELS];
} gap_result_t;

typedef struct {
    uint32_t forward_fft_us, whitening_us, inverse_fft_us;
    uint32_t envelope_peaks_us, arrival_fit_us;
} gap_profile_t;

/* Single caller; no allocation, SDK, clock, UART, historical angle or gain state.
 * Input order: D0L,D0R,D1L,D1R,D2L,D2R,D3R_CENTER, signed 16-bit PCM.
 * valid is a current-window geometric fit. Caller owns capture health, actual
 * sample age and the two-code-hit confirmation policy. No held angle is output.
 * arrival_samples are selected matched-envelope peaks relative to this frame's
 * common arrival center; NAN means no selected/retained peak for that channel.
 */
void gap_estimate(const int16_t audio[GAP_FRAMES][GAP_CHANNELS], gap_result_t *out);
void gap_reset(void);
const char *gap_reason_name(int reason);
size_t gap_workspace_bytes(void);
const char *gap_fft_backend_name(void);
/* Optional caller-supplied microsecond clock. NULL disables timing. The clock
 * can wrap uint32_t; each phase must last less than one full wrap. Counters are
 * reset per gap_estimate and accumulate all seven channels. Not reentrant.
 * Input checks/FFT input loading/caller confirmation are outside these phases.
 */
void gap_set_clock_us(uint32_t (*clock_us)(void));
const gap_profile_t *gap_get_profile(void);

#ifdef __cplusplus
}
#endif
#endif
