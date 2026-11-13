#ifndef EE475_TONE_FILTER_H
#define EE475_TONE_FILTER_H
#include <math.h>
#include <stdbool.h>
#include <stdint.h>

enum { TONE_N = 1024, TONE_FS = 48000, TONE_SCALE = 63 };
typedef struct { int32_t re[3], im[3]; } tone_accumulator;
static int8_t tone_cos[3][TONE_N], tone_sin[3][TONE_N];
static int32_t tone_cos_sum[3], tone_sin_sum[3];
static unsigned tone_frequency = 1000;

// Configuration is done with acquisition stopped. The sample loop then uses
// three narrowband pairs of bounded integer multiply-accumulates per sample.
static bool tone_configure(unsigned frequency) {
    if (frequency < 300 || frequency > 22000) return false;
    const unsigned frequencies[3] = {frequency,frequency-150,frequency+150};
    for (unsigned band=0;band<3;++band) {
        tone_cos_sum[band] = tone_sin_sum[band] = 0;
        for (unsigned i = 0; i < TONE_N; ++i) {
            double phase = 6.283185307179586 * frequencies[band] * i / TONE_FS;
            tone_cos[band][i] = (int8_t)lround(TONE_SCALE * cos(phase));
            tone_sin[band][i] = (int8_t)lround(TONE_SCALE * sin(phase));
            tone_cos_sum[band] += tone_cos[band][i];
            tone_sin_sum[band] += tone_sin[band][i];
        }
    }
    tone_frequency = frequency;
    return true;
}

static inline void tone_push(tone_accumulator *state, int32_t sample, unsigned frame) {
    // Absolute bound: 32768 * 63 * 1024 = 2113929216 < INT32_MAX.
    for(unsigned band=0;band<3;++band) {
        state->re[band] += sample * tone_cos[band][frame];
        state->im[band] += sample * tone_sin[band][frame];
    }
}

static float tone_band_power(const tone_accumulator *state, int64_t sample_sum, unsigned band) {
    float mean = (float)sample_sum / TONE_N;
    float re = state->re[band] - mean * tone_cos_sum[band];
    float im = state->im[band] - mean * tone_sin_sum[band];
    return 2.0f * (re * re + im * im) / ((float)TONE_N * TONE_N * TONE_SCALE * TONE_SCALE);
}

static float tone_power(const tone_accumulator *state, int64_t sum) {return tone_band_power(state,sum,0);}
static void tone_complex(const tone_accumulator *state, int64_t sum, float *re, float *im) {
    float mean=(float)sum/TONE_N;
    const float scale=1.0f/(TONE_N*TONE_SCALE);
    *re=(state->re[0]-mean*tone_cos_sum[0])*scale;
    *im=(state->im[0]-mean*tone_sin_sum[0])*scale;
}
static float tone_reference_power(const tone_accumulator *state, int64_t sum) {
    return (tone_band_power(state,sum,1)+tone_band_power(state,sum,2))*0.5f;
}
static bool tone_is_present(float power, float reference_power, uint32_t clips) {
    return !clips && power >= 16.0f * 16.0f && power >= 6.31f * fmaxf(reference_power,0.01f);
}
#endif
