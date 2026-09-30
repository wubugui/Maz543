# 完整绘制阶段计时与原生 Worker 动画帧

2026-09-09。完整 goal **ACTIVE**、16 项 **OPEN**。本阶段继续处理预览迟滞，不降低部件细节、贴图、阴影、求解频率或导出能力。

## 诊断入口和实现

`?render-worker=1&frame-profile=1` 增加一个开发用按钮，手动记录后续 12 个完整模型帧。`framePhaseProfile.ts` 测量渲染线程的姿态/相机/标签更新、查询检查、严格缓存检查、绘制提交和总工作时间。不调用 `gl.finish`、读回像素，不冻结状态，也不强制本应复用缓存的帧重画。采样后停止计时，退出组件清理两个自有元素。普通入口及无诊断参数的 Worker 不增加这些采样。

`?render-worker=1&frame-profile=1&native-raf=1` 额外选择 Dedicated Worker 原生 requestAnimationFrame。它执行同一完整 `createVehicleViewport`，以 Worker 本地 performance.now 作为回调时间。没有主线程每帧消息往返。仅在此开发参数下试验；普通入口和原 Worker 默认仍保持此前路径。

`workerViewportHost.ts` 把虚拟帧号映射到原生帧号，保证一次执行和取消；0 号原生句柄也正确取消。原生接口不存在或抛出 NotSupportedError 时使用原来的主线程动画帧桥接，其他异常如实抛出。桥接消息不能提前触发正在等待的原生回调。原有指针、标签、尺寸、显隐及机械控制通路不变。

为核实消息排队，`mechanics.worker.ts` 在发布状态的外层消息增加 `publishedAtEpochMs = performance.timeOrigin + performance.now()`。主通路和渲染通路收到同一消息。它不进入求解器、积分步长或物理状态。诊断在采用状态时按同一 epoch 计算消息年龄；复位清除旧时间戳。不能直接用两个 Worker 的 performance.now 或模拟时间相减冒充传输延迟。

## 实际样本

原始网页可访问文本及 JSON 在 `outputs/frame-profile/`，汇总由 `scripts/summarize-frame-profile.py` 生成，保留每帧数值和异常值。所有样本均使用同一完整模型和当前软件渲染器，未运行减面/低分辨率模式。

原桥接整车外观 12 帧：每帧 9,305 draws、21,582,915 个累计三角形；姿态及界面更新中位数 4.0 ms，缓存 20.6 ms，提交 302.85 ms，渲染线程工作 330 ms，帧起点间隔中位数 1,938.4 ms。两次提交约 1.86/1.87 秒。不能把未包含在线程工作中的间隔全部归为 GPU 运算。

原桥接传动纵剖、发动机自行运转 12 帧：每帧 2,849 draws、3,139,593 个累计三角形；更新中位数 3.8 ms，缓存 10.6 ms，提交 57.35 ms，总工作 70.2 ms，帧间隔中位数 990.2 ms。原生 Worker 传动样本保持完全相同的 draw/triangle 数，帧间隔约 0.51–0.58 秒。原生整车仍慢，没有据此声称解决整车性能。

所有这些帧报告 240 Hz 求解、积压 0。GPU 独立计时没有返回结果；渲染线程提交时间包含同步驱动等待，不能标为 GPU 时长。帧起点也不是画面实际呈现完成时刻。采样顺序、缓存及运行负载没有做严格随机控制，不能把有限样本之比当作普遍加速倍率。

增加统一 epoch 时间戳后，传动原生样本帧间隔中位数 **550.0 ms**，桥接复测为 **992.2 ms**；两者仍为 2,849 draws / 3,139,593 三角形。消息年龄中位数分别约 10.05 / 12.20 ms，最大约 454 / 522 ms，均有排队异常值。不能把先前不同时间原点的模拟时间差称为数秒消息延迟，也不能声称原生调度消除了排队。整车原生帧间隔中位数 1,917.0 ms，原桥接 1,938.4 ms，没有明显整车收益。

## 已检查和继续事项

原生调度测试覆盖一次回调、本地时钟、取消、0 号句柄、不支持回退以及意外异常不被吞掉。实际 OrbitControls、文档拖动、缩放、平移、尺寸、显隐和标签生命周期回归通过，7 个运行时 GLB 哈希不变。真实 Node Worker 阻塞 2 秒时，门在约 633 ms 到 40.625°，复位在绘制阻塞期间完成，两通路完整状态（含新时间戳）一致，仍为 240 Hz。类型检查通过；生产构建和后续观察见本文件补记。

`source-integrity.json` 进一步逐字节核对 8 个求解源文件与上一已封存阶段相同；机械 Worker 发布代码仅增加外层时间戳和说明注释，没有其他差异。

下一步仍需减少实际绘制负担，并完成完整 Worker 默认启用前的失败清理/恢复、生产入口、像素、标签、剖切、尺寸及真实拾取验证。帧调度实验尚未关闭这些门槛。

可进一步检查阴影输入是否真正变化：固定光源下，同一阴影相机看到的几何可能不变，而观察相机仍在变化。若实施缓存，必须对实际阴影绘制输入做完整一致性验证，覆盖光源/材质/透明裁剪/形变/可见性及失效；不能拿摄像机不动、低速或任意位移阈值作为复用理由。当前**未实施跨帧阴影复用或新的剔除算法**。

## 工业显示参考及适用边界

[Open Cascade 渲染流程](https://www.opencascade.com/blog_tag/visualization/) 区分持久内容和即时内容，以缓存的帧缓冲支持高亮等交互，并在结构绘制前用 BVH/视锥、裁剪范围排除不可见对象。当前模型仍包含运动机构和实时阴影，需要独立判定各输出的失效条件。

[HOOPS Visualize 性能文档](https://docs.techsoft3d.com/hoops/visualize-3df/prog_guide/3dgs/07_4_performance_rendering_selection.html) 讨论表示缓存、动态部分分离、视锥范围检查与高亮更新。其按像素大小不画小物体、降低透明层数等选项不适用于本任务的保精度要求，未采用。

[MDN Dedicated Worker requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/DedicatedWorkerGlobalScope/requestAnimationFrame) 明确原生 Worker 动画帧需要关联的 owner window，并可能在后台或隐藏时暂停。因此原生 RAF 不是绕过浏览器显隐策略的计时器；本实现保留原显隐及机械暂停语义。[Three 官方 OffscreenCanvas 示例](https://threejs.org/manual/en/offscreencanvas.html) 亦使用完整共享场景与 Worker 渲染。

前阶段：[资产精度和切线追踪](DISPLAY_ASSET_PRECISION_20260909.md)。完整整车导出仍有 82 个真实表面切线错误，零量化资产试验尚未替换原运行时资产。原有浏览器拒绝内部 GPU 页面诊断的边界不变，未绕过，也未改驱动、系统或服务器设置。

本阶段收尾：类型检查与生产构建通过，日志 `work/frame-profile/types-age.log`、`build.log`。生产构建仍保留开发参数限制，因此这不是生产 Worker 的浏览器验证。有限原生/桥接样本已经保存，未为追求更好的数字重复跑完整模型测试。继续项仍是完整绘制、Worker 发布门槛和全车机械 goal。
