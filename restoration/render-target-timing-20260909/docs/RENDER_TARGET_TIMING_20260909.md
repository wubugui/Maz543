# 各渲染目标的命令与状态往返计时

完整产品 goal ACTIVE，16 项整车验收全部 OPEN。此阶段只做有限诊断，没有删除或减少任何绘制、几何、材质、功能或机械计算，也没有性能完成结论。

## 方法与限制

开发入口 `inspect=target-timing-audit` 使用 `lib/renderTargetTiming.ts` 包装本 renderer 的 `setRenderTarget` 和 `renderBufferDirect`。全部原调用、接收者、参数及先后次序保持；记录每个目标的调用/三角形、材质标签和命令往返墙钟时间，成功或异常都恢复 hook。自有诊断不分配 GPU 目标，也不释放源资源。候选先画、原始后画，同一机械姿态读取最终完整 RGBA 比较。

不能把 WebGL `finish()` 的返回直接当 GPU 完成。查询时的 [Chromium 官方 HEAD 源码](https://chromium.googlesource.com/chromium/src/+/HEAD/third_party/blink/renderer/modules/webgl/webgl_rendering_context_base.cc) 中，该方法调用 `ContextGL()->Flush()`，注释为 “Intentionally a flush, not a finish.”。这是公开源码证据，不是对当前 IAB 二进制版本的反编译证明。

当前应用实际查询 `EXT_disjoint_timer_query_webgl2` 不可用。最终报告明确 `gpuCompletionProven:false`：区间包含提交、同步状态读取时的驱动/命令队列等待及该目标的解析、mipmap 命令工作；不是硬件 GPU 执行时间，不能据此逐毫秒归因 GPU，也不是稳态 FPS 基准。

第一版在 `getParameter` 前结束区间，整帧 1098.5 ms 而分项合计约 59.1 ms，遗漏状态读取的主要等待。保留 `still-incomplete-boundary.json` 作为已拒绝计时边界的证据，汇总不采用它。修正后包括每段 stateReadWaitMs，并将测量前命令/状态往返单独放在 initialStateRoundTripMs；以确定性假时钟测试验证这部分等待不会落到账外。`still-state-waits-v1.json` 是修正区间、尚未明确 GPU 完成限制的中间记录，同样不用于最终汇总。

## 实际结果

完整 8,868 实例，1212×773 实际绘制尺寸，IAB Basic Render Driver；诊断在既有 DEV Worker / native RAF 中运行，独立机械计算 240 Hz。下面是命令/状态往返墙钟分布，单位毫秒，禁止重标为硬件 GPU 耗时。

| 区间 | 静止预热 | 侧视、右前门 99°、约 549 RPM |
| --- | ---: | ---: |
| 阴影深度 | 41.1 | 31.6 |
| 透射预绘制（请求 4 samples） | 278.1 | 306.5 |
| 主颜色（请求 2 samples） | 477.8 | 502.8 |
| 法线缓冲 | 305.1 | 276.1 |
| GTAO 求值 | 0.8 | 2.3 |
| Poisson 降噪 | 1.6 | 5.6 |
| GTAO 拷贝与混合 | 5.2 | 1.6 |
| 最终 OutputShader | 2.0 | 1.2 |
| 整次捕获 | 1119.5 | 1134.4 |
| 未归入分项的开销 | 0.3 | 0.0 |

其余为目标切换/清理区间。两次候选与基线调用数、三角形数完全相同：静止 9,305 调用、动态 9,306 调用，均 21,582,915 三角形。两次最终差异像素 0、最大色阶差 0，候选/基线 GL 读回错误及诊断 GL 错误均 0。汇总逐项核对 draw/triangle 账目及各段时间和总账。

目标对象保存的尺寸为 1212.5×773.75，实际 framebuffer 是整数尺寸；报告没有把对象的浮点尺寸当作实际像素数。`endFramebufferSamples` 和 `endFramebufferDepthBits` 是关闭区间时的绑定状态，不冒充每次绘制时的采样配置证明。主颜色/透射分类结合实际请求样本数和本地 Three r183 原始渲染路径，法线与后处理用材质实例标签区分。

## 验证、状态与下一步

`verify-render-target-timing.mjs` 验证真实 Three 资源配合受控传输时的原调用保留、实际 ShadowMap 使用 null scene 的分类、确定性状态等待总账、异常恢复与源资源不释放。类型、最终构建和机械/导出不变基线通过（11 个文件、16,735 字符位姿块、质量设置不变）。

原测试 tab 8 曾从 IAB 会话列表消失，原因没有证实；此前数据及法线复用阶段已写盘并归档。新建本任务 tab 10 后继续验证，没有操作其他浏览器标签、驱动、设置或端口。

这些数据把下一步调查集中到原相机的主颜色、透射和法线几何通道，但不证明某个 GPU 阶段的精确占比。应继续尝试在原始通道上下文中保留/重放同一已链接顶点程序、同一几何和矩阵建立深度快照，先核对程序身份、采样/深度条件及画面，再考虑扩大遮挡复用。禁止直接把法线快照套到颜色通道，也禁止把当前有限计时或上一阶段零像素差异当作整车精度/性能最终验收。
