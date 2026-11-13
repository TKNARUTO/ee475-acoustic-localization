# Validation guide
## Evidence levels
- File/build checks establish format, reproducibility or binary identity.
- Native tests exercise real parsing/state logic with mocked time/hardware.
- Two-port trials establish observed packet-field agreement and ACK behavior.
- Known-angle acoustic tests are required for physical accuracy; motor tests for safe following.

See [the current report](../reports/communication-2026-11-12/REPORT_EN.md). A 33/33 angle-field match means transport preserved the estimate; it does not mean the sound source was at that angle. CPU timed-region/cycle ratios are proxies, not full profiler utilization. Linker free space is not a measured runtime high-water mark.

## Reproduce portable checks
Use project requirements, Python3.12+, and a native C/C++ compiler (not the embedded ARM compiler). Windows bench native tests used Cygwin GCC4.8.3. Replace executable paths and use an external writable result folder.
```powershell
python -m unittest discover -s pico-standalone/tests -p "test_*.py"
python pico-standalone/tests/run_offline_validation.py --help
python pico-standalone/tests/run_offline_validation.py --skip-real --gcc C:\Path\To\gcc.exe --output C:\BenchResults\public-dsp
g++ -std=c++11 -Iesp32-link/gap_receiver esp32-link/gap_receiver/tests/host_protocol_test.cpp -o C:\BenchResults\esp-tests.exe
C:\BenchResults\esp-tests.exe
python tools/verify_release.py
```
Consult the Pico README for native main/link checks. Public DSP fixtures default to the frozen combo reference. Private recordings require explicit arguments and are not in the repository.

**Known non-passing DSP acceptance:** the public float-reference run processed 187 windows: 27 of 29 checks passed; two wrong-code negative checks failed (1/37 false accepted in the ordinary negative set, and 3/3 in the repeated wrong-code case). C versus PC arrival-path validity agreed, but shared false positives remain. Do not convert this to an overall production PASS. FAST numerical equivalence evidence is separate.

## Hardware procedure for the next stage
Fix phone position at a recorded physical angle/distance/volume. Play the matched HF2 file, record intended pause intervals, capture a finite trial, then compare source timing, fitted direction, confirmation, freshness, transmitted fields, ESP accepted state and ACKs. Repeat at several known angles and distances. Keep all raw microphone data local.

The startup recorder's warmup interval is separate from formal observations. Keep the warmup data and any parse error; never silently remove bad lines. A start/end unmatched record is not automatically packet loss, while zero observed interior gaps does not prove an unobservable wire could never lose data.

Physical power-cycle, current-Flash positive phone acceptance, worst-case control scheduling, heap/stack high water, true sound-to-arrow delay and comprehensive Android background behavior remain open.
