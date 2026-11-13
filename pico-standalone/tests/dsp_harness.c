/* Native offline harness. PCM16LE input only; no SDK, serial or GPIO access.
 * Each complete 4096 x 7 frame produces one JSON line. Short final frames fail.
 * This reports native wall time, never a claim about RP2040 execution time. */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "../dsp/gap_dsp.h"

static int16_t audio[4096][7];

static double monotonic_ms(void) {
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value) != 0) return NAN;
    return (double)value.tv_sec * 1000.0 + (double)value.tv_nsec / 1000000.0;
}

static void number(float x) {
    if (isfinite(x)) printf("%.9g", (double)x);
    else fputs("null", stdout);
}

static void vector(const float *values) {
    unsigned ch;
    putchar('[');
    for (ch = 0; ch < 7; ++ch) {
        if (ch) putchar(',');
        number(values[ch]);
    }
    putchar(']');
}

int main(int argc, char **argv) {
    FILE *input;
    unsigned long index = 0;
    const uint16_t endian = 1;
    if (argc != 2) {
        fputs("usage: gap_dsp_harness frames.pcm16le\n", stderr);
        return 2;
    }
    if (*(const unsigned char *)&endian != 1) {
        fputs("This offline harness requires a little-endian host.\n", stderr);
        return 2;
    }
    input = fopen(argv[1], "rb");
    if (!input) { perror("input"); return 2; }
    gap_reset();
    for (;;) {
        size_t bytes = fread(audio, 1, sizeof audio, input);
        gap_result_t result;
        double start, end;
        if (!bytes && feof(input)) break;
        if (bytes != sizeof audio) {
            fprintf(stderr, "incomplete PCM frame %lu: %lu of %lu bytes\n",
                index, (unsigned long)bytes, (unsigned long)sizeof audio);
            fclose(input);
            return 3;
        }
        start = monotonic_ms();
        gap_estimate((const int16_t (*)[7])audio, &result);
        end = monotonic_ms();
        printf("{\"index\":%lu,\"valid\":%s,\"reason\":%d,\"reason_name\":\"%s\",\"code_channels\":%d,\"angle_deg\":",
            index, result.valid ? "true" : "false", result.reason,
            gap_reason_name(result.reason), result.code_channels);
        number(result.angle_deg);
        fputs(",\"quality\":", stdout); number(result.quality);
        fputs(",\"rms_samples\":", stdout); number(result.rms_samples);
        fputs(",\"projection\":", stdout); number(result.projection);
        fputs(",\"pnr_db\":", stdout); vector(result.pnr_db);
        fputs(",\"arrival_samples\":", stdout); vector(result.arrival_samples);
        fputs(",\"native_wall_ms\":", stdout); number((float)(end - start));
        printf(",\"workspace_bytes\":%lu}\n", (unsigned long)gap_workspace_bytes());
        ++index;
    }
    if (ferror(input)) { perror("read"); fclose(input); return 3; }
    fclose(input);
    return 0;
}
