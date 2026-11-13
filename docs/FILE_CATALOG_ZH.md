# 公开项目文件清单

说明基准日期：2026-11-12。共 237 个选中文件。这是本地发布选取，不代表已经推送 GitHub 或通过硬件验收。

当前分工：Pico 计算方向，NodeMCU-32S 接收并回执，安卓播放信标，电脑监控可选。根目录 Start.cmd 和 Update.cmd 不烧录固件。legacy 仅保留最终 Pico + 电脑对照模板及其精确匹配 ZIP。

运行日志、原始录音、密钥、设备备份、本机设置和构建缓存不选入。公开测试源码与指定固件发布保留。用户提供的 PDF、DOCX、PPTX 参考保留原语言。SHA256SUMS.txt 覆盖除自身以外的每个选中文件。

[English](FILE_CATALOG_EN.md) · [机器可读 CSV](FILE_CATALOG.csv)

| 文件 | 职责 | 功能 |
|---|---|---|
| `.gitattributes` | 项目设置、说明与完整性 | Git 文本、二进制与换行规则 |
| `.gitignore` | 项目设置、说明与完整性 | 阻止本地日志、构建、录音与密钥进入 Git |
| `AGENTS.md` | 项目设置、说明与完整性 | 仓库约束与代理交接入口 |
| `README.md` | 项目设置、说明与完整性 | 使用设置、文件职责与验证边界 |
| `README_EN.md` | 项目设置、说明与完整性 | 使用设置、文件职责与验证边界（英文版） |
| `README_ZH.md` | 项目设置、说明与完整性 | 使用设置、文件职责与验证边界（中文版） |
| `SHA256SUMS.txt` | 项目设置、说明与完整性 | 除校验文件自身外所有选中文件的 SHA256 |
| `Setup-Windows.ps1` | 项目设置、说明与完整性 | 准备可选 Windows 监控依赖 |
| `Start.cmd` | 项目设置、说明与完整性 | 打开或聚焦当前独立监控，不烧录固件 |
| `Update.cmd` | 项目设置、说明与完整性 | 检查并重启本地监控，不下载 Git 更新或烧录 |
| `android-player/Build.cmd` | 安卓本地循环播放端 | 安卓构建脚本的 Windows 入口 |
| `android-player/Build.ps1` | 安卓本地循环播放端 | 使用已配置的本地 SDK 构建安卓应用 |
| `android-player/CHANGELOG.md` | 安卓本地循环播放端 | 版本变更及其范围、状态 |
| `android-player/CHANGELOG_EN.md` | 安卓本地循环播放端 | 版本变更及其范围、状态（英文版） |
| `android-player/CHANGELOG_ZH.md` | 安卓本地循环播放端 | 版本变更及其范围、状态（中文版） |
| `android-player/README.md` | 安卓本地循环播放端 | 使用设置、文件职责与验证边界 |
| `android-player/README_EN.md` | 安卓本地循环播放端 | 使用设置、文件职责与验证边界（英文版） |
| `android-player/README_ZH.md` | 安卓本地循环播放端 | 使用设置、文件职责与验证边界（中文版） |
| `android-player/app/src/main/AndroidManifest.xml` | 安卓本地循环播放端 | 安卓应用身份、权限与服务声明 |
| `android-player/app/src/main/assets/gap-beacon.wav` | 安卓本地循环播放端 | 发射与参考波形，必须与接收端模板匹配 |
| `android-player/app/src/main/java/org/ee475/beaconloop/AudioLoader.java` | 安卓本地循环播放端 | 将选中的音频解码为播放用 PCM |
| `android-player/app/src/main/java/org/ee475/beaconloop/LoopService.java` | 安卓本地循环播放端 | 手机本地前台循环播放服务 |
| `android-player/app/src/main/java/org/ee475/beaconloop/MainActivity.java` | 安卓本地循环播放端 | 安卓音频选择与简单播放操作 |
| `android-player/app/src/main/java/org/ee475/beaconloop/PcmGain.java` | 安卓本地循环播放端 | 受限的可选 PCM 增益，不静默改变频率 |
| `android-player/app/src/main/res/drawable/ic_beacon.xml` | 安卓本地循环播放端 | 组件实现或可复现辅助程序：ic_beacon.xml |
| `android-player/app/src/main/res/values/styles.xml` | 安卓本地循环播放端 | 组件实现或可复现辅助程序：styles.xml |
| `android-player/releases/BeaconLoop-1.2.apk` | 安卓本地循环播放端 | 可安装的安卓本地信标循环播放器 |
| `android-player/sdk-downloads.json` | 安卓本地循环播放端 | 可复现安装所需的 SDK 依赖来源声明 |
| `android-player/tests/PcmGainTest.java` | 安卓本地循环播放端 | PCM 增益、幅度边界与削顶行为检查 |
| `android-player/toolchain.example.json` | 安卓本地循环播放端 | 本地工具链设置示例，不含真实凭据 |
| `android-player/tools/merge_apk.py` | 安卓本地循环播放端 | 本地构建时组合安卓 APK 组件 |
| `android-player/validation.json` | 安卓本地循环播放端 | 组件验证结果与适用边界 |
| `audio/README.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界 |
| `audio/README_EN.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界（英文版） |
| `audio/README_ZH.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界（中文版） |
| `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3` | 固定 HF2 发射与参考音频 | 发射与参考波形，必须与接收端模板匹配 |
| `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav` | 固定 HF2 发射与参考音频 | 发射与参考波形，必须与接收端模板匹配 |
| `audio/phone/HF2-gap-test/README.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界 |
| `audio/phone/HF2-gap-test/README.txt` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界 |
| `audio/phone/HF2-gap-test/README_EN.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界（英文版） |
| `audio/phone/HF2-gap-test/README_ZH.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界（中文版） |
| `audio/phone/README.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界 |
| `audio/phone/README.txt` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界 |
| `audio/phone/README_EN.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界（英文版） |
| `audio/phone/README_ZH.md` | 固定 HF2 发射与参考音频 | 使用设置、文件职责与验证边界（中文版） |
| `docs/FILE_CATALOG.csv` | 项目设置、说明与完整性 | 完整选中文件职责与功能索引 |
| `docs/FILE_CATALOG.md` | 项目设置、说明与完整性 | 完整选中文件职责与功能索引 |
| `docs/FILE_CATALOG_EN.md` | 项目设置、说明与完整性 | 完整选中文件职责与功能索引（英文版） |
| `docs/FILE_CATALOG_ZH.md` | 项目设置、说明与完整性 | 完整选中文件职责与功能索引（中文版） |
| `docs/HARDWARE_EN.md` | 项目设置、说明与完整性 | 已核对板型、GPIO 接线与供电职责（英文版） |
| `docs/HARDWARE_ZH.md` | 项目设置、说明与完整性 | 已核对板型、GPIO 接线与供电职责（中文版） |
| `docs/INTEGRATION_EN.md` | 项目设置、说明与完整性 | 系统集成结构、约束与预期故障（英文版） |
| `docs/INTEGRATION_ZH.md` | 项目设置、说明与完整性 | 系统集成结构、约束与预期故障（中文版） |
| `docs/RELEASE_NOTEBOOK_EN.md` | 项目设置、说明与完整性 | 组件实现或可复现辅助程序：RELEASE_NOTEBOOK_EN.md |
| `docs/RELEASE_NOTEBOOK_ZH.md` | 项目设置、说明与完整性 | 组件实现或可复现辅助程序：RELEASE_NOTEBOOK_ZH.md |
| `docs/SETUP_WINDOWS_EN.md` | 项目设置、说明与完整性 | Windows 运行环境与当前监控启动步骤（英文版） |
| `docs/SETUP_WINDOWS_ZH.md` | 项目设置、说明与完整性 | Windows 运行环境与当前监控启动步骤（中文版） |
| `docs/SHARING_EN.md` | 项目设置、说明与完整性 | 公开发布选取、隐私与同步核查（英文版） |
| `docs/SHARING_ZH.md` | 项目设置、说明与完整性 | 公开发布选取、隐私与同步核查（中文版） |
| `docs/TEAM_HANDOFF_EN.md` | 项目设置、说明与完整性 | 队友与代理职责、接口及后续优先事项（英文版） |
| `docs/TEAM_HANDOFF_ZH.md` | 项目设置、说明与完整性 | 队友与代理职责、接口及后续优先事项（中文版） |
| `docs/VALIDATION_EN.md` | 项目设置、说明与完整性 | 复现命令、测试结果及未解决验收项（英文版） |
| `docs/VALIDATION_ZH.md` | 项目设置、说明与完整性 | 复现命令、测试结果及未解决验收项（中文版） |
| `esp32-link/README.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界 |
| `esp32-link/README_EN.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界（英文版） |
| `esp32-link/README_ZH.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界（中文版） |
| `esp32-link/gap_receiver/README.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界 |
| `esp32-link/gap_receiver/README_EN.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界（英文版） |
| `esp32-link/gap_receiver/README_ZH.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界（中文版） |
| `esp32-link/gap_receiver/firmware/BUILD.json` | NodeMCU-32S 接收与回执组件 | 冻结源码与产物身份及构建、部署元数据 |
| `esp32-link/gap_receiver/firmware/README_EN.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界（英文版） |
| `esp32-link/gap_receiver/firmware/README_ZH.md` | NodeMCU-32S 接收与回执组件 | 使用设置、文件职责与验证边界（中文版） |
| `esp32-link/gap_receiver/gap_diagnostics.h` | NodeMCU-32S 接收与回执组件 | 独立输出收到的原始字段与控制目标状态 |
| `esp32-link/gap_receiver/gap_protocol.h` | NodeMCU-32S 接收与回执组件 | CRC、会话、序号解析及目标过期状态机 |
| `esp32-link/gap_receiver/gap_receiver.ino` | NodeMCU-32S 接收与回执组件 | NodeMCU-32S UART2 接收与回执程序，不控制电机 |
| `esp32-link/gap_receiver/gap_self_tests.h` | NodeMCU-32S 接收与回执组件 | 启用 UART 前在临时状态上执行接收器自检 |
| `esp32-link/gap_receiver/tests/host_protocol_test.cpp` | NodeMCU-32S 接收与回执组件 | 用本机编译器运行真实 ESP 协议与诊断测试 |
| `legacy/pico+computer combo sensoring version.zip` | 最终组合版归档 | 与最终 Pico + 电脑模板逐文件一致的归档 |
| `legacy/pico+computer combo sensoring version/.gitignore` | 保留的最终 Pico + 电脑模板 | 冻结对照：阻止本地日志、构建、录音与密钥进入 Git |
| `legacy/pico+computer combo sensoring version/AGENTS.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：仓库约束与代理交接入口 |
| `legacy/pico+computer combo sensoring version/AGENTS_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：仓库约束与编码代理交接（英文版） |
| `legacy/pico+computer combo sensoring version/AGENTS_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：仓库约束与编码代理交接（中文版） |
| `legacy/pico+computer combo sensoring version/FILE_CATALOG.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：完整选中文件职责与功能索引 |
| `legacy/pico+computer combo sensoring version/FILE_CATALOG_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：完整选中文件职责与功能索引（英文版） |
| `legacy/pico+computer combo sensoring version/FILE_CATALOG_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：完整选中文件职责与功能索引（中文版） |
| `legacy/pico+computer combo sensoring version/PLATFORM_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：当前组件的具体硬件与构建工具版本（英文版） |
| `legacy/pico+computer combo sensoring version/PLATFORM_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：当前组件的具体硬件与构建工具版本（中文版） |
| `legacy/pico+computer combo sensoring version/README.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/README_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（英文版） |
| `legacy/pico+computer combo sensoring version/README_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（中文版） |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/Build.ps1` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用已配置的本地 SDK 构建安卓应用 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/CMakeLists.txt` | 保留的最终 Pico + 电脑模板 | 冻结对照：Pico SDK 源文件、目标选项与构建规则 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/Load-RAM.ps1` | 保留的最终 Pico + 电脑模板 | 冻结对照：加载保留组合版的临时采集 RAM 镜像 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/Monitor.ps1` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：Monitor.ps1 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/README.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/README_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（英文版） |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/README_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（中文版） |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/app_controls.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：app_controls.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/app_instance.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：app_instance.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/array_geometry.json` | 保留的最终 Pico + 电脑模板 | 冻结对照：麦克风通道位置与阵列角度约定 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/arrival_dsp.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：电脑到达峰一致性与几何拟合参考 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/beacon-audio/coded-gap-v1-right-only.wav` | 保留的最终 Pico + 电脑模板 | 冻结对照：发射与参考波形，必须与接收端模板匹配 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/beacon_dsp.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：电脑参考信标生成、配置与检测 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/beacon_importer.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：beacon_importer.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/bridge_config.json` | 保留的最终 Pico + 电脑模板 | 冻结对照：共享配置、来源或结构化验证记录：bridge_config.json |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/check_protocol.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：check_protocol.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/crc32_fast.h` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：crc32_fast.h |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/direction_diagnostics.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：本地方向失败诊断采集，运行数据不公开分发 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/direction_estimator.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：电脑方向估计与结果协调 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/esp32_bridge.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：保留的电脑结果转发助手，不是 Pico 独立定位 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README.txt` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（英文版） |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/README_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（中文版） |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.elf` | 保留的最终 Pico + 电脑模板 | 冻结对照：用于调试与资源分析的固件可执行及符号产物 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2` | 保留的最终 Pico + 电脑模板 | 冻结对照：编译固件镜像，部署前核对构建身份 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/highband_dsp.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：电脑高频匹配与定位参考 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/joint_delay_dsp.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：电脑联合时差与方向搜索参考 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/link_frame.h` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：link_frame.h |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/main.c` | 保留的最终 Pico + 电脑模板 | 冻结对照：与电脑定位配套的保留 Pico 采集固件 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/make_regular_tones.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：make_regular_tones.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/radar_canvas.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：绘制保留电脑定位器的雷达界面 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/raw_packet.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：解析保留的 Pico 到电脑原始音频包格式 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/refresh_and_start.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：refresh_and_start.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/release_info.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：release_info.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/requirements.txt` | 保留的最终 Pico + 电脑模板 | 冻结对照：当前组件声明的 Python 依赖 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/runtime_tuning.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：runtime_tuning.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_i2s.pio` | 保留的最终 Pico + 电脑模板 | 冻结对照：麦克风同步 I2S 采样的 PIO 程序 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_launcher.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：保留的电脑定位入口，可能加载其采集 RAM 镜像 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_simple_view.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：sen0325_simple_view.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/sen0325_view.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：sen0325_view.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/signal_scope.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：在保留的电脑应用中显示信号与频谱诊断 |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/tone_filter.h` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：tone_filter.h |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/tracking_audio.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：tracking_audio.py |
| `legacy/pico+computer combo sensoring version/SEN0325-Pico-Setup/verify_ram.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：检查保留组合版采集 RAM 镜像身份 |
| `legacy/pico+computer combo sensoring version/SHA256SUMS.txt` | 保留的最终 Pico + 电脑模板 | 冻结对照：除校验文件自身外所有选中文件的 SHA256 |
| `legacy/pico+computer combo sensoring version/SOURCE_MANIFEST.json` | 保留的最终 Pico + 电脑模板 | 冻结对照：冻结模板源码身份与来源 |
| `legacy/pico+computer combo sensoring version/Setup-Windows.ps1` | 保留的最终 Pico + 电脑模板 | 冻结对照：准备可选 Windows 监控依赖 |
| `legacy/pico+computer combo sensoring version/TEMPLATE_VALIDATION.json` | 保留的最终 Pico + 电脑模板 | 冻结对照：冻结模板验证证据与限制 |
| `legacy/pico+computer combo sensoring version/Update.cmd` | 保留的最终 Pico + 电脑模板 | 冻结对照：保留的电脑计算启动或更新入口，可能加载组合版采集 RAM 固件 |
| `legacy/pico+computer combo sensoring version/VALIDATION.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：复现命令、测试结果及未解决验收项 |
| `legacy/pico+computer combo sensoring version/VALIDATION_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：复现命令、测试结果及未解决验收项（英文版） |
| `legacy/pico+computer combo sensoring version/VALIDATION_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：复现命令、测试结果及未解决验收项（中文版） |
| `legacy/pico+computer combo sensoring version/android-player/CHANGELOG.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：版本变更及其范围、状态 |
| `legacy/pico+computer combo sensoring version/android-player/CHANGELOG_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：版本变更及其范围、状态（英文版） |
| `legacy/pico+computer combo sensoring version/android-player/CHANGELOG_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：版本变更及其范围、状态（中文版） |
| `legacy/pico+computer combo sensoring version/android-player/QUICKSTART_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件安装与首次使用简要步骤（英文版） |
| `legacy/pico+computer combo sensoring version/android-player/QUICKSTART_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件安装与首次使用简要步骤（中文版） |
| `legacy/pico+computer combo sensoring version/android-player/README.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/android-player/README_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（英文版） |
| `legacy/pico+computer combo sensoring version/android-player/README_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（中文版） |
| `legacy/pico+computer combo sensoring version/android-player/releases/BeaconLoop-1.2.apk` | 保留的最终 Pico + 电脑模板 | 冻结对照：可安装的安卓本地信标循环播放器 |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.mp3` | 保留的最终 Pico + 电脑模板 | 冻结对照：发射与参考波形，必须与接收端模板匹配 |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav` | 保留的最终 Pico + 电脑模板 | 冻结对照：发射与参考波形，必须与接收端模板匹配 |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README.txt` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（英文版） |
| `legacy/pico+computer combo sensoring version/audio/phone/HF2-gap-test/README_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（中文版） |
| `legacy/pico+computer combo sensoring version/docs/HARDWARE.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：已核对板型、GPIO 接线与供电职责 |
| `legacy/pico+computer combo sensoring version/docs/HARDWARE_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：已核对板型、GPIO 接线与供电职责（英文版） |
| `legacy/pico+computer combo sensoring version/docs/HARDWARE_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：已核对板型、GPIO 接线与供电职责（中文版） |
| `legacy/pico+computer combo sensoring version/docs/SETUP_WINDOWS.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：Windows 运行环境与当前监控启动步骤 |
| `legacy/pico+computer combo sensoring version/docs/SETUP_WINDOWS_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：Windows 运行环境与当前监控启动步骤（英文版） |
| `legacy/pico+computer combo sensoring version/docs/SETUP_WINDOWS_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：Windows 运行环境与当前监控启动步骤（中文版） |
| `legacy/pico+computer combo sensoring version/docs/USER_GUIDE.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：USER_GUIDE.md |
| `legacy/pico+computer combo sensoring version/docs/USER_GUIDE_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：USER_GUIDE_EN.md |
| `legacy/pico+computer combo sensoring version/docs/USER_GUIDE_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：USER_GUIDE_ZH.md |
| `legacy/pico+computer combo sensoring version/tests/README.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界 |
| `legacy/pico+computer combo sensoring version/tests/README_EN.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（英文版） |
| `legacy/pico+computer combo sensoring version/tests/README_ZH.md` | 保留的最终 Pico + 电脑模板 | 冻结对照：使用设置、文件职责与验证边界（中文版） |
| `legacy/pico+computer combo sensoring version/tests/requirements-plots.txt` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件说明、依赖或项目参考：requirements-plots.txt |
| `legacy/pico+computer combo sensoring version/tests/verify_controls.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：verify_controls.py |
| `legacy/pico+computer combo sensoring version/tests/verify_english_ui.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：verify_english_ui.py |
| `legacy/pico+computer combo sensoring version/tests/verify_gap_beacon.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：verify_gap_beacon.py |
| `legacy/pico+computer combo sensoring version/tests/verify_raw_packet.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：verify_raw_packet.py |
| `legacy/pico+computer combo sensoring version/tools/launch.cmd` | 保留的最终 Pico + 电脑模板 | 冻结对照：保留的电脑计算启动或更新入口，可能加载组合版采集 RAM 固件 |
| `legacy/pico+computer combo sensoring version/tools/verify_handoff.py` | 保留的最终 Pico + 电脑模板 | 冻结对照：组件实现或可复现辅助程序：verify_handoff.py |
| `legacy/pico+computer combo sensoring version/一键启动.cmd` | 保留的最终 Pico + 电脑模板 | 冻结对照：保留的电脑计算启动或更新入口，可能加载组合版采集 RAM 固件 |
| `pico-standalone/CMakeLists.txt` | 当前 Pico 独立定位组件 | Pico SDK 源文件、目标选项与构建规则 |
| `pico-standalone/COMMUNICATION_NOTEBOOK_EN.md` | 当前 Pico 独立定位组件 | 通信决策、实验与剩余验收项（英文版） |
| `pico-standalone/COMMUNICATION_NOTEBOOK_ZH.md` | 当前 Pico 独立定位组件 | 通信决策、实验与剩余验收项（中文版） |
| `pico-standalone/DESIGN_NOTEBOOK_EN.md` | 当前 Pico 独立定位组件 | 可核查的算法、资源决策及已暂停计算优化（英文版） |
| `pico-standalone/DESIGN_NOTEBOOK_ZH.md` | 当前 Pico 独立定位组件 | 可核查的算法、资源决策及已暂停计算优化（中文版） |
| `pico-standalone/README.md` | 当前 Pico 独立定位组件 | 使用设置、文件职责与验证边界 |
| `pico-standalone/README_EN.md` | 当前 Pico 独立定位组件 | 使用设置、文件职责与验证边界（英文版） |
| `pico-standalone/README_ZH.md` | 当前 Pico 独立定位组件 | 使用设置、文件职责与验证边界（中文版） |
| `pico-standalone/dsp/README.md` | 当前 Pico 独立定位组件 | 使用设置、文件职责与验证边界 |
| `pico-standalone/dsp/gap_dsp.c` | 当前 Pico 独立定位组件 | 固定 HF2 匹配滤波、峰选择与到达时间一致性拟合 |
| `pico-standalone/dsp/gap_dsp.h` | 当前 Pico 独立定位组件 | DSP 结果、工作区与阶段计时接口 |
| `pico-standalone/dsp/gap_fast_float.h` | 当前 Pico 独立定位组件 | 二进制浮点缩放与舍入，保留库函数回退 |
| `pico-standalone/dsp/gap_integer_fft.h` | 当前 Pico 独立定位组件 | 有界整数 FFT 与可选已验证快速算术 |
| `pico-standalone/dsp/gap_integer_tables.h` | 当前 Pico 独立定位组件 | 整数 FFT 使用的只读 Q15 正弦常量 |
| `pico-standalone/dsp/gap_tables.h` | 当前 Pico 独立定位组件 | 编译进固件的 HF2 模板频谱与 FFT 常量 |
| `pico-standalone/dsp/generate_tables.py` | 当前 Pico 独立定位组件 | 复现固定模板与变换常量 |
| `pico-standalone/firmware/BUILD.json` | 当前 Pico 固件发布 | 冻结源码与产物身份及构建、部署元数据 |
| `pico-standalone/firmware/README_EN.md` | 当前 Pico 固件发布 | 使用设置、文件职责与验证边界（英文版） |
| `pico-standalone/firmware/README_ZH.md` | 当前 Pico 固件发布 | 使用设置、文件职责与验证边界（中文版） |
| `pico-standalone/firmware/pico_gap_standalone-v0.2.elf` | 当前 Pico 固件发布 | 用于调试与资源分析的固件可执行及符号产物 |
| `pico-standalone/firmware/pico_gap_standalone-v0.2.uf2` | 当前 Pico 固件发布 | 编译固件镜像，部署前核对构建身份 |
| `pico-standalone/firmware/resource-audit.json` | 当前 Pico 固件发布 | 链接资源账目，不代表实时空闲内存 |
| `pico-standalone/main.c` | 当前 Pico 独立定位组件 | Pico 采集、调度、定位调用与诊断输出 |
| `pico-standalone/sen0325_i2s.pio` | 当前 Pico 独立定位组件 | 麦克风同步 I2S 采样的 PIO 程序 |
| `pico-standalone/standalone_link.h` | 当前 Pico 独立定位组件 | UART 封装、CRC、回执解析、年龄与确认条件 |
| `pico-standalone/tests/dsp_harness.c` | 独立定位本机验证 | 使用本机 PCM 测例执行纯 C DSP，不访问设备 |
| `pico-standalone/tests/host_link_test.c` | 独立定位本机验证 | CRC、回执、边界与年龄/确认的 41 项本机检查 |
| `pico-standalone/tests/observe_pnr_sensitivity.py` | 独立定位本机验证 | 观察门限敏感性，不改变生产默认值 |
| `pico-standalone/tests/run_offline_validation.py` | 独立定位本机验证 | 使用公开测例对照 C DSP 与保留的电脑算法 |
| `pico-standalone/tests/test_analyze_link_trial.py` | 独立定位本机验证 | 链路配对、会话与缺失证据的回归检查 |
| `pico-standalone/tests/test_main_communication.py` | 独立定位本机验证 | 提取真实 Pico main 函数进行 107 项本机模拟断言 |
| `pico-standalone/tests/test_monitor_startup.py` | 独立定位本机验证 | 检查启动积压、换行对齐和正式记录不被改写 |
| `pico-standalone/tests/test_reference_paths.py` | 独立定位本机验证 | 验证整理后的可移植参考路径发现 |
| `pico-standalone/tools/analyze_link_trial.py` | 可选监控与证据工具 | 关联发送、ESP 字段与回执观察，保留缺项 |
| `pico-standalone/tools/desktop.py` | 可选监控与证据工具 | 可选雷达与耗时监控；方向由 Pico 计算 |
| `pico-standalone/tools/desktop_control.py` | 可选监控与证据工具 | 启动、聚焦、检查并正常重启本地监控 |
| `pico-standalone/tools/monitor.py` | 可选监控与证据工具 | 有限时长串口记录与明确的启动对齐 |
| `references/README.md` | 用户提供的原始参考 | 使用设置、文件职责与验证边界 |
| `references/README.txt` | 用户提供的原始参考 | 使用设置、文件职责与验证边界 |
| `references/README_EN.md` | 用户提供的原始参考 | 使用设置、文件职责与验证边界（英文版） |
| `references/README_ZH.md` | 用户提供的原始参考 | 使用设置、文件职责与验证边界（中文版） |
| `references/Tagalong_Project_Notes.docx` | 用户提供的原始参考 | 用户提供的原始项目或硬件参考，保留原语言 |
| `references/Tagalong_Proposal.pptx` | 用户提供的原始参考 | 用户提供的原始项目或硬件参考，保留原语言 |
| `references/hardware/MSM261S4030H0.pdf` | 用户提供的原始参考 | 用户提供的原始项目或硬件参考，保留原语言 |
| `references/hardware/Pico-backside-user.jpg` | 用户提供的原始参考 | 硬件或项目参考图片 |
| `references/hardware/Pico-installed-user.jpg` | 用户提供的原始参考 | 硬件或项目参考图片 |
| `references/hardware/SEN0325-array-datasheet.pdf` | 用户提供的原始参考 | 用户提供的原始项目或硬件参考，保留原语言 |
| `references/hardware/SEN0325-connector-user.jpg` | 用户提供的原始参考 | 硬件或项目参考图片 |
| `references/hardware/SEN0325-schematic.pdf` | 用户提供的原始参考 | 用户提供的原始项目或硬件参考，保留原语言 |
| `reports/communication-2026-11-12/REPORT_EN.md` | 公开阶段证据与图表 | 含对照与证据限制的阶段实测报告（英文版） |
| `reports/communication-2026-11-12/REPORT_ZH.md` | 公开阶段证据与图表 | 含对照与证据限制的阶段实测报告（中文版） |
| `reports/communication-2026-11-12/build_report.py` | 公开阶段证据与图表 | 从脱敏指标复现公开通信报告图表 |
| `reports/communication-2026-11-12/figures/communication_EN.png` | 公开阶段证据与图表 | 实测报告图表 |
| `reports/communication-2026-11-12/figures/communication_ZH.png` | 公开阶段证据与图表 | 实测报告图表 |
| `reports/communication-2026-11-12/metrics.json` | 公开阶段证据与图表 | 脱敏的机器可读实测结果与限制 |
| `requirements.txt` | 项目设置、说明与完整性 | 当前组件声明的 Python 依赖 |
| `tools/launch.cmd` | 本地维护与验证 | 监控入口共用的运行环境选择 |
| `tools/refresh_catalog.py` | 本地维护与验证 | 生成双语目录清单与选中文件 SHA256 校验 |
| `tools/verify_release.py` | 本地维护与验证 | 只读核查发布文件、哈希、ZIP、链接、隐私与构建身份 |
