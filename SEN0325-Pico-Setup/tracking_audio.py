"""Generate the selected diagnostic frequency; never change system volume/output."""
import array
import math
import sys
import wave


def prepare_tone_files(root, frequency):
    if not 300 <= frequency <= 22000:
        raise ValueError("Frequency must be within 300-22000 Hz.")
    if frequency == 1000:
        short, pattern = root / "1kHz-3s.wav", root / "1kHz-3s-on-3s-off.wav"
    else:
        folder = root / "test-tones"
        folder.mkdir(exist_ok=True)
        short, pattern = folder / f"{frequency}Hz-3s.wav", folder / f"{frequency}Hz-3s-on-3s-off.wav"
    if not short.exists() or not pattern.exists():
        rate = 48000
        samples = array.array("h", (round(0.08 * 32767 * min(1, i / (rate * .02),
            (3 * rate-i-1) / (rate * .02)) * math.sin(2 * math.pi * frequency * i / rate))
            for i in range(3 * rate)))
        if sys.byteorder != "little":
            samples.byteswap()
        tone = samples.tobytes()
        for path, data in ((short,tone), (pattern,(tone + bytes(len(tone))) * 4)):
            if path.exists():
                continue
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(rate)
                output.writeframes(data)
    for path, seconds in ((short,3),(pattern,24)):
        with wave.open(str(path),"rb") as source:
            if (source.getnchannels(),source.getsampwidth(),source.getframerate(),source.getnframes()) != (1,2,48000,seconds*48000):
                raise ValueError(f"Unexpected test-audio format: {path}")
    return short, pattern
