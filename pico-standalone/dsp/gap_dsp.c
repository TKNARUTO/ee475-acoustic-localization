/* HF2 Gap portable C prototype: matched envelope + arrival consensus.
 * This deliberately omits spectral-delay/joint-search rescue. It does not
 * change the phone code, sample rate, microphone mapping or prior-angle rules.
 * The float implementation must be timed on RP2040 before rate claims.
 */
#include "gap_dsp.h"
#include "gap_tables.h"
#include <math.h>
#include <string.h>

#ifndef GAP_INTEGER_FFT
#define GAP_INTEGER_FFT 0
#endif
#ifndef GAP_INTEGER_FAST
#define GAP_INTEGER_FAST 0
#endif
#ifndef GAP_WHITEN_FLOAT
#define GAP_WHITEN_FLOAT 0
#endif
#ifndef GAP_MAG_CACHE
#define GAP_MAG_CACHE 0
#endif
#if GAP_INTEGER_FFT
#include "gap_integer_fft.h"
#if GAP_INTEGER_FAST
#include "gap_fast_float.h"
#endif
#endif

enum { MAX_PEAKS = 96 };
typedef struct { float re, im; } Complex;
typedef struct { float sample, strength; } Peak;
typedef struct {
#if GAP_INTEGER_FFT
    union {
        Complex floating[GAP_FRAMES];
        GapIntegerComplex integer[GAP_FRAMES];
    } transform;
#else
    Complex fft[GAP_FRAMES];
#endif
    float common[GAP_FRAMES];
    float median_buffer[GAP_BAND_BINS];
    Peak peaks[GAP_CHANNELS][MAX_PEAKS];
    unsigned short peak_count[GAP_CHANNELS];
    unsigned char present[GAP_CHANNELS];
} Workspace;
static Workspace work;
#if GAP_INTEGER_FFT
#define FFT_VALUES (work.transform.floating)
#else
#define FFT_VALUES (work.fft)
#endif
static gap_profile_t profile;
static uint32_t (*clock_us_fn)(void);
typedef char workspace_limit[((sizeof work + sizeof profile + sizeof clock_us_fn) <= 56u * 1024u) ? 1 : -1];

static uint32_t clock_now(void) { return clock_us_fn ? clock_us_fn() : 0u; }

/* Coordinates in sample units: position_m * 48000 / 343.
 * x=right, y=U7/M0. Positive bearing is clockwise from y.
 */
static const float geometry[GAP_CHANNELS][2] = {
    {0.0f, 5.597667638f}, {4.847722375f, 2.798833819f},
    {4.847722375f, -2.798833819f}, {0.0f, -5.597667638f},
    {-4.847722375f, -2.798833819f}, {-4.847722375f, 2.798833819f},
    {0.0f, 0.0f}
};

static float minimum(float a, float b) { return a < b ? a : b; }
static float maximum(float a, float b) { return a > b ? a : b; }
static float clip(float a, float low, float high) { return minimum(high, maximum(low, a)); }

static inline float whitening_gain(float reference, float magnitude) {
    float ratio = reference / maximum(magnitude, reference * 0.12f);
#if GAP_WHITEN_FLOAT
    /* The bounded detector ratio is positive and finite. This replaces the
     * SDK powf general path's double log/exp with float logf/expf, preserving
     * the same exponent and clamps. It is a tested numerical approximation,
     * not an assertion of bit-identical libm results.
     */
    float gain = expf(0.65f * logf(ratio));
#else
    float gain = powf(ratio, 0.65f);
#endif
    return clip(gain, 0.025f, 3.0f);
}

/* Sorting only the 342-value scratch median, never input audio or FFT bins. */
static void sift_down(float *a, unsigned root, unsigned count) {
    for (;;) {
        unsigned child = root * 2u + 1u;
        float swap;
        if (child >= count) return;
        if (child + 1u < count && a[child] < a[child + 1u]) ++child;
        if (a[root] >= a[child]) return;
        swap = a[root]; a[root] = a[child]; a[child] = swap; root = child;
    }
}
static float median(float *a, unsigned count) {
    unsigned end, start;
    if (!count) return 0.0f;
    for (start = count / 2u; start > 0; --start) sift_down(a, start - 1u, count);
    for (end = count; end > 1u; --end) {
        float swap = a[0]; a[0] = a[end - 1u]; a[end - 1u] = swap;
        sift_down(a, 0, end - 1u);
    }
    return count & 1u ? a[count / 2u] : 0.5f * (a[count / 2u - 1u] + a[count / 2u]);
}

