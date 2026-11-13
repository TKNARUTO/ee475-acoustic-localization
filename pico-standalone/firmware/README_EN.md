# Pico persistent firmware release
This is the deployed **v0.2-link_diag** Flash image for Raspberry Pi Pico / RP2040. Its UF2 SHA256 is **11958e9310926e856f01359c10c4832cffc046cb64a8edebe675b76e3984caa0**.

- pico_gap_standalone-v0.2.uf2: persistent application, not the legacy RAM capture firmware.
- pico_gap_standalone-v0.2.elf: matching symbols and ELF, for inspection.
- BUILD.json: exact numeric options and SHA256 of all ten matching source files.
- resource-audit.json: linker sections, buffer sizes and static stack findings. These do not establish runtime stack/heap high water.

Built with Pico SDK2.3.1, Arm GNU14.2.Rel1/GCC14.2.1; SDK board pico. INTEGER_FFT and INTEGER_FAST are ON; WHITEN_FLOAT, MAG_CACHE and PICO_NO_FLASH are OFF. See [build instructions](../README_EN.md). Do not omit those options and assume the default CMake build produces this image.

Before replacing another user's application, back up its Flash. Hold BOOTSEL while plugging in USB, then copy the UF2 onto RPI-RP2, or use picotool2.3.1 load -v followed by reboot. This replaces the application. Normal standalone startup does not require the PC to reload firmware. USB serial may enumerate at a new COM port.

Load/verify succeeded. Background Flash communication, software reboot and operation without a Pico serial client were tested. The earlier positive phone trial used the same source/options in RAM. A fresh known-angle phone test and physical cold power-cycle remain open. This image does not yet meet fresh-target/0.2–0.5s acceptance; no motor commands.

The public ELF has debug paths removed; its loadable binary payload matches the original byte for byte. The original debug ELF remains local. UF2 is unchanged.
