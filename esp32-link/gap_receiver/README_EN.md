# Gap UART receiver v1.1 — link_diag

Updated 12 November 2026. [中文](README_ZH.md) · [Overview](../README_EN.md)

This sketch receives Pico's locally computed HF2 Gap bearing, validates packets and returns ACKs. It prints current raw diagnostics separately from target validity. It does not calculate acoustic direction on ESP32 or operate motors/LEDs.

## Required board package

| Selection | Tested configuration |
|---|---|
| Arduino IDE / CLI | **2.3.8 / 1.4.1** |
| Boards Manager package | **esp32 by Espressif Systems**, **3.3.12** |
| Board | **NodeMCU-32S**, classic ESP32 / NodeMCU ESP-32S |
| FQBN | `esp32:esp32:nodemcu-32s` |
| Additional Boards Manager URL | `https://espressif.github.io/arduino-esp32/package_esp32_index.json` |
| Serial settings | 115200 baud; inter-board UART 8N1 |

The package name, board model and COM port are different settings. Use the Espressif package, not the Arduino ESP32 Boards / Nano ESP32 package. This tested board is not ESP32-S3. The stable package URL and installation process come from [Espressif's official guide](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html).

## Three-wire connection

| Pico | Physical pin | Connection | ESP32 |
|---|---:|---|---|
| GP0 / UART0 TX | 1 | → | GPIO16 / P16 / UART2 RX |
| GP1 / UART0 RX | 2 | ← | GPIO17 / P17 / UART2 TX |
| GND | Any available GND | ↔ | GND |

Power the boards separately over USB. Disconnect USB before rewiring; do not join 5 V/VIN/3V3 rails. Keep SEN0325 GP6–GP13 wiring in place. The USB cables do not replace these UART wires.

## Arduino IDE steps

1. Open IDE **2.3.8**. In **File → Preferences → Additional Boards Manager URLs**, add the stable URL above if missing.
2. Open **Tools → Board → Boards Manager** or its sidebar icon. Search `esp32`; select **esp32 by Espressif Systems**, version **3.3.12**, and install.
3. Open `gap_receiver.ino`, keeping all companion headers in this folder.
4. Choose **Tools → Board → esp32 → NodeMCU-32S**. If automatic identification chose another board, use **Select other board and port** to select this model manually.
5. Choose the actual ESP32 in **Tools → Port**. The workstation example was **COM6**; every teammate must discover their own port. Latest local Pico was **COM8**, a different device.
6. Click **Verify**. Before **Upload**, close the Serial Monitor or logger holding that ESP32 port and preserve its existing Flash backup.
7. Open **Tools → Serial Monitor**, set **115200**, and reset ESP32 to see startup: `SELFTEST PASS checks=57 failed=0`, then `READY EE475_GAP_RECEIVER v1.1 link_diag RX=16 TX=17 ... no_motor`.

The [Arduino board/port guide](https://support.arduino.cc/hc/en-us/articles/4406856349970-Select-board-and-port-in-Arduino-IDE) explains manual selection. Fix a missing FQBN by selecting the board; fix an unavailable port by selecting the actual port and closing its other owner.

## CLI compile and upload

Run from this sketch folder. Replace `COMx` after examining `board list`; it is not a fixed port. These are instructions, not automatically executed commands.

```powershell
arduino-cli version
arduino-cli core list
arduino-cli board list
$EspPort = 'COMx'
arduino-cli compile --fqbn esp32:esp32:nodemcu-32s --output-dir '.\build\local' '.'
arduino-cli upload --fqbn esp32:esp32:nodemcu-32s --port $EspPort --input-dir '.\build\local' '.'
```

If the package is missing, install through the IDE above or run:

```powershell
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.12 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

CLI `upload` does not compile first: use the successful compile output, as described in the [official upload reference](https://arduino.github.io/arduino-cli/1.4/commands/arduino-cli_upload/). The desktop Arduino copy instead names its main file `sketch_nov12a.ino`; main `.ino` and sketch folder names must match.

The public [BUILD.json](firmware/BUILD.json) preserves the tested deployment hash, exact platform configuration and source identity. The merged binary is retained privately, not distributed, because it embeds local compiler paths. This packaging change does not modify the tested board firmware. The desktop entry file and canonical `.ino` plus three headers match byte-for-byte; a different sketch filename can change rebuilt binary metadata. Compile and upload the public source through Arduino IDE above, preserving the board's existing Flash backup first. No untested replacement binary is supplied. This receiver contains no motor control and is not for ESP32-S3.

## Diagnostics and valid targets

```text
BEARING seq=11 class=DIAG_STALE ack_status=1 source_valid=0 raw_cdeg=12345 raw_q=678 source_age_ms=700 target_valid=0
```

`raw_cdeg=12345` means **123.45° in array coordinates**. `raw_q` is received quality 0..1000, not accuracy probability. `source_age_ms` excludes the receiver's additional 20 ms allowance. `source_valid` is the transmitted flag; `target_valid` is the receiver's actual target state.

| Class | Meaning |
|---|---|
| `ACCEPTED` | New valid packet within the freshness bound |
| `DIAG_STALE` | Received age + 20 ms exceeds 500 ms; target invalid |
| `DIAG_INVALID` | New explicit-invalid packet within the age bound; detailed reason unavailable |
| `RX_REJECTED` | Wrong/no session or duplicate/out-of-order; cannot replace or renew target |

Rejection has priority over a stale label. For a rejected packet, `target_valid=1` may refer to an earlier unexpired target; raw fields still belong to the rejected packet. Old target angles are never printed under a new sequence.

Invalid B packets can carry a finite raw fit for diagnosis. **Zero degrees is legitimate.** The eight B fields lack `fit_valid`, confirmation state and detailed reason; do not infer fit presence from zero/nonzero values. There is no D packet. Diagnostics do not authorize motion.

## Protocol and timing

ASCII, maximum 128 bytes including LF. Here `\n` means one LF byte:

```text
@H,1,SESSION8HEX*CCCC\n
@P,1,SESSION8HEX,seq*CCCC\n
@B,1,SESSION8HEX,seq,age_ms,valid,angle_cdeg,quality*CCCC\n
@A,1,SESSION8HEX,seq,type,status,count*CCCC\n
```

CRC16-CCITT-FALSE covers the payload between `@` and `*`: polynomial 0x1021, initial 0xFFFF, no reflection/final XOR; `123456789` → `29B1`. Invalid CRC/fields, CRLF and overlong input receive no ACK. Malformed parsed lines produce `RX_REJECTED reason=bad_frame`.

H establishes the session. New sessions clear target/sequence state; repeated same-session H preserves it. H/P never renew measurements. B ranges: seq uint32; age 0..60000 ms; valid 0/1; angle 0..35999 centidegrees; quality 0..1000. Invalid/stale new B records advance sequence, with uint32 half-range ordering. Large turns remain allowed.

ACK type: 0 H, 1 P, 2 B. Status: 0 accepted, 1 explicit invalid, 2 stale, 3 duplicate/out-of-order, 4 wrong/no session. Count increases for H/P and B status 0/1. An explicit-invalid stale B retains status 1; `DIAG_STALE` is only its display classification.

```text
age = source_age_ms + 20 ms + elapsed_since_receive
target expires when age > 500 ms
```

The limit is unchanged. Array-to-robot-front calibration and a measured motor-stop guarantee are not provided.

## Validation and limitations

Shared native/startup checks: **57 passed**. Startup tests use temporary state before enabling UART2. Current locally verified Flash artifact prefixes: Pico **11958e93**, desktop ESP32 merged image **36610897**.

Trial 03 after Flash: **37/37 exact records**, **37 CRC-valid B ACKs**, **36 later Pico confirmations**. Trial 04 after Pico software reboot: **14/14**, **14**, **13** respectively. The final packet in each run reached the recording boundary before a later Pico report. No interior missing observations, parse errors or observed receiver error/drop counter increases occurred. Session/sequence recovery worked. Targets remained invalid: this verifies communication/recovery, not acoustic angle accuracy. See the [communication report](../../reports/communication-2026-11-12/REPORT_EN.md).

An earlier phone trial contained repeated and fragmented startup USB output. Do not treat the full file as a clean acceptance run. The recorder now saves bounded startup bytes separately, resets each input buffer once and aligns to LF before formal timing. It does not filter errors mid-trial; this does not prove an FTDI driver defect.

USB logging is best-effort; inspect `STAT bad`, `lines`, `ack_drop`, `usb_drop`. USB TX is 512 bytes, and the ACK queue has four slots. ESP ACK logs show generation/queueing; later Pico ACK metadata supplies receipt evidence. ACK roundtrip includes foreground parsing delay and is not isolated cable latency.

| File | Function |
|---|---|
| `gap_receiver.ino` | Receive/ACK loop and USB diagnostics |
| `gap_protocol.h` | Protocol/state machine, unchanged by v1.1 diagnostics |
| `gap_diagnostics.h` | Pure raw-packet formatter and classification |
| `gap_self_tests.h` | Shared 57-check regression suite |
| `tests/host_protocol_test.cpp` | Native runner, no serial/GPIO |
| `README_EN.md`, `README_ZH.md` | Setup/handoff instructions |
| `firmware/` | Deployment evidence and build/source hashes; tested binary retained privately |
| `build/` if present | Generated local output, not source or proof of installation |

See the [communication notebook](../../pico-standalone/COMMUNICATION_NOTEBOOK_EN.md) for provenance and decisions. Local recordings/backups stay outside the public handoff. Fresh acoustic target acceptance, distance sensing and motors remain separate work.
