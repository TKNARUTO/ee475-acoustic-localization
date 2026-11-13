# Beacon Loop 1.2 — local phone transmitter

[Install APK](releases/BeaconLoop-1.2.apk) · [Release record](CHANGELOG_EN.md) · [Matching audio](../audio/phone/HF2-gap-test/README_EN.md)

Beacon Loop plays a local audio file repeatedly, with play/pause controls and an optional bounded level adjustment. The only bundled/default signal is **HF2 gap, 18–22 kHz**. The UI is English. Runtime platform: **Android 8.0/API 26 or later**, target API 35, package `org.ee475.beaconloop`, version 1.2 / code 3.

**Player import is not receiver configuration.** The current independent Pico recognizes a fixed HF2 gap reference; choosing another phone file does not install a new Pico template. Use the bundled HF2 file for this project. Compatible custom-reference import belongs to the archived Windows + Pico combo, whose launcher loads a different capture firmware. Do not run both workflows on the same board/serial port. The computer remains receive-only.

## Use

1. Install the APK. Android may require permission for the app opening the APK to install packages.
2. Open Beacon Loop. **Use HF2 gap beacon** restores the matching built-in audio. **Choose audio file** selects a local file for general loop playback.
3. Press **Play loop** and set the phone media volume. **Pause** stops playback. The foreground notification also provides playback controls.
4. Keep **Normalize** off for baseline comparisons. This is the fresh-install default; an existing saved choice is remembered. Record file, volume, position, phone orientation and deliberate pauses.
5. The current Pico starts acquisition independently; open the passive Windows monitor only to inspect telemetry. It does not send the phone file to Pico.

Supported formats depend on the phone's Android decoder. Input must be mono/stereo, at most 120 seconds, at most 64 MiB source and 32 MiB decoded PCM. Audio is decoded once and looped using a static AudioTrack buffer. Existing silence, fades and codec padding are preserved. Prefer WAV for controlled comparisons.

HF2 gap contains 2048 active samples then 2048 silent samples at 48 kHz: approximately 42.667 ms + 42.667 ms. The app does not stop/restart AudioTrack for each pulse. The 12.288-second WAV retains its original boundary fades. Neither exact acoustic gaplessness, background/screen-off operation nor every S25 Ultra audio-processing condition has a complete device acceptance record here.

## Optional Normalize

Normalize applies a common constant gain to all channels. Maximum gain is **+3 dB**; the requested peak ceiling is **−3 dBFS**. Loud inputs may be attenuated, silent input remains unchanged, and PCM quantization still applies. It does not change code, frequency, timing or channel layout, calibrate a microphone ADC, remove room reflections or guarantee greater range. Phone equalization, audio processing and speaker response remain external variables.

## Source and build

| File | Role |
|---|---|
| app/src/main/java/org/ee475/beaconloop/MainActivity.java | File picker, HF2 reset, English controls and status |
| app/src/main/java/org/ee475/beaconloop/LoopService.java | PCM loop, notification, persisted settings and audio focus |
| app/src/main/java/org/ee475/beaconloop/AudioLoader.java | Decode and enforce duration/channel/memory bounds |
| app/src/main/java/org/ee475/beaconloop/PcmGain.java | Optional bounded constant gain |
| app/src/main/assets/gap-beacon.wav | Fixed HF2 gap default, identical to the phone WAV |
| tests/PcmGainTest.java | Nine host gain checks |
| Build.cmd / Build.ps1 | Windows resource/Java/DEX/APK build and signing |
| toolchain.example.json | Example local tool paths; not a ready-to-use machine configuration |

The recorded 1.2 build used **JDK 25.0.4.1+1**, Android platform API 35 and the Android 15 build-tools package. Java compiles with `-source 8 -target 8`; this is a bytecode/source setting, not a claim that the build requires JDK 8. The build uses aapt2, javac/jar, D8, Python, zipalign and apksigner; no Gradle daemon is required.

Copy `toolchain.example.json` to local `toolchain.json` and set the Java, platform JAR, build-tools, Python and existing keystore paths. Use an ASCII source/build path; `source_alias` may be null unless a matching alias is intentionally configured. Set `EE475_KEYSTORE_PASS` in the current terminal; set `EE475_KEY_PASS` only for a different key-entry password. Run `Build.cmd`. Missing keys or credentials stop the build: no replacement signing identity is created automatically. SDKs, JDKs and signing keys remain outside the public package. The app itself has no network runtime requirement.

## Signing and validation limits

The supplied 1.2 APK uses original 1.0's signing identity. It can follow that identity's upgrade path, but cannot directly update the imported differently signed 1.1. Preserve needed application state before deciding how to replace such an installation. A developer build signed with a different key cannot update the supplied identity; use a consistent team signing process. This APK is a team test artifact, not a Play Store release.

`validation.json` records the 5 November 2026 offline build, v2/v3 signature verification, signer comparison, ZIP alignment, matching waveform and nine gain checks. Those checks do not certify all device installation, file-picker, focus recovery, screen-off playback or physical localization behavior. This documentation revision did not rebuild/install the APK or play audio.

Declared permissions cover foreground service, media-playback foreground service and notifications. There is no declared network, microphone recording or broad storage permission. Local file selection uses the Android document picker and a private cached copy. See the [current Pico instructions](../pico-standalone/README_EN.md) for receiver limitations.
