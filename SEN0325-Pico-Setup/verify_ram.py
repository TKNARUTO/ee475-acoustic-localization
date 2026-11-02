"""Reject a UF2 unless every payload block targets RP2040 SRAM only."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("image", type=Path)
args = parser.parse_args()
data = args.image.read_bytes()
if not data or len(data) % 512:
    raise SystemExit("Invalid UF2 size")
seen = set()
addresses = []
for offset in range(0, len(data), 512):
    block = data[offset:offset + 512]
    magic0, magic1, flags, address, size, number, count, family = struct.unpack_from("<8I", block)
    if (magic0, magic1, struct.unpack_from("<I", block, 508)[0]) != (0x0A324655, 0x9E5D5157, 0x0AB16F30):
        raise SystemExit("Bad UF2 magic")
    if not 0 < size <= 476 or not 0x20000000 <= address < address + size <= 0x20042000:
        raise SystemExit(f"Refusing non-SRAM payload at {address:#x}")
    if not flags & 0x2000 or family != 0xE48BFF56 or count != len(data) // 512:
        raise SystemExit("Unexpected RP2040 family / block count")
    if number in seen:
        raise SystemExit("Duplicate UF2 block")
    seen.add(number)
    addresses.append((address, address + size))
if seen != set(range(len(data) // 512)):
    raise SystemExit("Missing UF2 block")
print(json.dumps({"path": str(args.image.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
                  "blocks": len(seen), "start": hex(min(a for a, b in addresses)),
                  "end_exclusive": hex(max(b for a, b in addresses)), "sram_only": True,
                  "flash_payload_blocks": 0}, indent=2))
