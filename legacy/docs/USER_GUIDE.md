# User Guide

## Normal phone test

The desktop app only receives and scans. Play the matching MP3 on the Samsung S25 Ultra speaker. Use one source at a fixed, comfortable volume. The [HF1 stage README](../stages/01-16-18kHz/README.md) describes the current high-frequency test and its limits.

For the audible baseline, open `Start-Localizer.cmd`, loop `audio/phone/HF1-MP3/02_LOCATE_Audible.mp3` and leave **Audible beacon** selected. For the new high-band test, open `Start-16-18kHz.cmd` and loop `01_LOCATE_16-18kHz.mp3` with **16-18 kHz beacon (Stage 1)** selected. Select **Start Scan** when Pico is connected.

## Main controls

| Control | Action |
| --- | --- |
| Start Scan / Stop Scan | Enable or pause capture and detection. |
| Set Front | Save the current valid source direction as 0°. |
| Advanced | Reconnect, mirror view, channel diagnostics, phone audio folder and trial recording. |
| Receiver dropdown | Choose the matching audible or 16–18 kHz coded detector; preserves scan state. |

The current UI has no computer playback function. The five TONE MP3s report frequency levels only, with no expected arrow. Use the coded LOCATE files to test direction. Both receiver profiles show the 1/16/17/17.5/18 kHz tone probes. These are median channel RMS values in ±150 Hz windows, in dBFS, not calibrated sound pressure. Record paused background as well as playing levels.

## Reading the display

0° is front; angles increase clockwise: 90° right, 180° rear, 270° left. The arrow indicates an accepted estimated bearing. Ring radius is decorative and has no distance scale. A quality score is a heuristic consistency score, not a probability of correctness. Target RMS is digital signal amplitude; it is not calibrated sound pressure.

The detector analyzes the known code within the chosen band. A bandpass alone would also accept unrelated sounds in the same band; code matching adds rejection. The microphones still capture broadband samples: software decides which samples contain the desired beacon.

An absent arrow means the receiver is paused, the code was not detected, a direction is ambiguous, the input is clipped, capture integrity failed, or the estimate became stale. This is preferable to holding an old direction after the source is lost. The display animates between measured bearings; it does not predict motion.

## Front reference and mirror view

Place the phone physically in front of the array and wait for a stable arrow. Select **Set Front**. Without moving the array, move the phone toward the physical right and left. If the displayed sense is reversed, enable **Mirror view** in Advanced and set front again. These settings are saved in `SEN0325-Pico-Setup/array_geometry.json`.

Setting front changes the angular reference; it does not calibrate microphone timing or prove angle accuracy.

## Record a trial

In Advanced, enter a distance measured with a ruler or tape and select **Record 10 s**. Keep the source and array fixed for the trial. Results are written as `SEN0325-Pico-Setup/logs/range-test-*.json` with valid-window fraction, code detections and per-window estimates. The entered distance is a test label; the software does not measure it. Record the true source angle separately for angular-error evaluation.

For the next acceptance test, use marked angles such as 0°, 45°, 90°, 180° and 270°, then repeat at measured distances such as 0.5, 1.0 and 1.5 m. These are proposed tests, not validated operating limits. Repeat with unrelated speech/music and in more than one room.

## Connection troubleshooting

- **Waiting for Pico:** hold BOOTSEL while connecting USB; release when RPI-RP2 appears. The launcher can load the validated RAM image.
- **Serial port unavailable:** close other copies of the application and Arduino/VS Code serial monitors, then use Advanced → Reconnect Pico. Connect one Pico.
- **No code detected:** check the audio profile/file pair, phone playback and volume. Use the audible file before trying the high-frequency experiment.
- **Clipping:** reduce playback volume or move the source farther away.
- **Ambiguous bearing or inconsistent delay:** try the audible profile, a single speaker, a fixed source and fewer nearby reflecting surfaces. Inspect the channel table and record a trial; do not interpret fluctuating output as verified tracking.
- **Old interface still displayed:** close the previously opened window and run `Start-Localizer.cmd` again. Source edits take effect on the next process launch.

Runtime diagnostics are stored in the workspace `logs/` folder. Selected historical evidence is indexed in `reports/validation/`. Diagnostic logs store metrics and estimates; capture bursts are normally processed in memory, not continuously saved as recordings.
