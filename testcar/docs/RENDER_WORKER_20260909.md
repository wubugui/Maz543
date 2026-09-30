# 完整显示运行时、直接机械通路与无损 GLB 封装

2026-09-09。完整 goal 保持 **ACTIVE**，全部 16 项整车验收仍 **OPEN**。本阶段针对预览卡顿推进；不是整车性能或机械精度验收。

## 当前启用范围

- 普通入口仍使用主线程显示。完整场景已提取到 `lib/vehicleViewport.ts`，React 只负责生命周期和控件引用。
- **独立显示仍为开发验证入口**：`http://localhost:3000/?render-worker=1`。`?qa-focus=drive&render-worker=1` 用于传动检查；不是简化模型，也不暂停机械求解。
- 主线程和 Worker 调用同一份场景、材质、姿态、选择、剖切及导出实现。未启用先前未通过的合批实验。
- 普通整车入口和 Worker 的当前姿态 GLB 导出都已改用 Blob 封装；其他页面继续保留原 `exportGLB` 接口。
- 退出视口时释放其自有 WebGL 上下文。未修改服务器端口、进程、浏览器/系统设置、驱动或原生模型文件。

## 实现

`viewportEnvironment.ts`、`workerViewportHost.ts`、`viewportProtocol.ts`、`viewport.worker.ts` 和 `renderWorkerClient.ts` 建立 OffscreenCanvas 主机适配。

Worker 保留完整 Three 对象图，界面只接收零件元数据。DOM 桥接限于自有画布、标注、诊断文字和下载链接。真实指针坐标、文档级拖动、滚轮和修饰键送入原 OrbitControls；相机与拾取仍由原实现计算。没有坐标取整、几何重采样或简化副本。尺寸来自真实画布位置和 CSS 大小；RAF 按页面刷新回调请求，使用 Worker 自己的时间原点。原像素比、抗锯齿、阴影、GTAO 和材质设置保留。

界面直接持有独立机械 Worker，控制、复位和显隐暂停直接送达。每个完成的 240 Hz 步仍发布完整状态，经 MessagePort 直达显示 Worker；仪表沿用约 150 ms 的发布间隔，避免等待繁忙绘制。复位代数隔离旧消息。关闭组件立即终止自有机械 Worker，通知显示运行时清理后终止自有显示 Worker；10 秒仅是该线程关闭的兜底期限。

## 已完成的有限验证

证据目录：`outputs/render-worker-evidence/`。

- `source-integrity.json`：16,735 字符的机械姿态/显示变换代码段与提取前逐字相同；8 个机械源文件与上一阶段归档逐字节相同。
- `host-tests.json`：真实 OrbitControls 的旋转、文档拖动释放、右键平移、滚轮缩放；小数坐标、尺寸、显隐、RAF 取消、标签生命周期通过。7 个原生 GLB 哈希与上一阶段一致。
- `direct-mechanics-tests.json`：实际渲染消费者线程阻塞 2 秒期间，车门仍在约 651 ms 内运动到 41.4375°，复位也可完成；完整状态在主通路/显示通路相同，旧代数指令被隔离。这里是 Node Worker 调度试验，不是 GPU 测速。
- `timeline-regression.json`：原 240 Hz 时间线的完整状态一致性、积压保留、隐藏暂停和真实 Worker 主线程阻塞回归通过。
- 浏览器实际显示 8,868 个几何实例；传动启动、整车四门打开、说明窗口、复位、实际拖动和原驾驶室网格拾取已观察。`whole-vehicle-picked-ax.txt` 与截图保留结果。
- `drive-current-pose.glb`：真实浏览器下载的传动检查当前可见姿态，71,503,480 字节，1,754 节点、892 网格、92 个带形变目标网格。完整、未截断 glTF 校验 0 错误/0 警告；未使用 UV 的信息提示保留。

整车绘制仍观察到约 **0.3–0.7 FPS**，部件视图也仍慢。按钮状态/仪表从繁忙绘制中分离，不表示转动相机或拾取反馈已达到流畅要求。截图中的软件渲染质量也不是最终写实效果验收。

## 真实整车导出与内存复制

原导出器的整车尝试并非永久失败：9 项图片已于 17:05:59.837 UTC 完成，整个 GLB 到 17:07:46.729 UTC 才返回。此前尚未完成时的记录必须结合这条后续结果读取。

`binaryGltfBlob.ts` 使用当前 Three r183 的实例级 writer 适配，只替换最终容器封装。仍使用原 scene/accessor/material/image/morph/animation 编码及插件；将已有二进制 Blob 与 GLB 头、UTF-8 JSON、长度及对齐填充直接组成 Blob，省掉两次完整载荷的 FileReader/ArrayBuffer 读回。不改变贴图格式、分辨率、几何、索引、形变和可见性规则。

`blob-encoding-tests.json` 中共享网格/材质、反射缩放、可见性、形变、动画、材质扩展及 UTF-8/对齐用例，与原导出器 **逐字节一致**。真实浏览器纹理用例同样逐字节一致（2,420 字节），见 `blob-export-log.json`。

