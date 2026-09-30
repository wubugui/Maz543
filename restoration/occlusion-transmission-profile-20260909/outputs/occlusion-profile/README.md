# 记录口径

`whole-unclassified.json`、`whole-main.json` 及对应 AX 是最初未区分渲染目标的记录。其名称和 kind 所称 main-pass 不准确，实际混合了玻璃透射预绘制和主颜色通道。不要把其中的 4630 draws / 10,787,856 triangles 当成单个主通道。

`whole-classified.json` 按实际渲染目标区分通道，caller 堆栈直接确认额外通道来自 Three 的 renderTransmissionPass。每个通道都是 2315 draws / 5,393,928 triangles。

`samples` 是 Three RenderTarget 请求值，width/height 也是对象中的请求尺寸；不能直接当成底层实际采样数或整数 framebuffer 尺寸。后续带 actualSamples / viewport 的记录才包含对应 GL 状态。

ANY_SAMPLES_PASSED_CONSERVATIVE 允许返回保守的假可见结果。单次零样本只说明该通道当前绘制顺序下没有通过的样本，不是跨帧可隐藏证明，也不是影子/GTAO 可跳过证明。两次诊断的零样本数量可能不同，不能据此声称性能已经改善。记录仅增加查询，未删除、跳过或重排任何绘制。
