"""Read a v0.5 raw packet with separate timings and explicit failure categories.

All timestamps use the host monotonic clock. Header wait includes device work;
it must not be described as USB transfer time alone.
"""
from dataclasses import dataclass
import time
import zlib


class PacketError(RuntimeError):
    def __init__(self, category, message, details):
        super().__init__(message)
        self.category = category
        self.details = dict(details, error=category, message=message)


@dataclass
class RawPacket:
    data: bytearray
    header: dict
    timing: dict


def receive_packet(link, send_record, log_line, *, clock=time.perf_counter,
                   header_timeout=4., payload_timeout=4., trailer_timeout=1.,
                   idle_timeout=.6, cancelled=lambda: False):
    """Use short, accumulated reads; restore the caller's serial timeout."""
    old_timeout = getattr(link, 'timeout', None)
    try:
        link.timeout = .02
        return _receive_packet(link, send_record, log_line, clock, header_timeout,
                               payload_timeout, trailer_timeout, idle_timeout, cancelled)
    finally:
        link.timeout = old_timeout


def _receive_packet(link, send_record, log_line, clock, header_timeout,
                    payload_timeout, trailer_timeout, idle_timeout, cancelled):
    started = clock()
    timing = {'request_monotonic': time.monotonic(), 'request_perf_counter': started, 'read_strategy': 'accumulated_20ms',
              'expected_bytes': 4096 * 7 * 2, 'received_bytes': 0,
              'payload_read_calls': 0, 'empty_payload_reads': 0}

    def waiting():
        try:
            return int(link.in_waiting)
        except (AttributeError, OSError):
            return None

    def fail(category, message):
        timing['packet_total_ms'] = round((clock() - started) * 1000, 3)
        timing['in_waiting_at_error'] = waiting()
        raise PacketError(category, message, timing)

    def check_cancelled():
        if cancelled():
            fail('capture_cancelled', 'Capture cancelled by scan, profile or connection change.')

    def text_line(deadline):
        # readline() may return a partial line on timeout. Keep it until LF.
        pending = bytearray()
        while clock() < deadline:
            check_cancelled()
            part = link.readline()
            pending.extend(part)
            if len(pending) > 1024:
                fail('text_framing', 'Raw packet text boundary exceeds 1024 bytes.')
            if pending.endswith(b'\n'):
                return pending.decode('ascii', 'replace').strip()
        if pending:
            timing['partial_text'] = pending.decode('ascii', 'replace')
        return ''

    send_record()
    sent = clock()
    timing['command_write_ms'] = round((sent - started) * 1000, 3)
    header = None
    deadline = sent + header_timeout
    while clock() < deadline:
        line = text_line(deadline)
        if line:
            log_line(line)
        if line.startswith('AUDIO '):
            try:
                header = dict(token.split('=', 1) for token in line.split()[1:])
                timing['seq'] = int(header['seq'])
                shape = tuple(int(header[k]) for k in ('frames', 'fs', 'channels', 'bytes'))
                expected_crc = int(header['crc32'], 16)
                for key in ('dropped', 'rx_stall', 'process_us'):
                    int(header[key])
            except (ValueError, KeyError):
                fail('header_format', 'Malformed raw packet header.')
            break
        if 'STOP_FIRST' in line:
            fail('device_state', 'Unexpected raw capture state; reconnecting.')
    header_done = clock()
    timing['header_wait_ms'] = round((header_done - sent) * 1000, 3)
    if header is None:
        fail('header_timeout', 'No raw capture header received. Reconnect Pico.')
    if shape != (4096, 48000, 7, 4096 * 7 * 2) or not 0 <= expected_crc <= 0xffffffff:
        fail('header_format', 'Unexpected raw packet length or format.')
    timing['expected_crc32'] = f'{expected_crc:08x}'
    timing['in_waiting_after_header'] = waiting()
    data = bytearray()
    read_times = []
    read_sizes = []
    deadline = header_done + payload_timeout
    last_progress = header_done
    while len(data) < timing['expected_bytes'] and clock() < deadline:
        check_cancelled()
        read_started = clock()
        chunk = link.read(timing['expected_bytes'] - len(data))
        read_times.append(round((clock() - read_started) * 1000, 3))
        read_sizes.append(len(chunk))
        timing['payload_read_calls'] += 1
        timing['empty_payload_reads'] += not bool(chunk)
        data.extend(chunk)
        timing['received_bytes'] = len(data)
        if chunk:
            last_progress = clock()
        elif clock() - last_progress >= idle_timeout:
            break
    payload_done = clock()
    timing.update(received_bytes=len(data), payload_read_ms=round((payload_done-header_done)*1000, 3),
                  payload_read_sizes=read_sizes, payload_read_durations_ms=read_times)
    crc_started = clock()
    actual_crc = zlib.crc32(data)
    timing['crc_check_ms'] = round((clock() - crc_started) * 1000, 3)
    timing['actual_crc32'] = f'{actual_crc:08x}'
    check_cancelled()
    if len(data) != timing['expected_bytes']:
        fail('short_payload', f'Incomplete raw packet: {len(data)}/{timing["expected_bytes"]} bytes; bearing suppressed.')
    if actual_crc != expected_crc:
        fail('crc_mismatch', 'Raw packet CRC mismatch; bearing suppressed.')
    trailer_started = clock()
    trailer = ''
    deadline = trailer_started + trailer_timeout
    while clock() < deadline and not trailer:
        trailer = text_line(deadline)
    timing.update(trailer=trailer, trailer_wait_ms=round((clock()-trailer_started)*1000, 3))
    if trailer != 'AUDIO_END seq=' + header['seq']:
        fail('trailer_mismatch' if trailer else 'trailer_timeout', 'Raw packet trailer missing or sequence mismatch.')
    timing.update(packet_done_perf_counter=clock(), packet_total_ms=round((clock()-started)*1000, 3))
    return RawPacket(data, header, timing)


def stop_and_resynchronize(link, send_stop, *, clock=time.perf_counter,
                           timeout=1.2, cancelled=lambda: False):
    """Drain to a fresh STOP acknowledgement before accepting another packet.

    No input-buffer reset: it could discard the very acknowledgement we need.
    Incomplete/CRC-failed samples never enter DSP, even after recovery.
    """
    started = clock()
    result = {'recovered': False, 'drained_bytes': 0, 'stop_attempts': 0}
    old_timeout = getattr(link, 'timeout', None)
    pending = bytearray()
    try:
        link.timeout = .02
        send_stop()
        result['stop_attempts'] += 1
        next_stop = clock() + .2
        while clock() - started < timeout and not cancelled():
            # A full host RX queue can also lose the first acknowledgement.
            # Retry only while draining; never accept an unconfirmed boundary.
            if clock() >= next_stop:
                send_stop()
                result['stop_attempts'] += 1
                next_stop = clock() + .2
            waiting = int(getattr(link, 'in_waiting', 0))
            chunk = link.read(max(1, min(waiting, 4096)))
            result['drained_bytes'] += len(chunk)
            pending.extend(chunk)
            while b'\n' in pending:
                line, _, rest = pending.partition(b'\n')
                pending = bytearray(rest)
                if line.strip() == b'STOPPED; clocks LOW':
                    result['recovered'] = True
                    return result
            if len(pending) > 1024:
                del pending[:-1024]
        return result
    finally:
        link.timeout = old_timeout
        result['recovery_ms'] = round((clock()-started)*1000, 3)
