# Beacon Loop 1.2 — 手机本地循环播放器

[安装 APK](releases/BeaconLoop-1.2.apk) · [版本记录](CHANGELOG_ZH.md) · [匹配音频](../audio/phone/HF2-gap-test/README_ZH.md)

Beacon Loop 将本地音频循环播放，提供播放／暂停及可选的受限音量调整。唯一内置且默认的信号是 **HF2 gap，18–22 kHz**。程序界面为英文。运行平台为 **Android 8.0/API 26 或以上**，目标 API 35；包名 `org.ee475.beaconloop`，版本 1.2／版本号 3。

**播放器导入不等于接收器配置。** 当前独立 Pico 只识别固定 HF2 gap 参考；选择另一手机文件不会给 Pico 安装新模板。本项目请用随包 HF2 文件。支持兼容自定义参考导入的是归档的 Windows＋Pico 组合，它的启动器加载另一套旧采集固件；不要让两个流程同时使用同一块板和串口。电脑始终只接收。

## 使用

1. 安装 APK；Android 可能要求允许打开 APK 的应用安装程序。
2. 打开 Beacon Loop。Use HF2 gap beacon 恢复匹配的内置信号；Choose audio file 选择本地文件作一般循环播放。
3. 点击 Play loop，调整手机媒体音量；Pause 暂停。前台通知也提供播放控制。
4. 基线比较先关闭 Normalize。新安装默认关闭，但已有设置会被记住。记录文件、音量、位置、手机朝向及主动暂停时刻。
5. 当前 Pico 自主启动采集；电脑监视器用于观察遥测，不会把手机文件传入 Pico。

格式支持由手机 Android 解码器决定。输入限单／双声道、最长 120 秒、源文件不超过 64 MiB、解码 PCM 不超过 32 MiB。文件解码一次后，以静态 AudioTrack 缓冲区循环；原有静音、渐变和编码填充保留。可控比较优先 WAV。

HF2 gap 在 48 kHz 下先发声 2048 点、再静音 2048 点，约 42.667 ms＋42.667 ms。播放器不会为每个脉冲停止再启动 AudioTrack；12.288 秒 WAV 原始首尾渐变也保留。这里没有覆盖所有实物无缝循环、后台／熄屏或 S25 Ultra 音效处理条件的完整设备验收记录。

## 可选 Normalize

Normalize 对全部通道施加同一恒定增益，最多 **+3 dB**，目标峰值上限为 **−3 dBFS**。较响的输入可能衰减，静音不变；仍有 PCM 量化。它不改变编码、频率、时序或通道，不校准麦克风 ADC，不消除房间反射，也不保证更远距离。手机均衡器、处理和扬声器频响仍是外部变量。

## 源码与构建

| 文件 | 作用 |
|---|---|
| app/src/main/java/org/ee475/beaconloop/MainActivity.java | 文件选择、HF2 复位、英文控制和状态 |
| app/src/main/java/org/ee475/beaconloop/LoopService.java | PCM 循环、通知、设置保存及媒体焦点 |
| app/src/main/java/org/ee475/beaconloop/AudioLoader.java | 解码及时间／声道／内存限制 |
| app/src/main/java/org/ee475/beaconloop/PcmGain.java | 可选受限恒定增益 |
| app/src/main/assets/gap-beacon.wav | 与手机 WAV 相同的固定 HF2 默认信号 |
| tests/PcmGainTest.java | 九项主机增益检查 |
| Build.cmd / Build.ps1 | Windows 资源、Java、DEX、APK 构建与签名 |
| toolchain.example.json | 本地路径示例，不是已配置的工具环境 |

1.2 的记录构建环境为 **JDK 25.0.4.1+1**、Android 平台 API 35 和 Android 15 build-tools 包。Java 使用 `-source 8 -target 8`，这是源码／字节码设置，不代表必须使用 JDK 8。流程使用 aapt2、javac/jar、D8、Python、zipalign 和 apksigner，不需要 Gradle 后台进程。

将 `toolchain.example.json` 复制为本地 `toolchain.json`，配置 Java、平台 JAR、build-tools、Python 及已有密钥库路径。源码／构建路径使用 ASCII；未有意配置匹配别名时，`source_alias` 可为 null。在当前终端设置 `EE475_KEYSTORE_PASS`；只有条目密码不同才另外设置 `EE475_KEY_PASS`，再执行 `Build.cmd`。缺少密钥或凭据会终止构建，不自动生成替代签名身份。SDK、JDK 和密钥不进入公开包；应用运行本身不要求联网。

## 签名与验证范围

随包 1.2 沿用原 1.0 签名，可沿该身份升级；不能直接覆盖另一签名的导入 1.1。决定替换前应保留需要的应用状态。开发者另签的 APK 也不能直接覆盖原身份，应使用一致的团队签名流程。本 APK 用于团队测试，不是 Play Store 发布版本。

`validation.json` 记录 2026 年 11 月 5 日离线构建、v2/v3 签名、身份比较、ZIP 对齐、波形匹配和九项增益检查。这不等于设备安装、文件选择、媒体恢复、熄屏播放或实物定位的完整验收。本次文书整理没有重建／安装 APK，也没有播放音频。

声明的权限为前台服务、媒体播放前台服务和通知，不含网络、麦克风录音或广泛存储权限。本地文件通过 Android 文档选择器选择并缓存到应用私有区域。接收端限制见[当前 Pico 说明](../pico-standalone/README_ZH.md)。
