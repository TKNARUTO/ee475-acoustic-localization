#ifndef EE475_GAP_INTEGER_FFT_H
#define EE475_GAP_INTEGER_FFT_H
/* Optional bounded integer FFT kernel, derived from the separately tested
 * experiments/integer_fft implementation. Input uses one block exponent and
 * each of 12 radix-2 stages divides by two. Float conversion and restoration
 * occur at the backend boundary in gap_dsp.c, not within butterflies.
 * No 64-bit multiplication. The portable path avoids signed negative shifts;
 * the optional fast path requires a compile-checked arithmetic right shift.
 */
#include <stdint.h>
#include "gap_integer_tables.h"
#ifndef GAP_INTEGER_FAST
#define GAP_INTEGER_FAST 0
#endif
typedef struct { int32_t re, im; } GapIntegerComplex;

#if GAP_INTEGER_FAST
/* Supported ARM GCC/Cygwin GCC targets implement sign-propagating right shift.
 * An unsupported compiler must use GAP_INTEGER_FAST=0, the portable path.
 */
typedef char gap_arithmetic_right_shift_required[((-1 >> 1) == -1) ? 1 : -1];
#endif

static inline int32_t gap_integer_half(int32_t value) {
#if GAP_INTEGER_FAST
    return value >> 1;
#else
    int32_t quotient = value / 2;
    return quotient - (value < 0 && value % 2 != 0);
#endif
}

static inline int32_t gap_integer_multiply_q15(int32_t value, int32_t twiddle) {
#if GAP_INTEGER_FAST
    int32_t hi = value >> 15;
    int32_t lo = (int32_t)((uint32_t)value & 32767u);
    int32_t product = lo * twiddle;
    return hi * twiddle + (product >> 15);
#else
    int32_t hi, lo, product, fraction;
    if (twiddle == 32768) return value;
    if (twiddle == -32768) return -value;
    if (twiddle == 0) return 0;
    hi = value / 32768;
    lo = value % 32768;
    if (lo < 0) { lo += 32768; --hi; }
    product = lo * twiddle;
    fraction = product / 32768;
    if (product < 0 && product % 32768 != 0) --fraction;
    return hi * twiddle + fraction;
#endif
}

static void gap_integer_transform(GapIntegerComplex data[4096], int inverse) {
    unsigned i, j = 0, length;
    for (i = 1; i < 4096u; ++i) {
        unsigned bit = 2048u;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) { GapIntegerComplex swap = data[i]; data[i] = data[j]; data[j] = swap; }
    }
    for (length = 2; length <= 4096u; length <<= 1) {
        unsigned half = length >> 1, step = 4096u / length;
        for (j = 0; j < half; ++j) {
            unsigned phase = j * step;
            int32_t cosine = phase <= 1024u ? gap_q15_quarter_sine[1024u-phase] : -gap_q15_quarter_sine[phase-1024u];
            int32_t sine = phase <= 1024u ? gap_q15_quarter_sine[phase] : gap_q15_quarter_sine[2048u-phase];
            if (!inverse) sine = -sine;
            for (i = j; i < 4096u; i += length) {
                GapIntegerComplex a = data[i], b = data[i + half];
                int32_t re = gap_integer_multiply_q15(b.re, cosine) - gap_integer_multiply_q15(b.im, sine);
                int32_t im = gap_integer_multiply_q15(b.re, sine) + gap_integer_multiply_q15(b.im, cosine);
                data[i].re = gap_integer_half(a.re + re);
                data[i].im = gap_integer_half(a.im + im);
                data[i + half].re = gap_integer_half(a.re - re);
                data[i + half].im = gap_integer_half(a.im - im);
            }
        }
    }
}
#endif