static void fft(int inverse) {
#if GAP_INTEGER_FFT
    unsigned i;
    float max_coordinate = 0.0f;
    int exponent = 0, input_shift, restore_exponent;
    for (i = 0; i < GAP_FRAMES; ++i) {
        float real = fabsf(FFT_VALUES[i].re), imag = fabsf(FFT_VALUES[i].im);
        if (real > max_coordinate) max_coordinate = real;
        if (imag > max_coordinate) max_coordinate = imag;
    }
    if (max_coordinate > 0.0f) (void)frexpf(max_coordinate, &exponent);
    input_shift = max_coordinate > 0.0f ? 27 - exponent : 0;
    restore_exponent = (inverse ? 0 : 12) - input_shift;
    /* Each integer coordinate starts below 2^27. Rounded Q15 rotations and
     * per-stage /2 keep intermediate sums below 2^29. The low-word product
     * stays below 2^30. Read both float members before overwriting union bytes.
     */
    for (i = 0; i < GAP_FRAMES; ++i) {
        Complex value = FFT_VALUES[i];
        GapIntegerComplex converted;
#if GAP_INTEGER_FAST
        converted.re = gap_fast_round_scaled(value.re, input_shift);
        converted.im = gap_fast_round_scaled(value.im, input_shift);
#else
        converted.re = (int32_t)roundf(ldexpf(value.re, input_shift));
        converted.im = (int32_t)roundf(ldexpf(value.im, input_shift));
#endif
        work.transform.integer[i] = converted;
    }
    gap_integer_transform(work.transform.integer, inverse);
    for (i = 0; i < GAP_FRAMES; ++i) {
        GapIntegerComplex value = work.transform.integer[i];
        Complex converted;
#if GAP_INTEGER_FAST
        converted.re = gap_fast_ldexp((float)value.re, restore_exponent);
        converted.im = gap_fast_ldexp((float)value.im, restore_exponent);
#else
        converted.re = ldexpf((float)value.re, restore_exponent);
        converted.im = ldexpf((float)value.im, restore_exponent);
#endif
        FFT_VALUES[i] = converted;
    }
#else
    unsigned i, j = 0, length;
    for (i = 1; i < GAP_FRAMES; ++i) {
        unsigned bit = GAP_FRAMES >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
            Complex swap = FFT_VALUES[i]; FFT_VALUES[i] = FFT_VALUES[j]; FFT_VALUES[j] = swap;
        }
    }
    for (length = 2; length <= GAP_FRAMES; length <<= 1) {
        unsigned half = length >> 1, step = GAP_FRAMES / length;
        for (j = 0; j < half; ++j) {
            unsigned phase = j * step;
            float cosine = phase <= 1024u ? gap_quarter_sine[1024u-phase] : -gap_quarter_sine[phase-1024u];
            float sine = phase <= 1024u ? gap_quarter_sine[phase] : gap_quarter_sine[2048u-phase];
            if (!inverse) sine = -sine;
            for (i = j; i < GAP_FRAMES; i += length) {
                Complex a = FFT_VALUES[i], b = FFT_VALUES[i + half];
                float real = b.re * cosine - b.im * sine;
                float imag = b.re * sine + b.im * cosine;
                FFT_VALUES[i].re = a.re + real;
                FFT_VALUES[i].im = a.im + imag;
                FFT_VALUES[i + half].re = a.re - real;
                FFT_VALUES[i + half].im = a.im - imag;
            }
        }
    }
    if (inverse) for (i = 0; i < GAP_FRAMES; ++i) {
        FFT_VALUES[i].re *= 1.0f / 4096.0f;
        FFT_VALUES[i].im *= 1.0f / 4096.0f;
    }
#endif
}

/* Returns false only when the bounded candidate list overflowed. Overflow is
 * explicit invalid data, never silent pruning of an inconvenient direction.
 */
