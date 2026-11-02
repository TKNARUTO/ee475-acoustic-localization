# Current architecture

Phone audio → acoustic path → SEN0325 digital I2S microphones → Pico PIO/DMA → CRC-protected USB packets → Windows code detector → primary delay fit → arrival fallback → RX4 joint spectral rescue → current-code confirmation and display smoothing → radar + received spectrum/waveform.

The raw payload is seven channels, 4096 frames, 48 kHz, signed 16-bit host samples. Firmware v0.6-RX2 keeps accelerated USB buffering and table CRC. High-band code confirmation is independent of direction-fit success. Every accepted direction still needs current acoustic evidence. No prior-angle veto or motor output is present.

The phone app is a separate local transmitter project. Original phone/PC reference files must match. Runtime logs live in the active workspace; checkpoint evidence and reports are frozen separately. See ROLES.md for responsibility boundaries.
