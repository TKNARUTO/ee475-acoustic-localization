#pragma once
#include "gap_protocol.h"
#include "gap_diagnostics.h"

namespace gaplink {
struct TestResult { unsigned checks = 0, failed = 0; const char *first_failure = nullptr; };
inline TestResult self_test() {
    TestResult result;
    auto check = [&](bool passed, const char *name) {
        ++result.checks;
        if (!passed) { ++result.failed; if (!result.first_failure) result.first_failure = name; }
    };
    auto from_payload = [](const char *payload, Message &message) {
        char encoded[MAX_FRAME + 1];
        const size_t n = frame(payload, encoded, sizeof encoded);
        if (!n) return false;
        encoded[n - 1] = 0; // parser consumes a completed line without LF
        return parse(encoded, message);
    };
    check(crc16("123456789", 9) == 0x29b1, "crc_known_vector");
    Message h, p, b;
    check(from_payload("H,1,1234ABCD", h) && h.session == 0x1234abcd, "hello");
    check(from_payload("P,1,1234ABCD,4294967295", p) && p.seq == UINT32_MAX, "uint32_max");
    check(from_payload("B,1,1234ABCD,1,100,1,9000,750", b), "bearing");
    Message invalid;
    const char *bad[] = {
        "H,1,123ABCD", "H,1,1234ABCD,", "H,2,1234ABCD",
        "B,1,1234ABCD,1,100,1,nan,750", "B,1,1234ABCD,1,-1,1,9000,750",
        "B,1,1234ABCD,4294967296,0,1,0,0", "B,1,1234ABCD,1,60001,1,0,0",
        "B,1,1234ABCD,1,0,2,0,0", "B,1,1234ABCD,1,0,1,36000,0",
        "B,1,1234ABCD,1,0,1,0,1001", "B,1,1234ABCD,,0,1,0,0",
        "B,1,1234ABCD,1,0,1,0,0,extra", "P,1,1234ABCD,+1"
    };
    for (const char *text : bad) check(!from_payload(text, invalid), "malformed_fields");
    char encoded[MAX_FRAME + 1];
    const size_t n = frame("H,1,1234ABCD", encoded, sizeof encoded);
    encoded[n - 1] = 0; encoded[3] = '9';
    check(!parse(encoded, invalid), "bad_crc");
    LineReader reader;
    for (size_t i = 0; i < 200; ++i) reader.push('X');
    check(reader.push('\n') == LineReader::REJECTED, "oversize_drop");
    const size_t valid_n = frame("H,1,1234ABCD", encoded, sizeof encoded);
    LineReader::Result status = LineReader::NONE;
    for (size_t i = 0; i < valid_n; ++i) status = reader.push(encoded[i]);
    check(status == LineReader::READY && parse(reader.line(), invalid), "recover_after_overflow");
    reader.push('@'); reader.push('\0');
    check(reader.push('\n') == LineReader::REJECTED, "control_byte_drop");
    // Exactly 127 non-LF bytes are allowed in the collector; 128 are not.
    for (size_t i = 0; i < 127; ++i) reader.push('X');
    check(reader.push('\n') == LineReader::READY, "max_line_boundary");
    for (size_t i = 0; i < 128; ++i) reader.push('X');
    check(reader.push('\n') == LineReader::REJECTED, "max_line_overflow");
    Receiver state;
    check(state.process(b, 0).status == WRONG_SESSION && !state.target_valid, "require_hello");
    check(state.process(h, 0).status == ACCEPTED && state.configured, "select_session");
    check(state.process(b, 10).status == ACCEPTED && state.target_valid && state.angle_cdeg == 9000, "accept_bearing");
    check(state.process(b, 20).status == DUPLICATE && state.received_ms == 10, "duplicate_no_refresh");
    Message older = b; older.seq = 0;
    check(state.process(older, 30).status == DUPLICATE, "old_sequence");
    state.process(h, 40); state.process(p, 50);
    check(state.received_ms == 10 && state.have_seq && state.last_seq == 1, "hello_ping_no_refresh");
    check(!state.expire(390) && state.target_valid, "age_boundary_valid");
    check(state.expire(391) && !state.target_valid && !state.expire(392), "expire_once");
    Message stale = b; stale.seq = 2; stale.age_ms = 481;
    check(state.process(stale, 400).status == STALE && !state.target_valid, "stale_arrival");
    Message turn = b; turn.seq = 3; turn.age_ms = 0; turn.angle_cdeg = 27000;
    check(state.process(turn, 410).status == ACCEPTED && state.angle_cdeg == 27000, "large_turn_allowed");
    Message stop = turn; stop.seq = 4; stop.valid = 0;
    check(state.process(stop, 420).status == INVALID && !state.target_valid, "explicit_invalid");
    Message wrong = turn; wrong.seq = 5; wrong.session ^= 1;
    check(state.process(wrong, 425).status == WRONG_SESSION && state.last_seq == 4, "wrong_session_no_refresh");
    Message next_h = h; ++next_h.session;
    state.process(next_h, 430);
    check(!state.have_seq && !state.target_valid && state.session == next_h.session, "session_clears_target");
    Receiver wrap; wrap.process(h, 0);
    Message end = b; end.seq = UINT32_MAX; end.age_ms = 0;
    wrap.process(end, 0xfffffff0u);
    end.seq = 0;
    check(wrap.process(end, 0xfffffff5u).status == ACCEPTED, "sequence_wrap");
    check(!wrap.expire(0x10u) && wrap.age(0x10u) == 47, "millis_wrap");
    Ack ack = wrap.process(end, 0x20u);
    char output[MAX_FRAME + 1];
    check(format_ack(ack, output, sizeof output) > 0 && output[0] == '@', "ack_format");

    // Exercise the actual USB formatter. A new invalid packet must never print
    // an old target's angle/quality as though they belonged to its new sequence.
    Receiver diagnostic; diagnostic.process(h, 0);
    Message before = b; before.seq = 10; before.age_ms = 0;
    diagnostic.process(before, 100);
    Message raw;
    check(from_payload("B,1,1234ABCD,11,200,0,12345,678", raw) &&
          raw.angle_cdeg == 12345 && raw.quality == 678, "invalid_nonzero_raw_allowed");
    ack = diagnostic.process(raw, 110);
    check(ack.status == INVALID && !diagnostic.target_valid && diagnostic.angle_cdeg == 9000,
          "diagnostic_does_not_replace_target");
    char line[DIAGNOSTIC_CAPACITY];
    check(format_bearing_diagnostic(raw, ack, diagnostic.target_valid, line, sizeof line) > 0 &&
          strcmp(line, "BEARING seq=11 class=DIAG_INVALID ack_status=1 source_valid=0 raw_cdeg=12345 raw_q=678 source_age_ms=200 target_valid=0\n") == 0,
          "new_raw_not_old_target_output");
    check(from_payload("B,1,1234ABCD,12,700,0,0,777", raw), "zero_degree_diagnostic_allowed");
    ack = diagnostic.process(raw, 120);
    check(ack.status == INVALID && strcmp(bearing_class(raw, ack), "DIAG_STALE") == 0,
          "stale_explicit_invalid_class");
    check(format_bearing_diagnostic(raw, ack, diagnostic.target_valid, line, sizeof line) > 0 &&
          strstr(line, "raw_cdeg=0 raw_q=777 source_age_ms=700 target_valid=0"), "zero_degree_not_missing");
    raw.seq = 13; raw.age_ms = 20; raw.quality = 0;
    ack = diagnostic.process(raw, 130);
    check(strcmp(bearing_class(raw, ack), "DIAG_INVALID") == 0 && !diagnostic.target_valid,
          "zero_raw_does_not_imply_fit");
    Message fresh = before; fresh.seq = 14; fresh.age_ms = 480;
    ack = diagnostic.process(fresh, 140);
    check(ack.status == ACCEPTED && strcmp(bearing_class(fresh, ack), "ACCEPTED") == 0 &&
          diagnostic.target_valid && !diagnostic.expire(140), "diagnostic_keeps_500ms_boundary");
    check(diagnostic.expire(141) && !diagnostic.target_valid, "diagnostic_does_not_extend_expiry");
    fresh.seq = 15; fresh.age_ms = 0;
    diagnostic.process(fresh, 150);
    Message duplicate = fresh; duplicate.valid = 0; duplicate.age_ms = 60000; duplicate.angle_cdeg = 33333;
    ack = diagnostic.process(duplicate, 151);
    check(ack.status == DUPLICATE && strcmp(bearing_class(duplicate, ack), "RX_REJECTED") == 0 &&
          diagnostic.target_valid && diagnostic.last_seq == 15, "duplicate_class_precedes_stale");
    check(format_bearing_diagnostic(duplicate, ack, diagnostic.target_valid, line, sizeof line) > 0 &&
          strstr(line, "class=RX_REJECTED") && strstr(line, "raw_cdeg=33333") && strstr(line, "target_valid=1"),
          "duplicate_output_distinguishes_raw_and_target");
    Message wrong_raw = duplicate; wrong_raw.seq = 16; wrong_raw.session ^= 1;
    ack = diagnostic.process(wrong_raw, 152);
    check(ack.status == WRONG_SESSION && strcmp(bearing_class(wrong_raw, ack), "RX_REJECTED") == 0 &&
          diagnostic.last_seq == 15 && diagnostic.target_valid, "wrong_session_class_precedes_stale");
    fresh.seq = 16; fresh.age_ms = 481;
    ack = diagnostic.process(fresh, 153);
    check(ack.status == STALE && strcmp(bearing_class(fresh, ack), "DIAG_STALE") == 0 &&
          !diagnostic.target_valid, "stale_valid_packet_remains_invalid");
    check(format_bearing_diagnostic(fresh, ack, false, line, 8) == 0 && line[0] == 0,
          "diagnostic_no_truncated_line");
    Message maximal = fresh; maximal.seq = UINT32_MAX; maximal.age_ms = 60000;
    maximal.angle_cdeg = 35999; maximal.quality = 1000;
    Ack maximal_ack = ack; maximal_ack.seq = maximal.seq;
    const size_t diagnostic_n = format_bearing_diagnostic(maximal, maximal_ack, false, line, sizeof line);
    check(diagnostic_n > 0 && diagnostic_n < DIAGNOSTIC_CAPACITY && line[diagnostic_n - 1] == '\n',
          "maximum_diagnostic_fits_buffer");
    check(format_bearing_diagnostic(h, maximal_ack, false, line, sizeof line) == 0 && line[0] == 0,
          "no_bearing_line_for_non_bearing");
    check(format_bearing_diagnostic(fresh, maximal_ack, false, line, sizeof line) == 0 && line[0] == 0,
          "no_bearing_line_for_mismatched_ack");
    check(!parse("@B,1,1234ABCD,99,0,0,22222,999*0000", raw) &&
          strcmp(BAD_FRAME_DIAGNOSTIC, "RX_REJECTED reason=bad_frame\n") == 0 && diagnostic.last_seq == 16,
          "bad_frame_rejected_without_new_target");
    return result;
}
} // namespace gaplink
