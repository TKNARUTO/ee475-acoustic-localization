#ifndef EE475_GAP_FAST_FLOAT_H
#define EE475_GAP_FAST_FLOAT_H
/* Optional binary32 exponent adjustment. All exceptional/subnormal scaling
 * cases use the original libm functions. memcpy preserves strict aliasing.
 */
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

typedef char gap_binary32_required[(sizeof(float) == 4 && FLT_RADIX == 2 &&
    FLT_MANT_DIG == 24 && FLT_MIN_EXP == -125 && FLT_MAX_EXP == 128) ? 1 : -1];

static inline float gap_fast_ldexp(float value, int shift) {
    uint32_t bits, exponent;
    int scaled_exponent;
    memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7fffffffu) == 0u) return value; /* Preserve either signed zero. */
    exponent = (bits >> 23) & 255u;
    if (exponent == 0u || exponent == 255u || shift < -255 || shift > 255)
        return ldexpf(value, shift);
    scaled_exponent = (int)exponent + shift;
    if (scaled_exponent <= 0 || scaled_exponent >= 255) return ldexpf(value, shift);
    bits = (bits & 0x807fffffu) | ((uint32_t)scaled_exponent << 23);
    memcpy(&value, &bits, sizeof value);
    return value;
}

/* Same defined-domain result as (int32_t)roundf(ldexpf(value, shift)).
 * Caller guarantees the rounded/scaled result is representable in int32.
 * The FFT normalizer bounds every result to at most 2^27 in magnitude.
 * Tests must not cast NaN/Inf/out-of-range reference results to integers.
 */
static inline int32_t gap_fast_round_scaled(float value, int shift) {
    uint32_t bits, exponent, mantissa, magnitude;
    int scaled_exponent, unbiased;
    memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7fffffffu) == 0u) return 0;
    exponent = (bits >> 23) & 255u;
    if (exponent == 0u || exponent == 255u || shift < -255 || shift > 255)
        return (int32_t)roundf(ldexpf(value, shift));
    scaled_exponent = (int)exponent + shift;
    if (scaled_exponent <= 0 || scaled_exponent >= 255)
        return (int32_t)roundf(ldexpf(value, shift));
    unbiased = scaled_exponent - 127;
    if (unbiased < -1) return 0;
    if (unbiased == -1) return bits >> 31 ? -1 : 1;
    if (unbiased >= 31) return (int32_t)roundf(ldexpf(value, shift));
    mantissa = (bits & 0x7fffffu) | 0x800000u;
    if (unbiased >= 23) magnitude = mantissa << (unsigned)(unbiased - 23);
    else {
        unsigned right = (unsigned)(23 - unbiased);
        uint32_t remainder = mantissa & ((1u << right) - 1u);
        magnitude = (mantissa >> right) + (remainder >= (1u << (right - 1u)));
    }
    return bits >> 31 ? -(int32_t)magnitude : (int32_t)magnitude;
}
#endif
