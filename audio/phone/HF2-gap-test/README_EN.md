# Current fixed HF2 gap phone signal

Use `01_LOCATE_18-22kHz_43ms-gap.wav` or its MP3. Beacon Loop 1.2's bundled WAV is byte-identical to this WAV. This is the active signal for the independent Pico receiver, not an optional replacement for an older 19–21 kHz preset.

| Property | Value |
|---|---|
| Nominal occupied band | 18,000–22,000 Hz; nominal center 20,000 Hz |
| Sample rate / PCM | 48,000 Hz / signed 16-bit WAV |
| Container / active channel | Stereo; left samples are zero, signal on right |
| Period | 4096 samples = 85.333 ms |
| Active / silent part | 2048 + 2048 samples = 42.667 + 42.667 ms |
| WAV length | 589,824 frames = 12.288 s = 144 periods |
| Measured right-channel PCM bounds | -11468 to 10923 |
| WAV SHA-256 | `e182fddee2615ed15b826e9d781c041ae557e59fcb6aa2ed7feb6274e3e9b9a1` |
| MP3 SHA-256 | `0aa6cec03b66ef44d4708ea3cbc2adefab025f5b5b3c481bb2f71f8ed4cd69bb` |

The silence and original boundary fades are part of the code; do not trim or stretch them. Prefer WAV for repeatable waveform comparisons. MP3 encoding/decoder padding and phone processing can affect the physical loop boundary, and software looping alone is not proof of acoustic gaplessness.

The independent Pico uses this fixed reference and begins scanning automatically. The Windows program is a passive direction/timing monitor. Changing the phone file does not change the Pico template. The archived PC+Pico combo has a separate compatible-reference import workflow and loads old capture firmware; do not confuse its launcher with the independent monitor.

Platform: Beacon Loop 1.2 requires Android 8.0/API 26+, targets API 35. Start with Normalize off, fixed position/orientation and recorded media volume. If enabled, gain is capped at +3 dB with a −3 dBFS peak target; it does not change the receiver reference or guarantee range. Energy near 18 kHz may be audible. Speaker bandwidth, geometry, room reflections and hearing vary; no fixed range or inaudibility claim is made. The PC should not play the beacon.

See [phone player instructions](../../../android-player/README_EN.md) and [Pico instructions](../../../pico-standalone/README_EN.md).
