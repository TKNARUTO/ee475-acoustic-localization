# NodeMCU-32S deployment evidence

This public folder contains [BUILD.json](BUILD.json) and documentation. **The tested binary is not distributed:** it embeds local compiler paths and is retained in the maintainer's private archive. Public source, exact build configuration, source hashes and the tested deployment hash remain available. No replacement binary or board firmware change was made for this packaging adjustment.

The recorded deployment was a **4 MiB synthesized merged build** written at offset **0x0**, not a readback of the owner's old board. Its SHA256 remains **36610897ee2f78f5fe8153d043df68cbb00b5a7cf040c7d3475dc2b3d77cda6b**. `deployment_image_name` identifies that local artifact; `image_distributed=false` means it is not a download path.

Built with Arduino CLI1.4.1, esp32 by Espressif Systems3.3.12, board NodeMCU-32S, FQBN esp32:esp32:nodemcu-32s. The actual build was named sketch_nov12a.ino; its source and three headers are byte-identical to this canonical sketch. Different sketch names may change build metadata, so rebuilding need not give the same binary hash. BUILD.json records source hashes and linker statistics.

Use the [Arduino instructions](../README_EN.md) to compile and upload the source, preserving the existing board application first. Re-detect the serial port; COM6 is only the owner's observed port. This is classic NodeMCU-32S, not ESP32-S3. A rebuilt artifact has not automatically inherited the original hardware validation; record its new hash and test it.

This image was written and verified, then used in Flash trials03–05. It only receives/ACKs on GPIO16/17 and prints diagnostics. There are no motor commands. Current stale/invalid diagnostic angles must not be treated as fresh motion targets.
