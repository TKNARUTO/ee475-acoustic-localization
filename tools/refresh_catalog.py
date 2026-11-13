"""Refresh the shareable local catalog and checksums; never package or publish.

Run after source/docs are stable. --check-only computes a preview without writing
anything. The current documentation baseline is 12 November 2026. Private logs,
recordings, machine configuration, keys, backups and generated builds are omitted.
The frozen combo ZIP is an exact exception, not a wildcard archive allowance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE_DATE = date(2026, 11, 12)
CATALOG_CSV = "docs/FILE_CATALOG.csv"
CATALOG_MD = "docs/FILE_CATALOG.md"
CATALOG_EN = "docs/FILE_CATALOG_EN.md"
CATALOG_ZH = "docs/FILE_CATALOG_ZH.md"
SUMS = "SHA256SUMS.txt"
GENERATED = {CATALOG_CSV, CATALOG_MD, CATALOG_EN, CATALOG_ZH, SUMS}
FROZEN_DIR = "legacy/pico+computer combo sensoring version"
FROZEN_ZIP = FROZEN_DIR + ".zip"
PUBLIC_TOP_DIRS = {"android-player", "audio", "docs", "esp32-link", "legacy", "pico-standalone", "references", "reports", "tools"}

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".vscode", ".idea", ".gradle",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "cmakefiles",
    "build", "builds", "native-build", "out", "output", "outputs", "dist",
    "delivery", "logs", "log", "runtime", "runtime-logs", "captures", "capture",
    "recordings", "recording", "raw-recordings", "raw-audio", "trials", "evidence",
    "beacon_profiles", "backup", "backups", ".backups", "keys", "signing-keys",
    "private", "secrets", "test-output", "test-outputs", "test-results", "test-generated",
    "credentials", "device-backups", "device-backup", "devicebackup", "flash-backups",
    "tmp", "temp", ".cache", "toolchains", "local-toolchain", "local-config",
}
SKIP_NAMES = {
    "toolchain.json", "local.properties", "file_index.txt", "00_全部文件索引.txt",
    "local_file_index.csv", "local_file_index.json", "local_archive.json",
    "legacy_migration.csv", "legacy_migration.json", "migration-in-progress.json",
    "desktop-instance.json", "desktop-restart.json", "desktop-request.json",
    "update-status.json", "update-error.txt", "cmakecache.txt", "compile_commands.json",
    "cmake_install.cmake", "build.ninja", ".ninja_log", ".ninja_deps",
    "local_config.json", "local-config.json", "runtime_config.json", "runtime-config.json",
    "machine-config.json", "machine_config.json", "user-config.json", "user_config.json",
    "credentials.json", "service-account.json", "secrets.json", "token.json",
}
SKIP_SUFFIXES = {
    ".jks", ".keystore", ".pem", ".key", ".p12", ".pfx", ".npz", ".npy",
    ".pcm", ".raw", ".cf32", ".f32", ".s16", ".s16le", ".f32le", ".i16",
    ".pyc", ".pyo", ".lnk", ".log", ".jsonl", ".o", ".obj", ".a", ".lib",
    ".dll", ".exe", ".pdb", ".map", ".bak", ".old", ".orig", ".tmp", ".temp",
    ".swp", ".swo", ".lock", ".lck", ".new", ".save", ".7z", ".rar", ".tar", ".gz",
}
AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
SOURCE_SUFFIXES = {".c", ".h", ".cpp", ".hpp", ".py", ".ps1", ".cmd", ".sh", ".pio", ".cmake", ".md", ".java", ".xml", ".gradle"}


def directory_reason(name):
    low = name.casefold()
    if low in SKIP_DIRS:
        return "runtime/build/private directory"
    if low.startswith(("build-", "build_", "cmake-build-", ".venv-", "backup-", "backup_")) or "备份" in low:
        return "build/backup directory"
    return None


def exclude_reason(relative):
    """Pure path policy, shared by traversal and temporary-tree tests."""
    path = PurePosixPath(str(relative).replace("\\", "/"))
    parts = path.parts
    if not parts or path.is_absolute() or ".." in parts:
        return "unsafe relative path"
    if any("\n" in part or "\r" in part for part in parts):
        return "unsupported manifest filename"
    if len(parts) > 1 and parts[0] not in PUBLIC_TOP_DIRS:
        return "directory outside current public tree"
    if parts[0] == "legacy" and path.as_posix() != FROZEN_ZIP and not path.as_posix().startswith(FROZEN_DIR + "/"):
        return "legacy other than the final combo template"
    if len(parts) == 1 and path.name == "一键启动.cmd":
        return "retired root launcher; use Start.cmd"
    for part in parts[:-1]:
        reason = directory_reason(part)
        if reason:
            return reason
    low = path.name.casefold(); suffix = path.suffix.casefold()
    if low in SKIP_NAMES or low.startswith((".env", ".refresh-catalog-", "id_rsa", "id_ed25519")):
        return "local configuration/key/temporary file"
    if low.endswith((".apk.idsig", "~")) or suffix in SKIP_SUFFIXES:
        return "private recording/key/build/temporary artifact"
    if any(fnmatch.fnmatch(low, pattern) for pattern in ("*.local.*", "local-*.json", "local_*.json", "*.backup.*", "*-backup.*", "backup-*", "backup_*")) and suffix not in SOURCE_SUFFIXES:
        return "local configuration/backup artifact"
    if suffix not in SOURCE_SUFFIXES and ("备份" in low or re.search(r"(^|[-_.])(backup|dump)([-_.]|$)", low)):
        return "backup or device dump"
    if suffix == ".zip" and path.as_posix() != FROZEN_ZIP:
        return "archive excluded; only exact frozen combo ZIP is selected"
    lowered = tuple(part.casefold() for part in parts)
    if suffix in AUDIO_SUFFIXES:
        reference_location = "audio" in lowered or "beacon-audio" in lowered or "assets" in lowered
        recording_name = bool(re.search(r"(^|[-_])(raw|capture|recording|recorded|trial|microphone|mic)([-_.]|$)", low))
        if not reference_location or recording_name:
            return "audio outside designated transmitter/reference location"
    if suffix in {".bin", ".elf", ".uf2", ".hex", ".apk"} and not any(part in {"firmware", "releases", "release"} for part in lowered):
        return "generated binary outside designated firmware/release location"
    # New offline experiments must not silently add generated data/results to a handoff.
    if len(parts) >= 3 and parts[0] == "pico-standalone" and parts[1] in {"tests", "experiments"}:
        if suffix not in SOURCE_SUFFIXES and path.name not in {"CMakeLists.txt", "README.txt", "requirements.txt"}:
            return "generated standalone test/experiment artifact"
    return None


def linked(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def selected_files(root):
    selected = set(); skipped = Counter()
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        folder = Path(current)
        keep = []
        for name in sorted(directories):
            reason = directory_reason(name)
            if folder == root and name not in PUBLIC_TOP_DIRS:
                reason = reason or "directory outside current public tree"
            if folder == root / "legacy" and name != PurePosixPath(FROZEN_DIR).name:
                reason = "legacy other than the final combo template"
            if linked(folder / name):
                reason = "symlink/junction"
            if reason:
                skipped[reason] += 1
            else:
                keep.append(name)
        directories[:] = keep
        for name in files:
            path = folder / name
            relative = path.relative_to(root).as_posix()
            reason = "symlink/junction" if linked(path) else exclude_reason(relative)
            if reason:
                skipped[reason] += 1
            elif path.is_file():
                selected.add(relative)
    selected.update(GENERATED)
    return sorted(selected), dict(sorted(skipped.items()))


# Values are authored in both languages; stale prior catalogs never supply roles.
NAME_PURPOSE = {
    ".gitattributes": ("Git text/binary and line-ending rules", "Git 文本、二进制与换行规则"),
    ".gitignore": ("Keep local logs, builds, recordings and keys out of Git", "阻止本地日志、构建、录音与密钥进入 Git"),
    "AGENTS.md": ("Entry for repository constraints and agent handoff", "仓库约束与代理交接入口"),
    "CMakeLists.txt": ("Pico SDK source selection, target options and build rules", "Pico SDK 源文件、目标选项与构建规则"),
    "main.c": ("Pico capture, scheduling, DSP invocation and telemetry", "Pico 采集、调度、定位调用与诊断输出"),
    "standalone_link.h": ("UART framing, CRC, ACK parsing, age and confirmation helpers", "UART 封装、CRC、回执解析、年龄与确认条件"),
    "sen0325_i2s.pio": ("PIO program for synchronous microphone I2S sampling", "麦克风同步 I2S 采样的 PIO 程序"),
    "gap_dsp.c": ("Fixed HF2 matched filter, peak selection and arrival-consensus fit", "固定 HF2 匹配滤波、峰选择与到达时间一致性拟合"),
    "gap_dsp.h": ("DSP result, workspace and phase-profiling interfaces", "DSP 结果、工作区与阶段计时接口"),
    "gap_integer_fft.h": ("Bounded integer FFT and optional verified fast arithmetic", "有界整数 FFT 与可选已验证快速算术"),
    "gap_fast_float.h": ("Binary32 scaling/rounding with library fallback", "二进制浮点缩放与舍入，保留库函数回退"),
    "gap_integer_tables.h": ("Read-only Q15 sine constants for the integer FFT", "整数 FFT 使用的只读 Q15 正弦常量"),
    "gap_tables.h": ("Compiled HF2 template spectrum and FFT constants", "编译进固件的 HF2 模板频谱与 FFT 常量"),
    "generate_tables.py": ("Reproduce fixed template and transform constants", "复现固定模板与变换常量"),
    "desktop.py": ("Optional radar/timing telemetry viewer; Pico computes direction", "可选雷达与耗时监控；方向由 Pico 计算"),
    "desktop_control.py": ("Start, focus, validate and gracefully restart the local viewer", "启动、聚焦、检查并正常重启本地监控"),
    "monitor.py": ("Finite serial recording with explicit startup alignment", "有限时长串口记录与明确的启动对齐"),
    "analyze_link_trial.py": ("Pair TX, ESP fields and ACK observations without hiding gaps", "关联发送、ESP 字段与回执观察，保留缺项"),
    "test_analyze_link_trial.py": ("Regression cases for link pairing, sessions and missing evidence", "链路配对、会话与缺失证据的回归检查"),
    "test_monitor_startup.py": ("Check startup backlog/LF alignment and unmodified formal records", "检查启动积压、换行对齐和正式记录不被改写"),
    "test_reference_paths.py": ("Verify portable reference discovery after repository cleanup", "验证整理后的可移植参考路径发现"),
    "test_main_communication.py": ("Extract real Pico main functions for 107 mocked host assertions", "提取真实 Pico main 函数进行 107 项本机模拟断言"),
    "host_link_test.c": ("41 host checks of CRC, ACK parsing, bounds and age/confirmation", "CRC、回执、边界与年龄/确认的 41 项本机检查"),
    "dsp_harness.c": ("Run portable C DSP on host PCM fixtures; no device access", "使用本机 PCM 测例执行纯 C DSP，不访问设备"),
    "run_offline_validation.py": ("Compare C DSP with the retained PC reference on public fixtures", "使用公开测例对照 C DSP 与保留的电脑算法"),
    "observe_pnr_sensitivity.py": ("Observe threshold sensitivity without changing production defaults", "观察门限敏感性，不改变生产默认值"),
    "gap_receiver.ino": ("NodeMCU-32S UART2 receive/ACK application; no motor commands", "NodeMCU-32S UART2 接收与回执程序，不控制电机"),
    "gap_protocol.h": ("CRC/session/sequence parsing and target expiry state machine", "CRC、会话、序号解析及目标过期状态机"),
    "gap_diagnostics.h": ("Print received raw fields independently of control-target state", "独立输出收到的原始字段与控制目标状态"),
    "gap_self_tests.h": ("Receiver startup tests on temporary state before enabling UART", "启用 UART 前在临时状态上执行接收器自检"),
    "host_protocol_test.cpp": ("Run real ESP protocol/diagnostic tests with a host compiler", "用本机编译器运行真实 ESP 协议与诊断测试"),
    "MainActivity.java": ("Android audio selection and simple playback controls", "安卓音频选择与简单播放操作"),
    "LoopService.java": ("Local foreground audio looping service", "手机本地前台循环播放服务"),
    "AudioLoader.java": ("Decode selected audio into playback PCM", "将选中的音频解码为播放用 PCM"),
    "PcmGain.java": ("Bounded optional PCM gain without silently changing frequency", "受限的可选 PCM 增益，不静默改变频率"),
    "PcmGainTest.java": ("Unit checks of PCM gain, bounds and clipping behavior", "PCM 增益、幅度边界与削顶行为检查"),
    "AndroidManifest.xml": ("Android app identity, permissions and service declarations", "安卓应用身份、权限与服务声明"),
    "Build.ps1": ("Build the Android application with configured local SDK tools", "使用已配置的本地 SDK 构建安卓应用"),
    "Build.cmd": ("Windows entry for the Android build script", "安卓构建脚本的 Windows 入口"),
    "merge_apk.py": ("Assemble Android APK components during the local build", "本地构建时组合安卓 APK 组件"),
    "toolchain.example.json": ("Portable example of local toolchain settings; no real credentials", "本地工具链设置示例，不含真实凭据"),
    "sdk-downloads.json": ("Declared SDK dependency sources for reproducible setup", "可复现安装所需的 SDK 依赖来源声明"),
    "Start.cmd": ("Open/focus the current standalone monitor; never flash firmware", "打开或聚焦当前独立监控，不烧录固件"),
    "Update.cmd": ("Validate and restart local viewer; no Git download or firmware write", "检查并重启本地监控，不下载 Git 更新或烧录"),
    "launch.cmd": ("Shared runtime selection for the monitor entry scripts", "监控入口共用的运行环境选择"),
    "Setup-Windows.ps1": ("Prepare the optional Windows viewer dependencies", "准备可选 Windows 监控依赖"),
    "requirements.txt": ("Declared Python dependencies for this component", "当前组件声明的 Python 依赖"),
    "refresh_catalog.py": ("Generate bilingual catalogs and selected-file SHA256 checksums", "生成双语目录清单与选中文件 SHA256 校验"),
    "verify_release.py": ("Read-only release, hash, ZIP, link, privacy and build-identity audit", "只读核查发布文件、哈希、ZIP、链接、隐私与构建身份"),
    "build_report.py": ("Reproduce public communication report figures from sanitized metrics", "从脱敏指标复现公开通信报告图表"),
    "BUILD.json": ("Frozen source/artifact identity and build/deployment metadata", "冻结源码与产物身份及构建、部署元数据"),
    "resource-audit.json": ("Linker resource accounting; not measured runtime free memory", "链接资源账目，不代表实时空闲内存"),
    "metrics.json": ("Sanitized machine-readable measured results and limitations", "脱敏的机器可读实测结果与限制"),
    "validation.json": ("Recorded component verification results and boundaries", "组件验证结果与适用边界"),
    "SOURCE_MANIFEST.json": ("Frozen template source identities and provenance", "冻结模板源码身份与来源"),
    "TEMPLATE_VALIDATION.json": ("Frozen-template validation evidence and limits", "冻结模板验证证据与限制"),
    "sen0325_launcher.py": ("Retained PC estimator launcher; may load its capture RAM image", "保留的电脑定位入口，可能加载其采集 RAM 镜像"),
    "main.c@combo": ("Retained Pico capture firmware used with PC-side localization", "与电脑定位配套的保留 Pico 采集固件"),
    "beacon_dsp.py": ("PC reference beacon generation, profiles and detection", "电脑参考信标生成、配置与检测"),
    "highband_dsp.py": ("PC high-band matching and localization reference", "电脑高频匹配与定位参考"),
    "arrival_dsp.py": ("PC arrival-peak consensus and geometric fitting reference", "电脑到达峰一致性与几何拟合参考"),
    "joint_delay_dsp.py": ("PC joint-delay/direction search reference", "电脑联合时差与方向搜索参考"),
    "direction_estimator.py": ("PC direction estimation and result coordination", "电脑方向估计与结果协调"),
    "direction_diagnostics.py": ("Local capture of direction-failure diagnostics; data not shipped", "本地方向失败诊断采集，运行数据不公开分发"),
    "raw_packet.py": ("Parse the preserved Pico-to-PC raw audio packet format", "解析保留的 Pico 到电脑原始音频包格式"),
    "radar_canvas.py": ("Draw the retained PC estimator radar display", "绘制保留电脑定位器的雷达界面"),
    "signal_scope.py": ("Show signal/spectrum diagnostics in the retained PC application", "在保留的电脑应用中显示信号与频谱诊断"),
    "esp32_bridge.py": ("Retained PC-result bridge helper, not standalone Pico estimation", "保留的电脑结果转发助手，不是 Pico 独立定位"),
    "Load-RAM.ps1": ("Load only the retained combo's temporary capture RAM image", "加载保留组合版的临时采集 RAM 镜像"),
    "verify_ram.py": ("Check the retained combo capture RAM image identity", "检查保留组合版采集 RAM 镜像身份"),
    "array_geometry.json": ("Microphone channel positions and array angle convention", "麦克风通道位置与阵列角度约定"),
}
DOC_PURPOSE = {
    "README": ("Setup, file roles and validation limits", "使用设置、文件职责与验证边界"),
    "DESIGN_NOTEBOOK": ("Reviewable algorithm/resource decisions and paused compute work", "可核查的算法、资源决策及已暂停计算优化"),
    "COMMUNICATION_NOTEBOOK": ("Communication decisions, trials and remaining acceptance checks", "通信决策、实验与剩余验收项"),
    "REPORT": ("Measured stage report with comparisons and evidence limitations", "含对照与证据限制的阶段实测报告"),
    "FILE_CATALOG": ("Complete selected-file role and function index", "完整选中文件职责与功能索引"),
    "TEAM_HANDOFF": ("Teammate/agent ownership, interfaces and next-stage priorities", "队友与代理职责、接口及后续优先事项"),
    "INTEGRATION": ("System integration architecture, constraints and predicted faults", "系统集成结构、约束与预期故障"),
    "HARDWARE": ("Verified board identification, GPIO wiring and power roles", "已核对板型、GPIO 接线与供电职责"),
    "PLATFORM": ("Specific hardware and build-tool versions for this component", "当前组件的具体硬件与构建工具版本"),
    "VALIDATION": ("Reproduction commands, test outcomes and unresolved checks", "复现命令、测试结果及未解决验收项"),
    "SETUP_WINDOWS": ("Windows runtime setup and current monitor launch procedure", "Windows 运行环境与当前监控启动步骤"),
    "SHARING": ("Public release selection, privacy and synchronization checks", "公开发布选取、隐私与同步核查"),
    "CHANGELOG": ("Version changes with their scope and status", "版本变更及其范围、状态"),
    "QUICKSTART": ("Short component installation and first-use instructions", "组件安装与首次使用简要步骤"),
    "AGENTS": ("Repository constraints and coding-agent handoff", "仓库约束与编码代理交接"),
}


def purpose_pair(relative):
    path = PurePosixPath(relative); name = path.name; suffix = path.suffix.casefold()
    if relative.startswith(FROZEN_DIR + "/") and relative[len(FROZEN_DIR) + 1:] in {"一键启动.cmd", "Update.cmd", "tools/launch.cmd"}:
        return ("Retained PC-computation launcher/update; may load combo capture RAM firmware", "保留的电脑计算启动或更新入口，可能加载组合版采集 RAM 固件")
    if relative == FROZEN_ZIP:
        return ("Exact byte-matching archive of the final Pico + PC template", "与最终 Pico + 电脑模板逐文件一致的归档")
    if name == SUMS:
        return ("SHA256 of all selected files except this checksum file itself", "除校验文件自身外所有选中文件的 SHA256")
    if name in NAME_PURPOSE:
        key = "main.c@combo" if name == "main.c" and relative.startswith(FROZEN_DIR + "/") else name
        return NAME_PURPOSE[key]
    stem = re.sub(r"_(EN|ZH)$", "", path.stem)
    if stem in DOC_PURPOSE:
        detail = DOC_PURPOSE[stem]
        if name.endswith("_ZH.md"):
            return detail[0] + " (Chinese)", detail[1] + "（中文版）"
        if name.endswith("_EN.md"):
            return detail[0] + " (English)", detail[1] + "（英文版）"
        return detail
    if suffix in AUDIO_SUFFIXES:
        return ("Transmitter/reference waveform; keep it matched to the receiver template", "发射与参考波形，必须与接收端模板匹配")
    if suffix in {".uf2", ".bin", ".hex"}:
        return ("Compiled firmware image; consult build identity before deployment", "编译固件镜像，部署前核对构建身份")
    if suffix == ".elf":
        return ("Firmware executable/symbol artifact for debugging and resource analysis", "用于调试与资源分析的固件可执行及符号产物")
    if suffix == ".apk":
        return ("Installable Android local beacon-loop player", "可安装的安卓本地信标循环播放器")
    if suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        return (("Measured report figure" if relative.startswith("reports/") else "Hardware/reference image"), ("实测报告图表" if relative.startswith("reports/") else "硬件或项目参考图片"))
    if suffix in {".pdf", ".docx", ".pptx"}:
        return ("Supplied original project/hardware reference; preserved in its original language", "用户提供的原始项目或硬件参考，保留原语言")
    if suffix in {".json", ".csv", ".yaml", ".yml", ".sha256"}:
        return ("Shared configuration, provenance or structured verification: " + name, "共享配置、来源或结构化验证记录：" + name)
    if suffix in SOURCE_SUFFIXES:
        return ("Component implementation or reproducible support utility: " + name, "组件实现或可复现辅助程序：" + name)
    return ("Component documentation, dependency or project reference: " + name, "组件说明、依赖或项目参考：" + name)


def describe(relative, previous=None, language="en"):
    """Do not reuse stale purposes from an older catalog or active-app layout."""
    index = 1 if language == "zh" else 0
    detail = purpose_pair(relative)[index]
    if relative == FROZEN_ZIP:
        role = ("Final combo archive", "最终组合版归档")
    elif relative.startswith(FROZEN_DIR + "/"):
        role = ("Retained final Pico + PC template", "保留的最终 Pico + 电脑模板")
        detail = ("Frozen comparison: " if index == 0 else "冻结对照：") + detail
    elif relative.startswith("pico-standalone/firmware/"):
        role = ("Current Pico firmware release", "当前 Pico 固件发布")
    elif relative.startswith("pico-standalone/tests/"):
        role = ("Standalone host validation", "独立定位本机验证")
    elif relative.startswith("pico-standalone/tools/"):
        role = ("Optional viewer and evidence tools", "可选监控与证据工具")
    elif relative.startswith("pico-standalone/"):
        role = ("Current independent Pico component", "当前 Pico 独立定位组件")
    elif relative.startswith("esp32-link/"):
        role = ("NodeMCU-32S receive/ACK component", "NodeMCU-32S 接收与回执组件")
    elif relative.startswith("audio/"):
        role = ("Fixed HF2 transmitter/reference", "固定 HF2 发射与参考音频")
    elif relative.startswith("android-player/"):
        role = ("Android local looping transmitter", "安卓本地循环播放端")
    elif relative.startswith("reports/"):
        role = ("Public stage evidence and figures", "公开阶段证据与图表")
    elif relative.startswith("references/"):
        role = ("Supplied original reference", "用户提供的原始参考")
    elif relative.startswith("tools/"):
        role = ("Local maintenance and verification", "本地维护与验证")
    else:
        role = ("Project setup, documentation and integrity", "项目设置、说明与完整性")
    return role[index], detail


def stable_hash(path):
    before = path.stat(); digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    stamp = (before.st_size, before.st_mtime_ns)
    if stamp != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("A selected file changed while hashing; rerun after edits/builds finish")
    return digest.hexdigest(), stamp


def prepare(root=ROOT, baseline_date=BASELINE_DATE):
    root = Path(root).resolve()
    files, skipped = selected_files(root)
    rows = []
    for relative in files:
        role, purpose = describe(relative)
        role_zh, purpose_zh = describe(relative, language="zh")
        rows.append(dict(path=relative, role=role, purpose=purpose, role_zh=role_zh, purpose_zh=purpose_zh))
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=("path", "role", "purpose", "role_zh", "purpose_zh"), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    escape = lambda value: str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|").replace("`", "&#96;")
    content = {CATALOG_CSV: csv_buffer.getvalue().encode("utf-8")}
    content[CATALOG_MD] = ("# File catalog\n\n[English file roles and functions](FILE_CATALOG_EN.md) · [中文文件职责与功能](FILE_CATALOG_ZH.md)\n\nThe single [CSV](FILE_CATALOG.csv) contains both languages. SHA256SUMS.txt covers the selected release files except itself. This local catalog does not claim publication or hardware acceptance.\n").encode("utf-8")
    for language, target in (("en", CATALOG_EN), ("zh", CATALOG_ZH)):
        if language == "en":
            lines = ["# Public project file catalog", "", f"Documentation baseline: {baseline_date.isoformat()}. {len(rows)} selected files. This is the local release selection, not a claim of a GitHub push or hardware acceptance.", "",
                "Current roles: Pico computes bearing; ESP32 NodeMCU-32S receives/acknowledges; Android plays the beacon; the PC viewer is optional. Root Start.cmd and Update.cmd never flash firmware. Only the final Pico + PC comparison template and its exact ZIP remain under legacy.", "",
                "Logs, raw recordings, keys, device backups, machine settings and build/cache outputs are excluded. Public test source and designated firmware releases remain selected. Supplied reference PDF/DOCX/PPTX retain their original language. SHA256SUMS.txt covers every selected file except itself.", "",
                "[中文](FILE_CATALOG_ZH.md) · [Machine-readable CSV](FILE_CATALOG.csv)", "", "| File | Role | Function |", "|---|---|---|"]
            keys = ("role", "purpose")
        else:
            lines = ["# 公开项目文件清单", "", f"说明基准日期：{baseline_date.isoformat()}。共 {len(rows)} 个选中文件。这是本地发布选取，不代表已经推送 GitHub 或通过硬件验收。", "",
                "当前分工：Pico 计算方向，NodeMCU-32S 接收并回执，安卓播放信标，电脑监控可选。根目录 Start.cmd 和 Update.cmd 不烧录固件。legacy 仅保留最终 Pico + 电脑对照模板及其精确匹配 ZIP。", "",
                "运行日志、原始录音、密钥、设备备份、本机设置和构建缓存不选入。公开测试源码与指定固件发布保留。用户提供的 PDF、DOCX、PPTX 参考保留原语言。SHA256SUMS.txt 覆盖除自身以外的每个选中文件。", "",
                "[English](FILE_CATALOG_EN.md) · [机器可读 CSV](FILE_CATALOG.csv)", "", "| 文件 | 职责 | 功能 |", "|---|---|---|"]
            keys = ("role_zh", "purpose_zh")
        lines.extend(f"| `{escape(row['path'])}` | {escape(row[keys[0]])} | {escape(row[keys[1]])} |" for row in rows)
        content[target] = ("\n".join(lines) + "\n").encode("utf-8")
    hashes = {}; stamps = {}
    for relative in files:
        if relative == SUMS:
            continue
        if relative in content:
            hashes[relative] = hashlib.sha256(content[relative]).hexdigest()
        else:
            hashes[relative], stamps[relative] = stable_hash(root / relative)
    content[SUMS] = ("\n".join(f"{hashes[relative]}  {relative}" for relative in files if relative != SUMS) + "\n").encode("utf-8")
    for relative, stamp in stamps.items():
        current = (root / relative).stat()
        if (current.st_size, current.st_mtime_ns) != stamp:
            raise RuntimeError("Selected sources changed during preparation; retry after edits finish")
    return {"root": root, "files": files, "rows": rows, "content": content, "hashes": hashes,
            "skipped": skipped, "baseline_date": baseline_date.isoformat()}


def refresh(root=ROOT, check_only=False, baseline_date=BASELINE_DATE):
    plan = prepare(root, baseline_date); root = plan["root"]
    changed = [relative for relative, data in plan["content"].items()
               if not (root / relative).exists() or (root / relative).read_bytes() != data]
    if not check_only:
        temporary = []
        try:
            for relative in (CATALOG_CSV, CATALOG_MD, CATALOG_EN, CATALOG_ZH, SUMS):
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                fd, filename = tempfile.mkstemp(prefix=".refresh-catalog-", suffix=".tmp", dir=target.parent)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(plan["content"][relative])
                temporary.append((Path(filename), target))
            for source, target in temporary:
                os.replace(source, target)
        finally:
            for source, _ in temporary:
                source.unlink(missing_ok=True)
        for relative, expected in plan["hashes"].items():
            actual, _ = stable_hash(root / relative)
            if actual != expected:
                raise RuntimeError("A selected file changed during refresh; catalogs need another refresh")
    return {"passed": True, "check_only": check_only, "written": not check_only,
            "baseline_date": plan["baseline_date"], "catalog_files": len(plan["files"]),
            "hash_entries": len(plan["hashes"]), "would_update": changed,
            "excluded_counts": plan["skipped"], "firmware_write": False,
            "publishes_or_packages": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="prepare and validate a preview without changing any file")
    parser.add_argument("--date", type=date.fromisoformat, default=BASELINE_DATE, help="documentation baseline YYYY-MM-DD (default 2026-11-12)")
    args = parser.parse_args()
    print(json.dumps(refresh(check_only=args.check_only, baseline_date=args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