static int match_channel(const int16_t audio[GAP_FRAMES][GAP_CHANNELS], unsigned ch, gap_result_t *out) {
    unsigned i, peak = 0;
    int32_t sum = 0;
    float mean, energy = 0.0f, reference, rms, peak_value = 0.0f, noise_energy = 0.0f, pnr;
    unsigned noise_count = 0;
    uint32_t phase_started;
    for (i = 0; i < GAP_FRAMES; ++i) sum += audio[i][ch];
    mean = (float)sum * (1.0f / 4096.0f);
    for (i = 0; i < GAP_FRAMES; ++i) {
        FFT_VALUES[i].re = (float)audio[i][ch] - mean;
        FFT_VALUES[i].im = 0.0f;
    }
    phase_started = clock_now();
    fft(0);
    profile.forward_fft_us += clock_now() - phase_started;
    phase_started = clock_now();
    for (i = 0; i < GAP_BAND_BINS; ++i) {
        Complex value = FFT_VALUES[GAP_FIRST_BIN + i];
        float square = value.re * value.re + value.im * value.im;
        energy += square;
        work.median_buffer[i] = sqrtf(square);
#if GAP_MAG_CACHE
        /* Bins 0..341 are outside target bins 1536..1877 and will be cleared
         * before IFFT. Their real components provide a zero-extra-RAM cache.
         */
        FFT_VALUES[i].re = work.median_buffer[i];
#endif
    }
    rms = sqrtf(2.0f * energy) * (1.0f / 4096.0f);
    reference = maximum(median(work.median_buffer, GAP_BAND_BINS), 1e-9f);
#if GAP_MAG_CACHE
    for (i = 0; i < GAP_BAND_BINS; ++i) {
        Complex value = FFT_VALUES[GAP_FIRST_BIN + i];
        float whitening = whitening_gain(reference, FFT_VALUES[i].re);
        FFT_VALUES[GAP_FIRST_BIN + i].re = (value.re * gap_reference_real[i] + value.im * gap_reference_imag[i]) * whitening;
        FFT_VALUES[GAP_FIRST_BIN + i].im = (value.im * gap_reference_real[i] - value.re * gap_reference_imag[i]) * whitening;
    }
    memset(FFT_VALUES, 0, GAP_FIRST_BIN * sizeof(Complex));
    memset(FFT_VALUES + GAP_FIRST_BIN + GAP_BAND_BINS, 0,
           (GAP_FRAMES - GAP_FIRST_BIN - GAP_BAND_BINS) * sizeof(Complex));
#else
    for (i = 0; i < GAP_FRAMES; ++i) {
        if (i >= GAP_FIRST_BIN && i < GAP_FIRST_BIN + GAP_BAND_BINS) {
            unsigned k = i - GAP_FIRST_BIN;
            Complex value = FFT_VALUES[i];
            float magnitude = sqrtf(value.re * value.re + value.im * value.im);
            float whitening = whitening_gain(reference, magnitude);
            /* X * conjugate(reference), retaining only positive bins. */
            FFT_VALUES[i].re = (value.re * gap_reference_real[k] + value.im * gap_reference_imag[k]) * whitening;
            FFT_VALUES[i].im = (value.im * gap_reference_real[k] - value.re * gap_reference_imag[k]) * whitening;
        } else {
            FFT_VALUES[i].re = 0.0f;
            FFT_VALUES[i].im = 0.0f;
        }
    }
#endif
    profile.whitening_us += clock_now() - phase_started;
    phase_started = clock_now();
    fft(1);
    profile.inverse_fft_us += clock_now() - phase_started;
    phase_started = clock_now();
    /* Reuse real components to hold the full envelope for this channel. */
    for (i = 0; i < GAP_FRAMES; ++i) {
        Complex value = FFT_VALUES[i];
        float envelope = sqrtf(value.re * value.re + value.im * value.im);
        FFT_VALUES[i].re = envelope;
        if (envelope > peak_value) { peak_value = envelope; peak = i; }
    }
    for (i = 0; i < GAP_FRAMES; ++i) {
        unsigned distance = i > peak ? i - peak : peak - i;
        if (distance > GAP_FRAMES / 2u) distance = GAP_FRAMES - distance;
        if (distance > 24u) {
            noise_energy += FFT_VALUES[i].re * FFT_VALUES[i].re;
            ++noise_count;
        }
    }
    /* Python width=max(16, round(2*48000/4000)) = 24 samples. */
    pnr = 20.0f * log10f(maximum(peak_value, 1e-12f) /
                         maximum(sqrtf(noise_energy / (float)noise_count), 1e-12f));
    out->pnr_db[ch] = pnr;
    if (!(pnr >= 12.5f && rms >= 0.25f)) {
        profile.envelope_peaks_us += clock_now() - phase_started;
        return 1;
    }
    work.present[ch] = 1;
    ++out->code_channels;
    for (i = 0; i < GAP_FRAMES; ++i) {
        float value = FFT_VALUES[i].re / maximum(peak_value, 1e-12f);
        FFT_VALUES[i].re = value;
        work.common[i] += value;
    }
    for (i = 0; i < GAP_FRAMES; ++i) {
        float left = FFT_VALUES[(i - 1u) & (GAP_FRAMES - 1u)].re;
        float value = FFT_VALUES[i].re;
        float right = FFT_VALUES[(i + 1u) & (GAP_FRAMES - 1u)].re;
        if (value > left && value >= right && value >= 0.45f) {
            float a = logf(maximum(left, 1e-12f)), b = logf(maximum(value, 1e-12f));
            float c = logf(maximum(right, 1e-12f)), curvature = a - 2.0f * b + c;
            float offset = fabsf(curvature) > 1e-12f ? clip(0.5f * (a-c) / curvature, -0.5f, 0.5f) : 0.0f;
            unsigned count = work.peak_count[ch];
            if (count == MAX_PEAKS) {
                profile.envelope_peaks_us += clock_now() - phase_started;
                return 0;
            }
            work.peaks[ch][count].sample = (float)i + offset;
            work.peaks[ch][count].strength = value;
            work.peak_count[ch] = (unsigned short)(count + 1u);
        }
    }
    profile.envelope_peaks_us += clock_now() - phase_started;
    return 1;
}

