"""Create low-level 1 kHz tone files with a visible 3 s on / 3 s off cadence."""
import array
import math
from pathlib import Path
import sys
import wave

root = Path(__file__).resolve().parent
rate = 48000
tone = array.array("h", (round(0.08 * 32767 * min(1, i / (rate * .02),
    (3 * rate - i - 1) / (rate * .02)) * math.sin(2 * math.pi * 1000 * i / rate))
    for i in range(3 * rate)))
if sys.byteorder != "little":
    tone.byteswap()
sound = tone.tobytes()
for name, data in (("1kHz-3s.wav", sound),
                   ("1kHz-3s-on-3s-off.wav", (sound + bytes(len(sound))) * 4)):
    with wave.open(str(root / name), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(data)
    print(root / name)
