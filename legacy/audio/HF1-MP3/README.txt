EE475 HF1 - PHONE PLAYBACK TEST PACK (2026-10-22)

The computer application is a receiver only. Play these MP3s on the Samsung
S25 Ultra speaker, with a single file on repeat. Do not play the computer.

FILES FOR DIRECTION / RADAR ARROW
01_LOCATE_16-18kHz.mp3 - coded 16-18 kHz beacon, Stage 1 receiver profile.
02_LOCATE_Audible.mp3 - coded 0.9-3.9 kHz beacon, Audible beacon profile.
These are 12.288-second known-code recordings. Choose the matching receiver.

FILES FOR FREQUENCY / DISTANCE LEVEL COMPARISON ONLY
11_TONE_1000Hz_level-only.mp3
12_TONE_16000Hz_level-only.mp3
13_TONE_17000Hz_level-only.mp3
14_TONE_17500Hz_level-only.mp3
15_TONE_18000Hz_level-only.mp3
Each tone is 20 seconds, equal digital RMS (-20 dBFS in the active channel),
with 30 ms fades. These tones do NOT contain the localization code.
Read the corresponding Tone levels field; no radar arrow is expected.

All MP3s: 48 kHz, 320 kbps, stereo, left silent and right carrying the signal.
Speaker routing depends on the player/phone. Keep orientation fixed and avoid
covering the active speaker. Disable player EQ, normalization and crossfade
for a repeatable comparison. Do not use Bluetooth or headphones for this test.

TEST
1. Open Start-16-18kHz.cmd in the EE475 folder and select Start Scan.
2. Play 01_LOCATE_16-18kHz.mp3 on the phone, initially about 0.5 m away.
3. After a stable arrow appears, use Set Front with the phone in front.
4. At the SAME phone volume and orientation, compare 0.5 m, 1 m and 1.5 m.
   Advanced > Record 10 s saves a trial; manually enter the measured distance.
5. Try the TONE files at the same distances and read 1/16/17/17.5/18 kHz levels.
   dBFS is received digital level, not calibrated sound pressure or distance.
6. Use 02_LOCATE_Audible.mp3 with Audible beacon selected as a direction baseline.

Check the idle/background level too. If a tone level barely changes when you
pause playback, the received tone is near the background or is not reaching
the sensor. Less negative dBFS means a stronger received signal.

The MP3s passed file/decoder checks, including code detection after decoding.
Physical phone range and accuracy are still awaiting this test. High-frequency
sound is not guaranteed inaudible; use a comfortable volume, not maximum.

CHINESE QUICK NOTES
电脑只扫描，手机外放单曲循环。
测箭头：01 高频编码音 / 02 可听编码音，要选对应 Receiver。
测强度：11-15 纯音只看右侧 Tone levels，不出现方向箭头是正常的。
保持音量和手机朝向不变，依次测 0.5、1、1.5 米；先暂停播放看背景值。
Advanced 里输入实测距离，点 Record 10 s，记录保存在程序 logs 文件夹。
这是待实测的阶段版本；不能用文件检查结果代替手机远距离测试。
