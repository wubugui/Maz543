# 完整应用的独立浏览器后端对照

完整 goal ACTIVE，16 项整车验收 OPEN。上一阶段的主色/法线/透射与阴影成本仍待解决。

在已有 Chrome 中新建本任务自己的比较页，访问相同 `localhost:3000` 应用与完整 Worker/native RAF 入口；待 8868 实例全部装配后，引导启动发动机，使用已有有限采样器记录 12 个完整动态帧。其他用户标签页未操作，未改浏览器设置、驱动、端口。取证后已关闭比较页。

当前 Chrome 的应用内公开 WebGL 后端字符串同样是 `ANGLE (Microsoft, Microsoft Basic Render Driver (0x0000008C) Direct3D11 vs_5_0 ps_5_0, D3D11)`。这是实际应用测量，没有访问内部 GPU 页面。12 帧均为 9305 draws、21,582,915 三角形，机械积压最大 0。平均帧起点间隔 1432.236 ms，中位数 1433.7 ms，平均同步提交区间 200.233 ms；页面约 0.7 FPS，发动机约 547 RPM。

该浏览器画布实际 2141×786、CSS 1713×629，与此前 IAB 的 1212×773 不同，不能直接把两个时间作为同尺寸性能排名。这一观察只证明换到当前已有 Chrome 没有自动得到不同的硬件后端或流畅的完整预览；不证明物理机器没有可用 GPU，也不定位浏览器配置/驱动的具体原因。既有“内置预览是唯一原因”的假设不成立，后续仍需处理显示负载。

原始 AX、逐帧 JSON、尺寸和统计见 `outputs/browser-backend-comparison/`。没有因此降低几何、模型细节、贴图、采样或机械计算精度。

同时检查了实际 Three r183 透射 shader：当前原生 Laminated_glass transmission=0.75、roughness≈0.08，无 volume thickness 扩展。不能仅凭该 roughness 常数缩小透射背景区域，因为实际 shader 还加上屏幕法线导数形成的 geometryRoughness，并进行分级双三次采样；透射背面还依赖中间结果。因此本阶段没有采用未经覆盖范围证明的玻璃区域裁剪。
