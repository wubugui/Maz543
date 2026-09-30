# 原始绘制遮挡与玻璃透射成本

2026-09-09。完整 goal **ACTIVE**，16 项 **OPEN**。本阶段增加有限开发诊断，取得实际分通道数据并排除一条不适用的多重采样复制方案。没有启用遮挡剔除、删除部件、减少面数、降低抗锯齿或更换玻璃材质；动态整车性能尚未解决。

## 工业 CAD 路径与本项目约束

[HOOPS 技术概览](https://docs.techsoft3d.com/hoops/visualize-desktop/general/technical_overview.html)介绍保留场景及按视图绘制/剔除。[渲染性能说明](https://docs.techsoft3d.com/hoops/visualize-3df/prog_guide/3dgs/07_4_performance_rendering_selection.html)进一步讨论按组织层次保存绘制、区分动态对象、视锥检查以及透明材质成本。这些机制需要结合实际场景和后端；该文也列出按屏幕尺寸省略对象、延迟绘制以及低质量透明近似，本项目没有采用这些会遗漏细节或改变效果的捷径。

现有 Three 视锥裁剪、逐帧单次阴影和精确静止缓存仍保留。当前考虑遮挡时必须分别核实颜色、玻璃透射、GTAO 法线/深度和阴影，不能直接把主相机上一帧的可见标志套到所有通道或移动机构上。

## 诊断实现

开发参数 `?render-worker=1&native-raf=1&occlusion-profile=1` 提供“记录一次实体可见性”。`lib/occlusionProfile.ts` 在完整模型下一次绘制的同步范围内，临时包装当前 renderer 的 `renderBufferDirect`，保留原函数接收者、参数、次序和所有绘制。仅对原相机、原 scene、没有 override material 的普通不透明 Mesh、开启深度测试与写入的调用加 ANY_SAMPLES_PASSED_CONSERVATIVE 查询。阴影相机、GTAO override、透明/线框及特殊实例类型不计入这些查询。

同一相机可能画入多个目标，因此记录实际 RenderTarget 身份、Three 请求的尺寸/采样数、GL SAMPLES、GL VIEWPORT 和首次调用堆栈。主目标取开始 composer.render 时的 readBuffer；其他目标分别标记。查询结果只有在 AVAILABLE 后才读取，不阻塞等待、不循环 gl.finish。完成后删除所有查询；异常也恢复原函数并释放，卸载移除诊断元素。普通入口没有查询和诊断元素。

`scripts/verify-occlusion-profile.mjs` 用真实 Three 几何和模拟 GL 验证原绘制/次序、源几何/材质不变，区分原相机与阴影/override/透明，按实际目标拆分、范围三角形计数、未完成查询不读结果、异常恢复和幂等释放。类型检查通过。

## 完整车辆测量

最终原始数据 `outputs/occlusion-profile/whole-actual-targets.json`、对应 AX 和 `summary.json`。同一 IAB 页面，8868 个几何实例均已装配；GL 错误 0。未改原图形设置，也未同时运行其他重型验证。

| 通道 | 实际 GL 采样 | 实际 GL 视口 | 不透明 draws | 三角形 | 零样本 draws | 零样本 draws 的三角形 |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 玻璃透射预绘制 | 4 | 1212 × 773 | 2315 | 5,393,928 | 1723 | 2,177,586 |
| 主颜色 | 2 | 1212 × 773 | 2315 | 5,393,928 | 1738 | 2,217,842 |

辅助目标的实际调用堆栈包含 Three `renderTransmissionPass`，主目标包含 `renderScene`。安装的 `node_modules/three/src/renderers/WebGLRenderer.js` 也确认该预绘制先绘制整个 opaqueObjects 列表，再根据条件补画透射对象背面并生成 mipmaps；主颜色随后又画同一个不透明列表。因此玻璃透射确实引入一遍约 539 万三角形的完整不透明处理，不能只按表面的玻璃面数理解其成本。

请求尺寸是 1212.5 × 773.75，但底层 GL VIEWPORT 是整数 1212 × 773。不能将 RenderTarget 的属性直接当成物理缓冲尺寸。请求采样 4 / 2 经 GL SAMPLES 核实也是 4 / 2。

零样本是该通道原绘制顺序下的结果，约 41% 主通道三角形落在零样本调用里，但不能直接等同于可节约的整车工作量。查询是保守的，允许假可见；后画的遮挡物也不会让先前查询倒推为不可见。不同捕获的零样本统计不同，未将其当成优化成效。移动、换视角、玻璃折射、GTAO 或阴影都需要独立的有效性证明。

最初 `whole-main.json` 错把两个目标合计称为单一主通道。它与 `whole-unclassified.json` 是同一初步记录，已在目录 README 明确标记口径错误，不可作为单主通道计数。第二次 `whole-classified.json` 已分目标，但还只有请求尺寸/采样；最终记录补足了底层 GL 状态。重采样是为了纠正口径和补足有效证据，不是挑选更好的时间。

## 排除的直接复制路径

曾分析在同一帧复用透射预绘制的不透明结果，以省去主通道重复几何处理。但当前预绘制与主缓冲实际采样数不同，且透射缓冲可能已经混入玻璃背面。直接复用会改变抗锯齿、深度或折射结果。

即使把请求采样对齐为 4，桌面 OpenGL 的多重采样缓冲间 blit 也不能直接搬到 WebGL 2。WebGL 2 继承相应 OpenGL ES 3.0 操作约束；[Khronos 官方 glBlitFramebuffer 参考源](https://raw.githubusercontent.com/KhronosGroup/OpenGL-Refpages/main/es3.0/glBlitFramebuffer.xml)明确规定 draw buffer 的 SAMPLE_BUFFERS 大于零产生 INVALID_OPERATION，见其 Errors 部分。当前没有编写或启用一个明知违反接口的复制实现，也没有通过降成单采样规避质量要求。

这一结论只排除上述直接多重采样复制方案，不表示任何形式的通道复用都不可能；进一步方案需要适合该后端的附件/通道组织与完整像素验证。

## 后续

所有机械求解、部件、材质和导出继续使用原实现。本阶段只提供更准确的成本/遮挡证据，不声称提速。继续优先验证能保持精度的图形后端与通道组织，再评估保守遮挡方案；不能将一次零样本结果变成跨帧全局 hidden 标志。完整外形、内构、各部件动力学、联动及最终产品验收仍为原 goal 的要求。

验证脚本、最终 TypeScript 检查和生产构建均以 exit 0 完成，日志位于 `work/occlusion-profile/`。构建仍提示 vinext 无法静态分类部分路由，未将该提示改写为完整发布验收。正常预览移除诊断查询参数，避免把大量开发数据面板留在用户操作流程中。

阶段归档目标为 `E:/Maz543/restoration/occlusion-transmission-profile-20260909`，仅复制本阶段源码、测试、测量和接手说明并核对 SHA-256，不覆盖之前的归档。完整 goal 保持 ACTIVE，16 项整车验收仍 OPEN。