两次真实整车当前可见姿态导出：

| 项目 | 原封装 | Blob 封装 |
|---|---:|---:|
| GLB 字节 | 349,722,392 | 349,722,388 |
| 节点 | 3,226 | 3,226 |
| 网格 | 1,758 | 1,758 |
| 图片 | 9 | 9 |
| 二进制载荷字节 | 346,418,624 | 346,418,624 |

`whole-export-comparison.json`：**346,418,624 字节载荷完全相同**，SHA-256 均为 `cb5a1ca51d7c539b9443e73e0752f3cfbe7964508165e57add148e71400acb82`。JSON 仅三个根节点矩阵数值不同，两次导出在不同机械时刻：两个旋转分量约 10^-20，一个平移分量约 10^-9 m、差值约 10^-18 m。未通过冻结求解或舍入这些值伪造相同快照。其余 JSON 完全相同。导出依然遵循原有“当前可见姿态”，不包含网页逻辑，也不声称普通外观模式导出了被隐藏的全部内构。

Blob 路径在 17:11:40.917 UTC 报告二进制封装，17:11:40.918 UTC 返回 349,722,388 字节，实际下载文件已复制到 `whole-current-pose.glb`。这些是一次真实工作流的阶段记录，不是控制了缓存、并发负载和内存峰值的性能基准。

**整车导出完整校验未通过**：`whole-current-pose-validation.json` 报告 698 个 `ACCESSOR_VECTOR3_NON_UNIT`，全部指向切线 TANGENT，0 警告；信息提示 1,977 个，报告未截断。例子包括 `BL_Merged_body_OD_green_aged_enamel`、`BL_Merged_body_Rubber_window_seals` 和 `COOL_upper_input_flange_0`。存在长度约 0.000423、0.000345 的切线，也有分量 1.000225 的切线。原 Worker 封装与新 Blob 封装的载荷完全相同，说明这些数据不是 Blob 封装改坏的；但不能因此把整车导出当作正确。原生资产含 Draco 压缩，需继续核查解码切线、退化 UV 和量化；尚未确认根因，未擅自删除切线、改贴图或重导出原生资产。此前部件导出的 0 错误仅适用于那份部件文件。

## 下一步，不能据此停止

1. 先追踪整车导出的 698 个切线错误，区分源网格、Draco 解码和导出规范；保留真实方向、UV 和拓扑，不得删除属性掩盖错误。
2. 完成独立显示默认启用前的跨上下文图像核对、标签、剖切/透视、尺寸变化、生产 Worker 及失败恢复核查。当前开发入口可用不等于默认发布通过。
3. 继续减少实际绘制成本，研究工业 CAD 的可见性、表示共享及深度利用；保持权威几何和机械求解。绘制帧率仍是核心未解决项。
4. 加入更有代表性的交互延迟和内存峰值记录。现有截图/工具调用耗时不能当作严谨的 UI 延迟基准。
5. Blob 适配使用 Three writer 的内部结构，升级 Three 时必须重验接口及字节相等测试。未改第三方包源码。
6. 完整机械 goal 中变矩器流体/闭锁、装配、全内构及参数校准继续 OPEN，参见原有 16 项验收和前阶段文档。

前阶段关于 `chrome://gpu` 被浏览器安全策略拒绝的边界继续有效；不得通过其他接口绕过该诊断限制。本阶段仅进行应用代码和公开 WebGL/浏览器操作验证。

## 参考

- [Three 官方 OffscreenCanvas：共享完整场景代码、转发 DOM 输入和尺寸](https://threejs.org/manual/en/offscreencanvas.html)
- [MDN：transferControlToOffscreen](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/transferControlToOffscreen)
- [OCCT AIS_ConnectedInteractive 表示复用](https://occt3d.com/dev/doc/refman/html/_a_i_s___connected_interactive_8hxx.html)

前阶段：[独立机械调度](SIMULATION_DISPLAY_SCHEDULING_20260909.md)、[CAD 显示优化](PERFORMANCE_CAD_DISPLAY_20260908.md)。

检查收尾：`tsc --noEmit --incremental false` 与生产构建通过，日志位于 `work/render-worker-refactor/worker-types.log`、`worker-build.log`。构建成功不代表生产 Worker 已在浏览器运行验证。完整 GLB 校验脚本因上述 698 个切线错误返回失败，未忽略错误。服务器仍为 `::1:3000`、PID 4156。本阶段代码、报告及实际导出文件通过 `scripts/archive-render-worker-stage.py` 保存到 `E:\Maz543\restoration\render-worker-and-blob-20260909`，使用逐文件 SHA-256 验证；旧阶段归档保持不变。

归档后补充观察：从整车点击“变速机构”的 Playwright 操作出现一次 3 秒超时；重新读取页面后，通过当前可访问元素操作成功进入传动/纵剖，见 `post-archive-drive-switch-ax.txt`。因此不能声称独立显示消除了全部操作迟滞；未因观察超时重启服务。该补充留在活动工作区，未改写已封存的 69 文件/423,566,206 字节归档。
