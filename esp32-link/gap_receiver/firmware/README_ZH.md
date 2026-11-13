# NodeMCU-32S 部署证据

这个公共目录只提供 [BUILD.json](BUILD.json)和说明。**已测试二进制不随项目分发**：其中嵌有本机编译路径，因此保留在维护者的私有归档。公开源码、准确构建配置、源码哈希和已测试部署哈希仍然可用。本次打包调整没有替换板上固件，也没有制作未经测试的替代二进制。

记录中的部署文件是**构建生成的 4 MiB 合并镜像**，写入地址为 **0x0**，不是读取用户原板得到的备份。SHA256 仍为 **36610897ee2f78f5fe8153d043df68cbb00b5a7cf040c7d3475dc2b3d77cda6b**。`deployment_image_name` 只是该本机文件的身份记录；`image_distributed=false` 表示它不是下载路径。

构建使用 Arduino CLI1.4.1、esp32 by Espressif Systems3.3.12，板型 NodeMCU-32S，FQBN esp32:esp32:nodemcu-32s。实际编译名称是 sketch_nov12a.ino，其源码和三个头文件与本目录标准 sketch 逐字相同。文件夹／sketch 名称可能改变构建元数据，所以重新编译不保证二进制哈希完全一样。BUILD.json 保存源码哈希和链接统计。

请按 [Arduino 说明](../README_ZH.md)从源码编译上传，并先保留板上原应用。端口需实际枚举，COM6 只是本机值；本板是经典 NodeMCU-32S，不是 ESP32-S3。重新编译的文件不能自动继承原部署的硬件验证结论，应记录新哈希并自行测试。

已写入核验并用于 Flash 测试03–05。它只在 GPIO16／17 接收和返回 ACK，并输出诊断；没有电机指令，当前过期／无效诊断角度不能作为新鲜运动目标。
