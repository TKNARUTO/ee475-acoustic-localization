# Offline checks

Run `python tools/verify_handoff.py --output-dir <outside-template-folder>` from the template root. Six groups cover Python syntax, launcher source, SRAM-only UF2 addressing, receive-only controls, packet faults and the synthetic gap model. They do not open a serial port. Always pass an output directory outside the frozen template; the unchanged historical default otherwise creates a local stage folder.

verify_english_ui.py is an optional disconnected/mock Tk UI check and requires a desktop session. It was not part of this six-group rerun. Plot requirements are optional. These tests contain no private microphone fixtures and do not establish physical angular accuracy, range or reliable rejection of all interference. Runtime logs are not part of the saved checksum baseline.

Platform/tools: Windows 10/11, Python 3.12+ with Tcl/Tk and Pico USB capture; phone player: Android 8.0/API 26+. A compiler is not needed to run the retained binary. See [platform requirements](../PLATFORM_EN.md) for versions and limits. In the full repository, the current independent Pico program is at `../../pico-standalone/` relative to the template root; this ZIP does not include it.
