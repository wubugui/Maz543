# 当前 IAB 的 WebGPU 可用性

2026-09-09，在与整车相同的 Codex IAB 内，通过 localhost 普通网页公开接口检查。

`navigator.gpu` 存在，安全上下文为 true；`requestAdapter({})` 与 `requestAdapter({powerPreference:'high-performance'})` 都返回 null。因此未创建 GPUDevice，未执行探针后续三角形/深度/4 倍采样验证。不能报告三角形验证通过，也不能据此声称机器没有物理显卡。

原始界面结果：`iab-ax.txt`。源码：`work/backend-probe/index.html`。临时静态入口 `public/maz-backend-probe.html` 已移除，探针标签已关闭。未更改浏览器设置、驱动、启动参数、端口或任何模型。

根据 [W3C WebGPU 规范](https://www.w3.org/TR/webgpu/)，适配器由浏览器选择，接口存在本身不保证请求返回可用适配器。当前结果排除了立即在此 IAB 中验证 WebGPU 整车迁移的路径；继续优化已有 WebGL 管线。完整 goal ACTIVE，整车功能/机械精度目标不变。