typedef struct {
    int found, support;
    float angle, quality, rms, projection, center;
    float arrivals[GAP_CHANNELS];
} Fit;

static int solve3(float a[3][4], float solution[3]) {
    unsigned col, row, k;
    for (col = 0; col < 3; ++col) {
        unsigned pivot = col;
        for (row = col + 1; row < 3; ++row)
            if (fabsf(a[row][col]) > fabsf(a[pivot][col])) pivot = row;
        if (fabsf(a[pivot][col]) < 1e-6f) return 0;
        if (pivot != col) for (k = col; k < 4; ++k) {
            float swap = a[col][k]; a[col][k] = a[pivot][k]; a[pivot][k] = swap;
        }
        for (row = col + 1; row < 3; ++row) {
            float factor = a[row][col] / a[col][col];
            for (k = col; k < 4; ++k) a[row][k] -= factor * a[col][k];
        }
    }
    for (col = 3; col > 0; --col) {
        row = col - 1;
        float value = a[row][3];
        for (k = row + 1; k < 3; ++k) value -= a[row][k] * solution[k];
        solution[row] = value / a[row][row];
    }
    return 1;
}

static int fit_origin(float origin, Fit *result) {
    int selected[GAP_CHANNELS], keep[GAP_CHANNELS];
    unsigned ch, count = 0, attempt;
    float residual[GAP_CHANNELS], solution[3] = {0.0f,0.0f,0.0f};
    const float span = 5.597667638f * 1.3f + 2.0f;
    for (ch = 0; ch < GAP_CHANNELS; ++ch) {
        unsigned p;
        float nearest = span + 1.0f;
        selected[ch] = -1; keep[ch] = 0;
        for (p = 0; p < work.peak_count[ch]; ++p) {
            float distance = fabsf(work.peaks[ch][p].sample - origin);
            if (distance <= span && distance < nearest) {
                nearest = distance; selected[ch] = (int)p;
            }
        }
        if (selected[ch] >= 0) { keep[ch] = 1; ++count; }
    }
    if (count < 5u) return 0;
    for (attempt = 0; attempt < 2; ++attempt) {
        float matrix[3][4] = {{0.0f}};
        unsigned row, col, worst = 0;
        float worst_residual = 0.0f;
        for (ch = 0; ch < GAP_CHANNELS; ++ch) if (keep[ch]) {
            Peak peak = work.peaks[ch][selected[ch]];
            float design[3] = {geometry[ch][0], geometry[ch][1], 1.0f};
            float weight = peak.strength * peak.strength;
            /* Arrival delay is NEGATIVE position dot source direction. */
            for (row = 0; row < 3; ++row) {
                for (col = 0; col < 3; ++col) matrix[row][col] += weight * design[row] * design[col];
                matrix[row][3] += weight * design[row] * -peak.sample;
            }
        }
        if (!solve3(matrix, solution)) return 0;
        for (ch = 0; ch < GAP_CHANNELS; ++ch) if (selected[ch] >= 0) {
            residual[ch] = geometry[ch][0] * solution[0] + geometry[ch][1] * solution[1] + solution[2]
                           + work.peaks[ch][selected[ch]].sample;
            if (fabsf(residual[ch]) > worst_residual) { worst_residual = fabsf(residual[ch]); worst = ch; }
        }
        if (attempt == 0u && count >= 6u && worst_residual > 1.5f) keep[worst] = 0;
        else break;
    }
    {
        unsigned support = 0;
        float kept_error = 0.0f, all_error = 0.0f, kept_weight = 0.0f, all_weight = 0.0f;
        float strengths[GAP_CHANNELS], strength, quality, rms, all_rms;
        float norm = sqrtf(solution[0] * solution[0] + solution[1] * solution[1]);
        for (ch = 0; ch < GAP_CHANNELS; ++ch) if (selected[ch] >= 0) {
            float magnitude = work.peaks[ch][selected[ch]].strength;
            float weight = magnitude * magnitude;
            float error = weight * residual[ch] * residual[ch];
            all_error += error; all_weight += weight;
            if (keep[ch]) {
                kept_error += error; kept_weight += weight;
                strengths[support++] = magnitude;
            }
        }
        if (support < 5u || norm < 0.25f || norm > 1.3f) return 0;
        rms = sqrtf(kept_error / kept_weight);
        all_rms = sqrtf(all_error / all_weight);
        strength = median(strengths, support);
        if (rms > 0.9f || all_rms > 2.0f || strength < 0.55f) return 0;
        quality = minimum(1.0f, (float)support / 6.0f) * strength * expf(-0.5f * (rms / 1.25f) * (rms / 1.25f));
        if (quality < 0.48f) return 0;
        result->found = 1;
        result->support = (int)support;
        result->angle = atan2f(solution[0], solution[1]) * 57.295779513f;
        if (result->angle < 0.0f) result->angle += 360.0f;
        if (result->angle >= 360.0f) result->angle -= 360.0f;
        result->quality = quality; result->rms = rms; result->projection = norm;
        result->center = -solution[2];
        for (ch = 0; ch < GAP_CHANNELS; ++ch)
            result->arrivals[ch] = keep[ch] ? work.peaks[ch][selected[ch]].sample : NAN;
        return 1;
    }
}

