# 验证说明
## 证据分层
- 文件／构建检查只能证明格式、可复现性或二进制身份。
- 本机原生测试使用模拟时间／硬件，验证真实协议与状态逻辑。
- 双串口实测证明记录范围内字段传输和 ACK 行为。
- 物理准确性需要已知角度测试；安全跟随还需要电机实测。

见[当前报告](../reports/communication-2026-11-12/REPORT_ZH.md)。33/33 个角度字段一致，说明传输保留了估计值，不代表声源真在该角度。计时代码段占周期的比例只是算力代理指标，不是完整 profiler 利用率；链接器剩余空间不是运行时高水位。

## 复现公开检查
需要项目依赖、Python3.12 以上和本机 C/C++ 编译器，不能拿嵌入式 ARM 编译器代替。本机验证使用过 Cygwin GCC4.8.3。替换工具路径，结果放项目外可写目录。
```powershell
python -m unittest discover -s pico-standalone/tests -p "test_*.py"
python pico-standalone/tests/run_offline_validation.py --help
python pico-standalone/tests/run_offline_validation.py --skip-real --gcc C:\Path\To\gcc.exe --output C:\BenchResults\public-dsp
g++ -std=c++11 -Iesp32-link/gap_receiver esp32-link/gap_receiver/tests/host_protocol_test.cpp -o C:\BenchResults\esp-tests.exe
C:\BenchResults\esp-tests.exe
python tools/verify_release.py
```
Pico 的 main／link 原生检查见该目录 README。公开 DSP 测试默认读取最终组合模板中的参考算法；私人录音必须显式传入，仓库不包含。

**已知未通过的 DSP 验收：**公开 float 参考测试处理 187 窗，29 项中 27 项通过，两个错码负例检查失败：常规负例 37 窗中 1 窗误接受，重复错码 3 窗全部误接受。C 与电脑 arrival 路径有效性一致，但共同存在的误触发未解决，不能写成生产验收通过。FAST 数值等价验证是另一组证据。

## 下一阶段硬件测试
记录手机真实角度、距离、音量，固定位置后播放配套 HF2，并标出有意停播区间。有限时间采集后比较源数据时间、拟合、确认、新鲜度、发送字段、ESP 有效目标与 ACK。再换几个已知角度／距离重复。原始麦克风数据只留本地。

启动预热与正式记录区间分开；保留原始预热数据和解析错误，不悄悄过滤坏行。记录首尾未匹配不一定是丢包；内部没观察到缺项，也不代表线路永远不会丢数据。

物理断电重启、当前 Flash 的正向手机复测、控制任务最坏调度、堆栈高水位、真实声音到箭头延迟，以及安卓后台全面验收仍未完成。
