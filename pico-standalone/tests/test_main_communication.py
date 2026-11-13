"""Test real Pico communication functions on the host, without device access.

Extracts the current main.c functions verbatim and supplies only hardware mocks.
Requires a host GCC with C11 support, not arm-none-eabi-gcc. Generated files and
results must be outside the project so native binaries/private paths are not
accidentally included in a public handoff. No DSP kernel or device is executed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gcc', required=True, help='Host GCC executable path or command on PATH')
    parser.add_argument('--output-dir', required=True, type=Path,
                        help='Directory outside the project for generated source, executable and results')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    project = source.parent
    out = args.output_dir.expanduser().resolve()
    if out == project or out.is_relative_to(project):
        parser.error('--output-dir must be outside the project')
    gcc_input = shutil.which(args.gcc) or args.gcc
    gcc = Path(gcc_input).expanduser().resolve()
    if not gcc.is_file():
        parser.error('--gcc does not identify an existing host compiler')
    if not (source / 'main.c').is_file() or not (source / 'standalone_link.h').is_file():
        parser.error('Cannot find current Pico source relative to this script')
    out.mkdir(parents=True, exist_ok=True)
    text = (source / 'main.c').read_text(encoding='utf-8')

    def function(name):
        import re
        match = re.search(r'^static [^\n]*\b' + re.escape(name) + r'\([^\n]*\) \{', text, re.M)
        assert match, name
        start, cursor, depth, quote = match.start(), match.end() - 1, 0, None
        while cursor < len(text):
            char = text[cursor]
            if quote:
                if char == '\\': cursor += 2; continue
                if char == quote: quote = None
            elif text.startswith('/*', cursor):
                cursor = text.index('*/', cursor + 2) + 2; continue
            elif text.startswith('//', cursor):
                cursor = text.index('\n', cursor + 2) + 1; continue
            elif char in ['"', "'"]: quote = char
            elif char == '{': depth += 1
            elif char == '}':
                depth -= 1
                if not depth: return text[start:cursor + 1]
            cursor += 1
        raise AssertionError(name)

    globals_begin = text.index('static uint32_t session,')
    globals_end = text.index('static sl_confirmation_t confirmation;', globals_begin) + len('static sl_confirmation_t confirmation;')
    typedef_begin = text.index('typedef struct {', globals_end)
    typedef_end = text.index('static pending_result_t result;', typedef_begin) + len('static pending_result_t result;')
    prefix = r'''
    #include <assert.h>
    #include <float.h>
    #include <inttypes.h>
    #include <math.h>
    #include <stdbool.h>
    #include <stdint.h>
    #include <stdio.h>
    #include <string.h>
    #include "standalone_link.h"
    #include "dsp/gap_dsp.h"
    #define GAP_BACKEND_LABEL "integer_q15_fast"
    #define UART_UARTFR_BUSY_BITS 8u
    #define uart0 0
    static char tx_frame[SL_FRAME_MAX];
    static volatile uint16_t tx_length, tx_position;
    static bool uart_ready;
    static uint32_t capture_drop_count;
    static uint64_t now_us=1000000, tick_us;
    static uint64_t time_us_64(void) { uint64_t value=now_us; now_us+=tick_us; return value; }
    static uint32_t save_and_disable_interrupts(void) { return 0; }
    static void restore_interrupts(uint32_t value) { (void)value; }
    static struct {uint32_t dr, fr;} fake_hw;
    #define uart_get_hw(n) (&fake_hw)
    static bool uart_is_writable(int n) {(void)n;return true;}
    static void uart_set_irqs_enabled(int n,bool rx,bool tx) {(void)n;(void)rx;(void)tx;}
    static char captured[SL_FRAME_MAX+1], gap_line[2048], profile_line[1024];
    static bool send_success=true;
    static unsigned sends, assertions;
    static bool uart_send(const char *frame,size_t length,uint64_t *started) {
        if(!send_success)return false;
        memcpy(captured,frame,length);captured[length]=0;++sends;
        if(started)*started=now_us+9;
        return true;
    }
    static bool usb_line(const char *line) {
        if(!strncmp(line,"GAP ",4))strcpy(gap_line,line);else strcpy(profile_line,line);
        return true;
    }
    const char *gap_reason_name(int reason) {(void)reason;return "estimated";}
    static void check(bool value) {++assertions;assert(value);}
    '''
    body = '\n'.join([function('uart_idle'), function('uart_send').replace('static bool uart_send(', 'static bool actual_uart_send('),
                       function('result_valid'), function('result_reason'), function('receive_ack'),
                       function('report_profile'), function('report_result'), function('send_pending_result')])
    tests = r'''
    static void reset_case(void) {
        memset(&result,0,sizeof result);memset(&fake_hw,0,sizeof fake_hw);
        result.estimate.valid=1;result.estimate.angle_deg=123.456f;result.estimate.quality=.789f;
        result.pending=true;result.sequence=9;result.end_us=800000;result.confirmed=true;
        session=0x12345678;uart_ready=true;uart_sequence=6;last_bearing_sequence=6;
        tx_result_seq=99;tx_age_ms=88;tx_valid=1;tx_angle_cdeg=777;tx_quality=66;
        ack_seq=3;ack_roundtrip_us=123;ack_status=2;ack_count=0;bearing_ack_pending=false;
        tx_length=tx_position=0;now_us=1000000;tick_us=0;sends=0;send_success=true;captured[0]=0;
    }
    static void wire_matches(uint32_t valid,uint32_t angle,uint32_t quality) {
        unsigned sess,seq,age,wire_valid,wire_angle,wire_quality;
        check(sscanf(captured,"@B,1,%8x,%u,%u,%u,%u,%u",&sess,&seq,&age,&wire_valid,&wire_angle,&wire_quality)==6);
        char *star=strchr(captured,'*');check(star!=NULL);
        unsigned crc;check(sscanf(star+1,"%4x",&crc)==1);
        check(crc==sl_crc16(captured+1,(size_t)(star-captured-1)));
        check(sess==session && seq==uart_sequence && seq==last_bearing_sequence);
        check(wire_valid==valid && wire_angle==angle && wire_quality==quality);
        check(tx_result_seq==result.sequence && tx_age_ms==age && tx_valid==valid && tx_angle_cdeg==angle && tx_quality==quality);
        check(!result.pending && bearing_ack_pending && sends==1);
    }
    int main(void) {
        reset_case();send_pending_result();wire_matches(1,12346,789);
        reset_case();result.end_us=0;send_pending_result();wire_matches(0,12346,789);check(tx_age_ms==1043);
        reset_case();result.confirmed=false;send_pending_result();wire_matches(0,12346,789);
        reset_case();result.estimate.valid=0;send_pending_result();wire_matches(0,0,0);
        reset_case();result.override_reason="capture_loss";send_pending_result();wire_matches(0,0,0);
        reset_case();result.estimate.angle_deg=NAN;send_pending_result();wire_matches(0,0,0);
        reset_case();result.estimate.quality=INFINITY;send_pending_result();wire_matches(0,0,0);
        reset_case();result.estimate.angle_deg=-1.25f;result.estimate.quality=2.f;send_pending_result();wire_matches(1,35875,1000);
        reset_case();result.estimate.angle_deg=720.f;result.estimate.quality=-.5f;send_pending_result();wire_matches(1,0,0);
        reset_case();now_us=70000000;result.end_us=0;send_pending_result();wire_matches(0,12346,789);check(tx_age_ms==60000);
        reset_case();uart_sequence=UINT32_MAX;send_pending_result();wire_matches(1,12346,789);check(uart_sequence==0);
        reset_case();send_success=false;send_pending_result();check(sends==0 && result.pending && uart_sequence==6);
        check(tx_result_seq==99 && tx_age_ms==88 && tx_valid==1 && tx_angle_cdeg==777 && tx_quality==66);
        reset_case();fake_hw.fr=UART_UARTFR_BUSY_BITS;send_pending_result();check(sends==0 && result.pending && tx_result_seq==99);
        reset_case();tick_us=1000;send_pending_result();check(sends==0 && result.pending && tx_result_seq==99);
        reset_case();send_pending_result();now_us=1100000;
        sl_ack_t ack={.session=session,.seq=last_bearing_sequence,.type=2,.status=1};receive_ack(&ack);
        check(ack_seq==7 && ack_status==1 && ack_roundtrip_us==99991 && !bearing_ack_pending);
        now_us=1200000;receive_ack(&ack);check(ack_roundtrip_us==99991 && ack_count==1);
        ack.type=0;ack.seq=0;ack.status=0;receive_ack(&ack);check(ack_seq==7 && ack_status==1 && ack_roundtrip_us==99991 && uart_ready);
        reset_case();send_pending_result();ack=(sl_ack_t){.session=session^1,.seq=7,.type=2,.status=0};receive_ack(&ack);
        check(ack_seq==3 && bearing_ack_pending && ack_count==0);
        ack.session=session;ack.seq=6;receive_ack(&ack);check(ack_seq==3 && bearing_ack_pending);
        ack.seq=7;ack.type=1;receive_ack(&ack);check(ack_seq==3 && bearing_ack_pending);
        ack.type=2;ack.status=4;hello_sent=true;now_us+=5000;receive_ack(&ack);
        check(!uart_ready && !hello_sent && ack_status==4 && ack_seq==7 && !bearing_ack_pending);
        reset_case();uint64_t stamp=777;check(actual_uart_send("123",3,&stamp));check(stamp==1000000 && fake_hw.dr=='3');
        fake_hw.fr=UART_UARTFR_BUSY_BITS;stamp=777;check(!actual_uart_send("123",3,&stamp));check(stamp==777);
        reset_case();send_pending_result();result.sequence=UINT32_MAX;result.estimate.angle_deg=359.999f;result.estimate.quality=1;
        result.estimate.code_channels=UINT8_MAX;result.capture_us=result.capture_wait_us=result.unpack_total_us=result.max_block_us=UINT32_MAX;
        result.dsp_us=result.cycle_us=result.result_interval_us=UINT32_MAX;result.override_reason="stale_measurement";
        tx_result_seq=tx_age_ms=tx_valid=tx_angle_cdeg=tx_quality=ack_seq=ack_roundtrip_us=ack_status=capture_drop_count=usb_drops=UINT32_MAX;
        report_result(UINT32_MAX);check(strlen(gap_line)<1024 && strstr(gap_line,"\"tx_result_seq\":4294967295") && strstr(gap_line,"v0.2-link_diag"));
        printf("{\"passed\":true,\"assertions\":%u,\"max_test_gap_line_bytes\":%zu}\n",assertions,strlen(gap_line));
        puts(gap_line);
        return 0;
    }
    '''
    probe = out / 'native-main-communication.c'
    probe.write_text(prefix + '\n' + text[globals_begin:globals_end] + '\n' + text[typedef_begin:typedef_end] + '\n' + body + '\n' + tests, encoding='utf-8')
    env = dict(os.environ)
    env['PATH'] = str(gcc.parent) + os.pathsep + env.get('PATH','')
    command = [str(gcc), '-std=c11','-O2','-Wall','-Wextra','-I'+str(source),str(probe),'-lm','-o',str(out/'native-main-communication.exe')]
    compiled = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    if compiled.returncode != 0:
        raise RuntimeError('Native compilation failed:\n' + compiled.stdout + compiled.stderr)
    ran = subprocess.run([str(out/'native-main-communication.exe')], capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    if ran.returncode != 0:
        raise RuntimeError('Native test failed:\n' + ran.stdout + ran.stderr)
    lines = [line for line in ran.stdout.splitlines() if line]
    results = json.loads(lines[0])
    results['gap_example'] = json.loads(lines[1][4:])
    results['main_sha256'] = hashlib.sha256((source/'main.c').read_bytes()).hexdigest()
    results['link_sha256'] = hashlib.sha256((source/'standalone_link.h').read_bytes()).hexdigest()
    results['hardware_access'] = False
    results['dsp_executed'] = False
    results['source_discovery'] = 'pico-standalone relative to this test script'
    results['compiler_version'] = subprocess.run([str(gcc), '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, check=True).stdout.splitlines()[0]
    results['compile_command'] = command
    results['compile_warnings'] = compiled.stderr
    results['test_method'] = 'Actual main.c functions extracted verbatim; UART/time/USB hardware mocked; actual uart_send additionally exercised with register mock.'
    (out/'native-main-communication-results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:results[key] for key in ['passed','assertions','max_test_gap_line_bytes','main_sha256']},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