void gap_estimate(const int16_t audio[GAP_FRAMES][GAP_CHANNELS], gap_result_t *out) {
    unsigned i, ch, center = 0;
    int overflow = 0, maximum_support = 0;
    Fit best_by_support[3] = {{0}}, best = {0};
    uint32_t fit_started;
    if (!out) return;
    memset(&profile, 0, sizeof profile);
    memset(out, 0, sizeof(*out));
    out->reason = GAP_BEACON_NOT_DETECTED;
    for (ch = 0; ch < GAP_CHANNELS; ++ch) out->arrival_samples[ch] = NAN;
    if (!audio) return;
    for (i = 0; i < GAP_FRAMES; ++i) for (ch = 0; ch < GAP_CHANNELS; ++ch) {
        int value = audio[i][ch];
        if (value >= 32760 || value <= -32760) { out->reason = GAP_CLIPPING; return; }
    }
    memset(work.common, 0, sizeof work.common);
    memset(work.present, 0, sizeof work.present);
    memset(work.peak_count, 0, sizeof work.peak_count);
    for (ch = 0; ch < GAP_CHANNELS; ++ch) if (!match_channel(audio, ch, out)) overflow = 1;
    if (out->code_channels < 4) return;
    /* As in the existing arrival fallback, six code-positive microphones are
     * needed to enter this solver, which may retain five after one outlying mic.
     */
    if (out->code_channels < 6) { out->reason = GAP_INSUFFICIENT_ARRIVAL_CHANNELS; return; }
    if (overflow) { out->reason = GAP_PEAK_OVERFLOW; return; }
    fit_started = clock_now();
    for (i = 1; i < GAP_FRAMES; ++i) if (work.common[i] > work.common[center]) center = i;
    for (ch = 0; ch < GAP_CHANNELS; ++ch) {
        unsigned count = 0, p;
        for (p = 0; p < work.peak_count[ch]; ++p) {
            Peak peak = work.peaks[ch][p];
            int index = (int)floorf(peak.sample + 0.5f);
            int relative = index - (int)center;
            if (relative >= GAP_FRAMES / 2) relative -= GAP_FRAMES;
            if (relative < -GAP_FRAMES / 2) relative += GAP_FRAMES;
            if (relative >= -96 && relative <= 96) {
                peak.sample = (float)relative + (peak.sample - (float)index);
                work.peaks[ch][count++] = peak;
            }
        }
        work.peak_count[ch] = (unsigned short)count;
    }
    for (ch = 0; ch < GAP_CHANNELS; ++ch) for (i = 0; i < work.peak_count[ch]; ++i) {
        Fit candidate = {0};
        if (fit_origin(work.peaks[ch][i].sample, &candidate)) {
            Fit *slot = &best_by_support[candidate.support - 5];
            if (candidate.support > maximum_support) maximum_support = candidate.support;
            if (!slot->found || candidate.center < slot->center ||
                (candidate.center == slot->center && candidate.quality > slot->quality)) *slot = candidate;
        }
    }
    for (i = 0; i < 3; ++i) {
        Fit *candidate = &best_by_support[i];
        if (!candidate->found || candidate->support < maximum_support - 1) continue;
        if (!best.found || candidate->center < best.center ||
            (candidate->center == best.center && candidate->quality > best.quality)) best = *candidate;
    }
    profile.arrival_fit_us = clock_now() - fit_started;
    if (!best.found) { out->reason = GAP_NO_CONSISTENT_ARRIVAL; return; }
    out->valid = 1; out->reason = GAP_ESTIMATED;
    out->angle_deg = best.angle; out->quality = best.quality;
    out->rms_samples = best.rms; out->projection = best.projection;
    memcpy(out->arrival_samples, best.arrivals, sizeof out->arrival_samples);
}

void gap_reset(void) { memset(&work, 0, sizeof work); memset(&profile, 0, sizeof profile); }
size_t gap_workspace_bytes(void) { return sizeof work + sizeof profile + sizeof clock_us_fn; }
const char *gap_fft_backend_name(void) {
#if GAP_INTEGER_FFT
#if GAP_INTEGER_FAST
    return "integer_q15_bitexact_fast";
#else
    return "integer_q15_block_scaled";
#endif
#else
    return "float_baseline";
#endif
}
void gap_set_clock_us(uint32_t (*clock_us)(void)) { clock_us_fn = clock_us; }
const gap_profile_t *gap_get_profile(void) { return &profile; }
const char *gap_reason_name(int reason) {
    switch (reason) {
        case GAP_ESTIMATED: return "estimated";
        case GAP_BEACON_NOT_DETECTED: return "beacon_not_detected";
        case GAP_INSUFFICIENT_ARRIVAL_CHANNELS: return "insufficient_arrival_channels";
        case GAP_NO_CONSISTENT_ARRIVAL: return "no_consistent_arrival";
        case GAP_CLIPPING: return "clipping";
        case GAP_PEAK_OVERFLOW: return "peak_overflow";
        default: return "unknown";
    }
}
