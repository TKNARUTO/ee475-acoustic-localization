# HF1 progress notes / 阶段汇报

**2026-10-22 · Stage 1 · Awaiting phone test**

这次先处理 16–18 kHz 的接收问题。检查代码后发现，原来的高频文件实际在约 20–22 kHz，和这次要测的频段不一致。现在加了真正的 16–18 kHz 编码音和对应检测器，也加强了窄带干扰处理与多麦克风时延拟合。

按本次要求，电脑端已经去掉播放功能，只做扫描。主界面保留 Start Scan、Set Front、Advanced 三个按钮。手机文件分两组：01/02 用于定位；11–15 的 1、16、17、17.5、18 kHz 纯音用于看接收强度。纯音没有定位编码，不出箭头正常。

目前做过的检查：

- 30 组生成信号，覆盖强信号、弱信号带频响衰减、窄带干扰、载波相位偏移和一条延迟反射。强信号等四类各 6 组的最终方向都通过；较弱且带频响衰减的 6 组中，4 组最终通过。仍然有弱信号失败，不能说远距离问题已经解决。
- 84 组负例，每组 3 个采集窗口，没有接受方向；包括纯音、噪声、错误编码和旧高频编码。另查了丢块、削波和数据形状异常的拒绝处理。
- 与旧检测器使用同频段、同编码、同一批生成样本做接收对比，部分弱信号能从不匹配变成匹配。对比的是编码检出率，不是实测距离或方向精度。
- 实际连接 Pico，采到 36 个七路音频块，界面、开始/停止、频段切换、诊断窗口通过；丢块最大 0，RX stall 最大 0。测试时没有播放手机信标。
- 7 份 MP3 均做了编码后再解码检查。16–18 kHz 定位音的目标频带能量占比约 99.9985%；两份编码音各 16 个截取窗口均能匹配编码。解码后的人工时延测试也通过。

下一步由手机外放实测：同音量、同朝向，先 0.5 米，再 1 米和 1.5 米。记下背景值、对应频率电平、Code 命中和方向是否稳定。拿到结果后再决定是输出端高频太弱、接近背景噪声，还是已经收到编码但方向拟合不稳定。

本阶段没有改 Pico 固件、接线、已有前向校准或采集调度。总延迟与更远距离的专项调整留到下一阶段，避免一次改太多而难以判断原因。

## English team note

HF1 adds an actual 16–18 kHz coded beacon and receiver. The previous high-frequency asset occupied approximately 20–22 kHz. The new path uses partial spectral whitening and a bounded multi-pair delay fit. The audible path is preserved.

The desktop UI is now receive-only. Seven phone MP3s are provided: two coded localization beacons and five equal-RMS level probes. Codec round-trip checks, generated-signal regression and a 36-burst real Pico transport/UI check passed. Phone distance performance and physical angular accuracy remain unverified. The weak colored-signal model still has rejected cases.

Next: compare 0.5/1/1.5 m with the S25 Ultra at fixed volume and orientation, then choose the next change from the recorded results. Broader latency and range changes are deferred until this feedback.
