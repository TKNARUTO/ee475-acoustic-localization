/* Host-only protocol/age tests: no Pico SDK or hardware access. */
#include <stdio.h>
#include <string.h>
#include "../standalone_link.h"

static unsigned checks, failures;
static void check(int condition, const char *name) {
    ++checks;
    if (!condition) { ++failures; printf("FAIL %s\n", name); }
}
static bool ack(const char *payload, sl_ack_t *out) {
    char encoded[SL_FRAME_MAX];
    size_t n = sl_encode(encoded, sizeof encoded, payload);
    return n && sl_parse_ack(encoded, n - 1, out);
}
int main(void) {
    sl_ack_t parsed;
    char frame[SL_FRAME_MAX], long_payload[123];
    check(sl_crc16("123456789", 9) == 0x29b1, "CRC16 CCITT-FALSE standard vector");
    check(sl_crc16("", 0) == 0xffff, "CRC empty");
    check(ack("A,1,1234ABCD,0,0,0,0", &parsed), "hello ACK");
    check(parsed.session == 0x1234abcdu && parsed.seq == 0 && parsed.type == 0 && parsed.status == 0, "ACK fields");
    check(ack("A,1,ffffffff,4294967295,2,4,4294967295", &parsed), "unsigned maximum and status4");
    check(parsed.seq == UINT32_MAX && parsed.count == UINT32_MAX, "full uint32 retained");
    const char *bad[] = {
        "H,1,1234ABCD", "A,2,1234ABCD,0,0,0,0", "A,1,123ABCD,0,0,0,0",
        "A,1,1234ABCG,0,0,0,0", "A,1,1234ABCD,4294967296,0,0,0",
        "A,1,1234ABCD,-1,0,0,0", "A,1,1234ABCD,+1,0,0,0",
        "A,1,1234ABCD,0,3,0,0", "A,1,1234ABCD,0,0,5,0",
        "A,1,1234ABCD,0,0,0,4294967296", "A,1,1234ABCD,0,0,0,0,1",
        "A,1,1234ABCD,,0,0,0", "A,1,1234ABCD,0,0,0", "A,1,1234ABCD,0,0,0, 0"
    };
    for (unsigned i = 0; i < sizeof bad / sizeof bad[0]; ++i) check(!ack(bad[i], &parsed), bad[i]);
    size_t n = sl_encode(frame, sizeof frame, "A,1,1234ABCD,21,2,0,8");
    check(n && frame[n - 1] == '\n' && frame[0] == '@', "wire framing includes LF");
    check(!sl_parse_ack(frame, n, &parsed), "parser requires stripped LF");
    frame[n - 2] = frame[n - 2] == '0' ? '1' : '0';
    check(!sl_parse_ack(frame, n - 1, &parsed), "bad CRC rejected");
    check(sl_encode(frame, 8, "H,1,1234ABCD") == 0, "capacity bound");
    memset(long_payload, 'A', 121); long_payload[121] = 0;
    check(sl_encode(frame, sizeof frame, long_payload) == 128, "128-byte wire bound accepted");
    long_payload[121] = 'A'; long_payload[122] = 0;
    check(sl_encode(frame, sizeof frame, long_payload) == 0, "129-byte wire rejected");
    check(sl_encode(frame, sizeof frame, "H,1,1234ABCD\n") == 0, "embedded control byte rejected");
    check(sl_measurement_age_ms(1000000, 1000000) == 43, "sample window center age");
    check(sl_measurement_age_ms(1000000, 1437333) == 480, "480ms boundary");
    check(sl_measurement_age_ms(1000000, 1437334) == 481, "ceil prevents understating stale age");
    check(sl_age_is_fresh(480) && !sl_age_is_fresh(481), "fixed 500ms expiry plus20 allowance");
    check(!sl_age_is_fresh(UINT32_MAX), "age overflow rejected");
    sl_confirmation_t state = {0};
    check(!sl_confirm(&state, 1000000, true), "first code is confirming");
    check(sl_confirm(&state, 1200000, true), "second code confirms by real time");
    check(sl_confirm(&state, 1300000, false), "single missing-code window retains confirmation state");
    check(sl_confirm(&state, 1600000, true), "third code within deadline");
    check(!sl_confirm(&state, 2350000, false), "750ms expires confirmation");
    check(!sl_confirm(&state, 2400000, true), "after expiry first hit only");
    check(!sl_confirm(&state, 3150000, true), "750ms-separated hits do not confirm");
    check(sl_confirm(&state, 3250000, true), "subsequent nearby code confirms");
    sl_confirmation_reset(&state);
    check(!state.have_code && !state.confirmed, "capture loss reset");
    printf("checks=%u failures=%u\n", checks, failures);
    return failures ? 1 : 0;
}
