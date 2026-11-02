"""Write the HF1 handoff documents and preserve its local test evidence."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import shutil
import zipfile

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
STAGE=PROJECT/'stages/01-16-18kHz'
PHONE=PROJECT/'audio/phone/HF1-MP3'
OUT=Path(r'C:\Users\33296\Documents\Codex\2026-10-08\w\outputs')

def write(path,text):
    path.write_text(text.strip()+'\n',encoding='utf-8')

if not (STAGE/'README-before-HF1.md').exists():
    shutil.copy2(PROJECT/'README.md',STAGE/'README-before-HF1.md')
smoke=json.loads((ROOT/'logs/simple-ui-smoke-test.json').read_text(encoding='utf-8'))
assert smoke['passed'] and smoke['main_button_count']==3
shutil.copy2(ROOT/'logs/simple-ui-smoke-test.json',STAGE/'pico-ui-validation.json')
raw=Path(smoke['raw_log'])
shutil.copy2(raw,STAGE/raw.name)
events=[json.loads(line[len('# EVENT '):]) for line in raw.read_text(encoding='utf-8').splitlines() if line.startswith('# EVENT ')]
estimates=[e for e in events if e.get('event')=='beacon_estimate']
headers=[dict(re.findall(r'(\w+)=(\S+)',line)) for line in raw.read_text(encoding='utf-8').splitlines() if line.startswith('AUDIO ')]
capture={'purpose':'Real Pico/USB/GUI check in ambient room; no phone beacon played',
         'captured_bursts':smoke['raw_bursts'],'profiles':dict(Counter(e['profile'] for e in estimates)),
         'accepted_bearings':sum(bool(e['valid']) for e in estimates),
         'windows_with_4_code_hits':sum(e.get('code_channels',0)>=4 for e in estimates),
         'maximum_dropped_blocks':max(int(h['dropped']) for h in headers),
         'maximum_rx_stalls':max(int(h['rx_stall']) for h in headers),
         'observed_capture_detection_loop_hz':smoke['observed_detection_hz'],
         'observed_ui_refresh_hz':smoke['observed_ui_refresh_hz'],
         'phone_range_acceptance':'pending user test','raw_log':raw.name}
write(STAGE/'pico-capture-summary.json',json.dumps(capture,indent=2))
model=json.loads((STAGE/'model-validation.json').read_text(encoding='utf-8'))
mp3=json.loads((STAGE/'mp3-validation.json').read_text(encoding='utf-8'))
assert model['passed'] and mp3['passed']

write(STAGE/'README.md',r'''
# HF1 — 16–18 kHz phone test

**22 October 2026 · Stage 1 · Ready for user testing; physical range acceptance pending**

This stage adds a receiver for a known coded beacon in the actual 16–18 kHz band. The desktop application only captures and scans. It has no computer playback control or audio output backend. Play the supplied MP3 files on the Samsung S25 Ultra speaker.

The earlier high-frequency beacon occupied approximately 20–22 kHz. It is a different signal and will not match this receiver. The audible beacon remains available as the baseline.

## Start the test

1. Keep the existing wiring and connect the Pico by USB. Close other serial monitors.
2. Open `Start-16-18kHz.cmd` at the EE475 project root. The receiver starts stopped, with **16-18 kHz beacon (Stage 1)** selected. Select **Start Scan**.
3. Transfer `audio/phone/HF1-MP3/` or `releases/EE475-Phone-MP3-HF1.zip` to the phone.
4. Loop **01_LOCATE_16-18kHz.mp3**, initially about 0.5 m from the array. Keep one phone speaker unobstructed. Use a comfortable volume and keep it fixed throughout the comparison.
5. After a stable arrow appears with the phone physically in front, select **Set Front**. Keep the array fixed while moving the phone left and right.
6. Compare 0.5 m, 1 m and 1.5 m at the same phone volume, height and orientation. These are test distances, not validated operating limits.
7. In **Advanced**, enter the measured distance and select **Record 10 s**. The program saves a `range-test-*.json` file in `SEN0325-Pico-Setup/logs/`. Record the filename, volume and true source angle separately.

Use **02_LOCATE_Audible.mp3** with the **Audible beacon** receiver for an audible baseline. The two coded files use different digital levels, so do not compare their absolute received levels as calibrated frequency response.

## Which file to use

| File | Receiver / purpose | Expected display |
| --- | --- | --- |
| `01_LOCATE_16-18kHz.mp3` | 16–18 kHz coded localization | Code hits; arrow only when the geometry checks pass |
| `02_LOCATE_Audible.mp3` | Audible coded localization, 0.9–3.9 kHz | Baseline code hits and bearing |
| `11_TONE_1000Hz_level-only.mp3` | 1 kHz level reference | Read the 1 kHz tone level |
| `12_TONE_16000Hz_level-only.mp3` | 16 kHz level probe | Read the 16 kHz tone level |
| `13_TONE_17000Hz_level-only.mp3` | 17 kHz level probe | Read the 17 kHz tone level |
| `14_TONE_17500Hz_level-only.mp3` | 17.5 kHz level probe | Read the 17.5 kHz tone level |
| `15_TONE_18000Hz_level-only.mp3` | 18 kHz level probe | Read the 18 kHz tone level |

**TONE files do not contain the localization code. No arrow is expected.** Their digital RMS levels are equal. Use them to compare received strength at different frequencies and distances. Both receiver selections report these five level probes.

All files are actual 48 kHz, 320 kbps MP3s. The left channel is silent; the right carries the signal to reduce interference between two phone speakers. Player routing can vary. Avoid Bluetooth/headphones for this test. Disable player equalization, normalization and crossfade if enabled. The original lossless WAVs remain in `audio/phone/` as references.

## Read the measurements

- **Code: n/7** counts channels that matched the known beacon. Four are required before this stage attempts a direction fit.
- **16–18 kHz level** is median channel energy across that whole band, measured before spectral weighting.
- **Tone levels** are median channel RMS in ±150 Hz windows around 1/16/17/17.5/18 kHz. They update even when no localization code is detected.
- Levels are digital **dBFS**, not calibrated dB SPL. A less negative value means a stronger received signal. Pause phone playback to measure the background; a reading near that background is inconclusive.
- The arrow shows bearing only. The rings do not show range. Set Front changes the zero reference, not microphone timing calibration.
- Display refresh and capture/detection rate are different. This stage does not claim a completed latency improvement.

For example, a tone changing from −60 dBFS at 0.5 m to −70 dBFS at 1 m has dropped by 10 dB in this setup. Compare the same file, source volume and orientation. Changing to a phone speaker may improve the usable signal, but distance attenuation remains physical and must be measured.

## Scope and status

Implemented: band-matched code, lower crest factor within that band, partial spectral whitening, bounded multi-pair delay fitting, conservative direction confirmation, scanner-only UI, frequency probes and MP3 handoff.

Checked: generated-signal regression, negative examples, legacy audible regression, real Pico transport/GUI, MP3 spectrum and code compatibility after decoding. **No phone distance or physical angular-accuracy acceptance has been completed for HF1.** 16–18 kHz is not guaranteed inaudible.

Next changes to latency and longer-range behavior wait for this stage's feedback. See [progress notes](PROGRESS_NOTES.md), [change details](CHANGE_DETAILS.md) and [test sheet](TEST_NOTES.md).

## 中文快速说明

电脑只接收；手机外放单曲循环。测方向先放 `01_LOCATE_16-18kHz.mp3`，软件选 16–18 kHz，然后点 **Start Scan**。先测 0.5 米，稳定后 **Set Front**；保持音量和手机朝向不变，再测 1 米、1.5 米。

11–15 是纯音，只看右侧对应频率的 **Tone levels**，不出箭头正常。暂停播放看一下背景值，数值越不负，接收到的信号越强。测方向必须换回 01 或 02 编码音，并选对应的 Receiver。

这次先完成高频接收这一步。文件检查和 Pico 采集检查已通过，手机远距离是否改善由这次实测确认。
''')

write(STAGE/'PROGRESS_NOTES.md',f'''
# HF1 progress notes / 阶段汇报

**2026-10-22 · Stage 1 · Awaiting phone test**

这次先处理 16–18 kHz 的接收问题。检查代码后发现，原来的高频文件实际在约 20–22 kHz，和这次要测的频段不一致。现在加了真正的 16–18 kHz 编码音和对应检测器，也加强了窄带干扰处理与多麦克风时延拟合。

按本次要求，电脑端已经去掉播放功能，只做扫描。主界面保留 Start Scan、Set Front、Advanced 三个按钮。手机文件分两组：01/02 用于定位；11–15 的 1、16、17、17.5、18 kHz 纯音用于看接收强度。纯音没有定位编码，不出箭头正常。

目前做过的检查：

- 30 组生成信号，覆盖强信号、弱信号带频响衰减、窄带干扰、载波相位偏移和一条延迟反射。强信号等四类各 6 组的最终方向都通过；较弱且带频响衰减的 6 组中，4 组最终通过。仍然有弱信号失败，不能说远距离问题已经解决。
- 84 组负例，每组 3 个采集窗口，没有接受方向；包括纯音、噪声、错误编码和旧高频编码。另查了丢块、削波和数据形状异常的拒绝处理。
- 与旧检测器使用同频段、同编码、同一批生成样本做接收对比，部分弱信号能从不匹配变成匹配。对比的是编码检出率，不是实测距离或方向精度。
- 实际连接 Pico，采到 {capture['captured_bursts']} 个七路音频块，界面、开始/停止、频段切换、诊断窗口通过；丢块最大 {capture['maximum_dropped_blocks']}，RX stall 最大 {capture['maximum_rx_stalls']}。测试时没有播放手机信标。
- 7 份 MP3 均做了编码后再解码检查。16–18 kHz 定位音的目标频带能量占比约 99.9985%；两份编码音各 16 个截取窗口均能匹配编码。解码后的人工时延测试也通过。

下一步由手机外放实测：同音量、同朝向，先 0.5 米，再 1 米和 1.5 米。记下背景值、对应频率电平、Code 命中和方向是否稳定。拿到结果后再决定是输出端高频太弱、接近背景噪声，还是已经收到编码但方向拟合不稳定。

本阶段没有改 Pico 固件、接线、已有前向校准或采集调度。总延迟与更远距离的专项调整留到下一阶段，避免一次改太多而难以判断原因。

## English team note

HF1 adds an actual 16–18 kHz coded beacon and receiver. The previous high-frequency asset occupied approximately 20–22 kHz. The new path uses partial spectral whitening and a bounded multi-pair delay fit. The audible path is preserved.

The desktop UI is now receive-only. Seven phone MP3s are provided: two coded localization beacons and five equal-RMS level probes. Codec round-trip checks, generated-signal regression and a {capture['captured_bursts']}-burst real Pico transport/UI check passed. Phone distance performance and physical angular accuracy remain unverified. The weak colored-signal model still has rejected cases.

Next: compare 0.5/1/1.5 m with the S25 Ultra at fixed volume and orientation, then choose the next change from the recorded results. Broader latency and range changes are deferred until this feedback.
''')

write(STAGE/'CHANGE_DETAILS.md',f'''
# HF1 change details

**Stage 1 · 2026-10-22 · Host-side 16–18 kHz reception and phone-test handoff**

## Signal and receiver

`beacon_dsp.py` adds `coded-16-18` (16,000–18,000 Hz, 17,000 Hz nominal center). Its 4,096-sample known code repeats at 48 kHz. Twenty-four iterative clipping/spectral-projection steps select a lower-crest waveform while retaining the target spectrum. The exported waveform is not clipped. Peak amplitude is 0.35 full scale, versus 0.12 for the retained older beacons. This changes the emitted digital signal, not the sensor's analog gain. Old audible and 20–22 kHz templates remain unchanged.

`highband_dsp.py` is used only by this profile:

1. Validate shape, finite samples, packet health and clipping; clear temporal evidence on faults.
2. FFT the synchronous channels; calculate raw band RMS/dBFS before weighting.
3. Apply partial spectral whitening with exponent 0.65, bounded to 0.025–3.0, to reduce a dominant narrow spectral line and response tilt. Nulls are bounded rather than amplified without limit.
4. Match the known code. Require PNR ≥12.5 dB, peak-energy concentration ≥0.12, band RMS ≥0.25 PCM16 units and at least four channels. The old thresholds were 14.5 dB and 0.18. A plain frequency match cannot authorize a bearing.
5. Isolate the common code-arrival region (±96 samples) and combine two strong-signal or up to three weaker-signal bursts within 0.75 s.
6. Search bounded complex coherence across frequency for each microphone-pair delay, allowing a free carrier-phase intercept. The 17 kHz carrier phase alone cannot choose a direction. Reject poor coherence, narrow frequency support and flat delay curves.
7. Fit array geometry with robust weighting. At most 20% of pairs may be trimmed when at least ten are available. Report both all-pair and retained-pair residuals. Gates include retained RMS ≤1 sample, all-pair RMS ≤1.5 samples, horizontal projection 0.25–1.3 and quality ≥0.48.
8. Require two consistent bearings, then smooth with the existing geometry/front/mirror settings. Rejecting a direction clears the arrow; this is not a promise of continuous tracking.

This is digital processing. It cannot restore high-frequency acoustic energy that never reaches the microphones or claim increased analog microphone sensitivity.

## Interface and measurements

- `app_controls.py`: replaces playback/acquisition controls with `ScanControls`; no audio output backend.
- `sen0325_simple_view.py`: three main buttons (**Start Scan**, **Set Front**, **Advanced**); receiver selection, real band level and five tone-level probes. Phone Audio Files is inside Advanced. Existing calibration, reconnect, charts and trial recording remain.
- `sen0325_launcher.py`: explicit profile-to-center-frequency mapping, `--profile` selection, probe values in logged estimates, unchanged USB packet validation. Discard results from an older capture generation after stopping/switching.
- `Start-16-18kHz.cmd`: launch directly into this receiver with acquisition off. The existing Start-Localizer entry still defaults to the audible receiver; both use the same receive-only interface.
- `probe_levels`: median channel RMS, ±150 Hz around 1/16/17/17.5/18 kHz, dBFS. Reuses the high-band FFT. The audible path uses an additional FFT for these diagnostic values. No display gain or sound-pressure calibration is applied.
- `Record 10 s` includes the profile, manually entered distance, code hits, accepted directions, frequency levels and underlying log path. It does not record the phone volume, actual file or true angle automatically; write these on the test sheet.

## Phone assets and reproducibility

`audio/phone/HF1-MP3/` contains two 12.288 s coded files and five 20 s pure tones. Pure tones share −20 dBFS active-channel RMS and 30 ms fades. All assets have a silent left channel and an active right channel; the phone/player determines actual speaker routing.

Encoding: FFmpeg/libmp3lame, 48 kHz, 320 kbps CBR, compression quality 0, lowpass cutoff 22 kHz, joint stereo disabled. The explicit cutoff avoids relying on encoder-selected bandwidth. See the [official FFmpeg codec options](https://ffmpeg.org/ffmpeg-codecs.html#libmp3lame). `tests/generate_phone_mp3.py` creates the files and checks actual decoded spectra, level, clipping, channel routing and known-code compatibility. It uses the optional generation dependency `imageio-ffmpeg==0.6.0`; the receiver runtime still only needs the original requirements.

`mp3-validation.json` records filenames, hashes and decoder results. It tests files and artificial plane-wave delays after decoding, not a phone speaker or room. The 16–18 kHz decoded in-band energy fraction is 0.999985; each coded asset matched all 16 sampled windows. Pure tones were not accepted as directions.

## Evidence and limits

- `model-validation.json`: 30 positive generated cases, 84 three-window negative groups, corruption/clipping guards, legacy audible regression and an old/new receiver sensitivity comparison. Maximum accepted generated-case error {model['maximum_simulated_error_deg']}°, not a hardware angular specification. Median processing {model['median_processing_ms']} ms / maximum {model['maximum_processing_ms']} ms in this run; host load affects these figures.
- Receiver-only comparison uses the same 16–18 kHz template and samples for both algorithms. In the colored-response/noise case at source RMS 18, code-hit windows changed from 0/18 to 15/18. With an added narrow tone at source RMS 25, they changed from 0/18 to 18/18. The weaker RMS 8 and 12 cases remained 0/18. These are generated PCM amplitudes, not meters.
- `pico-ui-validation.json`: {capture['captured_bursts']} real bursts, seven channels, three buttons, 15 checks, no callback errors. Observed steady capture/detection-loop rate {capture['observed_capture_detection_loop_hz']} Hz; display refresh {capture['observed_ui_refresh_hz']} Hz. No phone source was played. Startup and USB warmup are not represented by the steady rate.
- `pico-capture-summary.json` and the copied raw launcher log preserve ambient-capture evidence.
- `controls-validation.json` and `english-ui-validation.json` cover scan state, late-burst rejection, English labels and layout. Offline UI checks make no hardware claim.

Pico `main.c`, the supplied RAM UF2, `runtime_tuning.py` and existing `array_geometry.json` are unchanged. No new GPIO wiring, firmware flash, ESP32 link or motor control is included. The 17 October weekly ZIP remains frozen. The pre-stage host snapshot is `before-stage-1.zip`; close the app before manually restoring from it. Use the old audible entry after a rollback because the old launcher does not support the new profile.

## Next acceptance gate

Use the test sheet to distinguish background-limited reception, missing code and inconsistent direction. Do not start general latency/range tuning until the phone comparison is reviewed. Reliable >1 m operation and inaudibility remain open measurements.
''')

write(STAGE/'TEST_NOTES.md',r'''
# HF1 phone test sheet / 手机测试记录

**Status: awaiting user measurements. Do not prefill results as passing.**

Record once per test session: date/time, room, phone/player, media volume, player effects, speaker orientation, source/array height, array orientation and any nearby equipment. Keep these fixed while changing distance. Test one source at a time.

## Level test / 强度

Play each TONE file in a loop. Select Start Scan and read the corresponding Tone levels value. Record roughly ten seconds, then pause playback and note the background. These files do not produce a localization arrow.

| File / Hz | Volume | Distance m | Background dBFS | Playing median dBFS | Notes |
| --- | --- | --- | --- | --- | --- |
| 1,000 | | 0.5 / 1 / 1.5 | | | |
| 16,000 | | 0.5 / 1 / 1.5 | | | |
| 17,000 | | 0.5 / 1 / 1.5 | | | |
| 17,500 | | 0.5 / 1 / 1.5 | | | |
| 18,000 | | 0.5 / 1 / 1.5 | | | |

Use separate rows or copies for each distance. If playing and background levels are almost equal, report that; do not interpret the background as a measured beacon. Equal digital file RMS does not mean equal acoustic phone output. Differences across frequencies include both speaker and microphone responses and the room.

## Direction test / 方向

Use 01_LOCATE_16-18kHz.mp3 with 16–18 kHz selected; use 02_LOCATE_Audible.mp3 with Audible beacon. Start at 0.5 m and set front with the source in front. Keep the array fixed, use measured source positions, and record each trial in Advanced > Record 10 s. Enter the measured distance before recording.

| File/profile | Volume | Distance m | True bearing ° | Code hits /7 | Valid windows/total | Bearing range/error | Saved JSON |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HF1 | | 0.5 | 0 / 45 / 90 | | | | |
| HF1 | | 1.0 | 0 / 45 / 90 | | | | |
| HF1 | | 1.5 | 0 / 45 / 90 | | | | |
| Audible | | same positions | | | | | |

A stable arrow alone is not proof of angle accuracy. Enter the actual marked source angle and compare it with the displayed bearing. Files use different digital levels, so the audible/high-band comparison is a practical beacon comparison, not a calibrated hardware frequency-response test.

## How to report a problem / 如何反馈

- No rise above background: report frequency, volume, distance and speaker orientation.
- Signal rises but Code remains below 4/7: report file/profile pair and save a trial.
- Code ≥4/7 but arrow disappears: report the on-screen reason and save a trial; inspect delay/geometry consistency next.
- Arrow points the wrong way: distinguish reversed left/right, a constant angular offset and random jumps. Include actual source angle.

中文：先比较暂停时的背景值，再记录播放值。测试期间不要变音量或转手机。纯音只看电平；定位必须用编码音。把距离、文件名和保存的 JSON 一起交回来，下一阶段再针对结果调整。
''')

write(PROJECT/'audio/phone/README.txt',r'''
PHONE AUDIO - CURRENT STAGE HF1 (2026-10-22)

Use HF1-MP3/ for the current phone test. It contains 7 MP3 files and instructions.
The computer application is receive-only; play the phone speaker externally.

HF1-MP3/01_LOCATE_16-18kHz.mp3: Stage 1 coded localization beacon (16-18 kHz).
HF1-MP3/02_LOCATE_Audible.mp3: audible coded localization baseline (0.9-3.9 kHz).
HF1-MP3/11-15_TONE_...mp3: 1/16/17/17.5/18 kHz level probes; no direction code.

LOSSLESS REFERENCE FILES
coded_16_18khz_stage1_right.wav: same HF1 code before MP3 encoding.
audible_beacon_right.wav: original weekly baseline, unchanged.
ultrasonic_experimental_right.wav: old 20.04-21.96 kHz experiment; not selectable
in the current simple UI and does not match the new 16-18 kHz receiver.

WAVs: 48 kHz, 16-bit stereo, 12.288 s, left silent/right active.
MP3s: 48 kHz, 320 kbps stereo, left silent/right active.
Phone range and high-frequency angular accuracy remain pending physical testing.
See ../../stages/01-16-18kHz/README.md for current operation and test notes.
''')

readme=(STAGE/'README-before-HF1.md').read_text(encoding='utf-8')
readme=readme.replace('**EE475 · Weekly milestone: 17 October 2026 · Desktop application v0.7 · Pico firmware v0.5**',
    '**EE475 · Current desktop stage: HF1, 22 October 2026 · Pico firmware v0.5**\n\nCurrent test: [HF1 — 16–18 kHz phone playback](stages/01-16-18kHz/README.md). Read the [stage report](stages/01-16-18kHz/PROGRESS_NOTES.md), [change details](stages/01-16-18kHz/CHANGE_DETAILS.md) and [test sheet](stages/01-16-18kHz/TEST_NOTES.md). The 17 October weekly release remains archived unchanged.')
readme=readme.replace('The current milestone is an **audible-beacon bench prototype**.',
    'The audible beacon is the demonstrated bench baseline; **HF1 adds experimental 16–18 kHz reception for phone testing**.')
readme=readme.replace('Keep computer playback off during a phone test.','The application only receives and scans; it has no computer playback control.')
readme=readme.replace('Play `audio/phone/audible_beacon_right.wav`','Loop `audio/phone/HF1-MP3/02_LOCATE_Audible.mp3`')
readme=readme.replace('on the phone in a loop','on the phone')
readme=readme.replace('**Start Radar**','**Start Scan**').replace('**Stop Radar**','**Stop Scan**')
readme=readme.replace(' to stop acquisition and **Stop Sound** to stop computer playback.',' to stop acquisition. Control playback on the phone.')
readme=readme.replace('Radar and computer playback are independent and both start off. The high-frequency option remains experimental and is not the demonstration baseline.',
    'Capture starts off. For HF1, open **Start-16-18kHz.cmd** and loop **audio/phone/HF1-MP3/01_LOCATE_16-18kHz.mp3** on the phone. Pure TONE files only update level probes; they do not produce a bearing. High-frequency phone acceptance remains pending.')
readme=readme.replace('English-named, ready-to-transfer phone WAV files and playback notes.','Current phone MP3 pack, lossless reference WAVs and playback notes.')
readme=readme.replace('| `tests/` |','| `stages/01-16-18kHz/` | Current stage README, progress/change notes, test sheet, evidence and pre-stage backup. |\n| `tests/` |')
readme=readme.replace('- Independent sound/radar controls and transferable phone audio.',
    '- Receive-only scan controls, transferable phone MP3s and per-frequency received-level diagnostics.\n- Experimental HF1 band-matched code detection, spectral interference weighting and bounded pair-delay localization.')
readme=readme.replace('# Repeat the offline signal-model and independent-control checks.', '# Repeat the offline signal-model and scanner-control checks.')
readme=readme.replace("& 'C:\\Tools\\Embedded\\venv\\Scripts\\python.exe' '.\\tests\\verify_controls.py'", "& 'C:\\Tools\\Embedded\\venv\\Scripts\\python.exe' '.\\tests\\verify_controls.py'\n& 'C:\\Tools\\Embedded\\venv\\Scripts\\python.exe' '.\\tests\\verify_highband_stage1.py'")
write(PROJECT/'README.md',readme)
for destination in [OUT/'EE475-README.md',PROJECT/'releases/Slack-Upload/README.md']:
    shutil.copy2(PROJECT/'README.md',destination)

guide=(PROJECT/'docs/USER_GUIDE.md').read_text(encoding='utf-8')
start=guide.index('## Normal phone test')+len('## Normal phone test')
end=guide.index('## Reading the display')
guide=guide[:start]+'''

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

'''+guide[end:]
write(PROJECT/'docs/USER_GUIDE.md',guide)
write(PROJECT/'tests/requirements-audio.txt','imageio-ffmpeg==0.6.0')

baseline=json.loads((STAGE/'before-stage-1-hashes.json').read_text(encoding='utf-8-sig'))
unchanged={}
for name in ('main.c','runtime_tuning.py','array_geometry.json'):
    expected=next(r['Hash'].lower() for r in baseline if Path(r['Path']).name==name)
    actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    assert actual==expected,(name,actual,expected)
    unchanged[name]=actual
uf2=ROOT/'firmware/sen0325_setup-RAM.uf2'
actual=hashlib.sha256(uf2.read_bytes()).hexdigest()
assert actual=='b10c5203c44cb7dff7ba48007f787e13fe8327fa6068835a0d74e92aa9e4350c'
unchanged['firmware/sen0325_setup-RAM.uf2']=actual
write(STAGE/'unchanged-hardware-assets.json',json.dumps(unchanged,indent=2))

phonezip=PROJECT/'releases/EE475-Phone-MP3-HF1.zip'
with zipfile.ZipFile(phonezip,'w',zipfile.ZIP_DEFLATED) as package:
    for path in sorted(PHONE.iterdir()):
        if path.is_file():package.write(path,'HF1-MP3/'+path.name)
with zipfile.ZipFile(phonezip) as package:
    assert package.testzip() is None
    assert len([i for i in package.namelist() if i.endswith('.mp3')])==7
shutil.copy2(phonezip,OUT/phonezip.name)
print(json.dumps({'docs_written':True,'capture_summary':capture,'phone_zip':str(phonezip)},indent=2))
