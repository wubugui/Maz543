# 原精度静态/运动阴影深度组合实验

2026-09-09。完整 goal ACTIVE，16 项整车 gate OPEN。本实验仅开发入口 `inspect=shadow-partition-audit` 启用，普通预览仍使用已验证的完整阴影缓存。

## 依据与实现

参考工业可视化的静态显示结构与发生变化后重建的策略：[HOOPS 性能说明](https://docs.techsoft3d.com/hoops/visualize-desktop/prog_guide/0703_performance_considerations.html)。此处把复用范围限制为未变化部件的原精度阴影深度，不改变模型几何、内构、机械计算或彩色/法线/透射绘制。

检查本项目实际 Three r183 `WebGLShadowMap.js`，PCF 阴影使用单采样 UnsignedInt 原生深度纹理。`WebGLRenderer.js` 的 `copyTextureToTexture` 深度分支使用同尺寸 DEPTH_BUFFER_BIT / NEAREST blit；这是单采样深度目标之间的复制，和此前已否定的多采样透射颜色回填不同。[Three 官方复制接口](https://threejs.org/docs/pages/WebGLRenderer.html#copyTextureToTexture) 要求两侧目标已初始化；本实验先实际绘制静态影图、清理组合目标，再调用复制接口，随后通过 setRenderTarget 恢复原目标绑定。

`PartitionedShadowCache` 每个渲染姿态按原始完整 JS matrixWorld 和全部 morph 权重与上一帧 Object.is 对比。第一次出现的部件及有任何变化的部件走运动深度绘制；其余进入静态候选。静态缓存还按 DirectionalShadowCache 的原几何/索引/上传版本/材质/纹理/灯光/相机深度变换和可见集合完整签名确认。候选变动会重建静态图，移走旧位置的深度；未按部件名称臆测永远静止的结构。

完整场景先经过原缓存的保守适用性检查；自定义回调、裁剪、特殊网格、非标准深度及其他不支持路径保持整车原始阴影重绘。构建静态和绘制运动部分都调用实际 stock shadow pass，临时过滤 renderBufferDirect 中对应阴影相机的源绘制，未重写深度 shader。组合后彩色、GTAO、透射按原始路径执行。所有临时 renderer 函数和 light.shadow.map 都在 finally 恢复，异常使缓存失效并请求全图更新。

额外影图为 2048×2048，按颜色 4 + 深度 4 bytes/像素估算约 32 MiB；这不是驱动实际内存测量。纹理和目标归该实验所有，在退出时释放，不处理源模型资源。

## 当前证据

`scripts/verify-partitioned-shadow.mjs` 使用真实 Three 输入与模拟提交/深度集合，验证首次全动态、持续运动复用其余静态集合、1e-12 m 位移和 1e-15 morph 变化、几何/材质/灯光/显隐/资源释放失效、DoubleSide 原生版本变化，以及异常后函数与原图恢复。该测试不代替 WebGL 像素证据。

首次完整 8868 实例实际对照：候选和基线均 9305 draws、21,582,915 三角形，1212×773，0 不同像素、0 GL 错误。首次分类 0 静态、2322 运动，空静态图建立后确实复制 1 次。候选冷态同步 2457.0 ms，基线 1692.6 ms；包括首次分配和同步读回，不据此宣称提速。原始证据 `outputs/partitioned-shadow/whole-cold-ax.txt`。

预热后 2322 静态 / 0 运动，静态影图不刷新，整帧 6983 draws、16,187,549 三角形，0 不同像素、0 GL 错误；同步配对候选 1459.3 ms、原始 1640.3 ms。该静止状态原有完整阴影缓存也能覆盖，不能算新方案相对已启用缓存的新增收益。

实际引导启动后发动机约 549 RPM，自行运转、机械 240 Hz、待推进 0。该帧 1941 静态 / 381 运动，静态图不重建，只画 381 次运动阴影，确实复制一次深度；整帧 7364 / 原始 9305 draws，17,344,748 / 原始 21,582,915 三角形，0 不同像素、0 GL 错误。配对同步耗时 1535.9 / 1593.1 ms，仅约 3.6% 小样本差，界面仍约 0.6–0.7 FPS。它支持本工况的源绘制复用和像素一致，不证明流畅性已恢复，也不证明稳定帧率提升。

侧视、右舱前门 99°、发动机约 549 RPM 的组合工况仍为 0 不同像素、0 GL 错误；静态/运动分区同上。选中部件增加一次线框绘制，候选/原始 7365/9306 draws，三角形仍为 17,344,748/21,582,915；同步配对 1619.5/1684.9 ms。以上均为候选先行的同姿态同步小样本，静态图更新成本计入候选，没有把建图预处理从计时中删去。

尚未默认启用。后续仍需要处理大量主色/法线/透射绘制在 Microsoft Basic Render Driver 后端的成本；本次没有将显示实验当作完整产品目标完成。

纵剖被识别为 `shadow clipping`，正确退出分区，0 次深度复制；候选和原始均 9138 draws、20,352,995 三角形，0 不同像素、0 GL 错误。配对 1728.4/1752.9 ms 不代表退出路径提速。该捕获中分区计数都为 0，只表示没有进入分区提交统计，并非没有绘制；原始 extraBytes 报 0 是退回分支统计遗漏，已有缓存影图仍保留至退出实验。随后仅修正该字段，使其报告已保留影图的估算字节数，未重绘或改写这份原始证据。

## 源完整性与构建

针对性分区缓存测试和原完整缓存回归通过。`verify-partitioned-shadow-integrity.py` 核对 11 个机械/导出文件、16735 字符的原始整车姿态更新段及显示质量设置，与最近适用不可变归档一致。

异常注入测试促使额外补上失败路径的原 render target/face/mipmap 绑定恢复，已重新通过测试、类型检查和最终构建（均 exit 0）。此补充只作用于异常路径，前述成功像素样本没有使用该分支；并不承诺 stock renderer 内部状态在任意异常后可继续运行，异常仍向现有 Worker 生命周期错误处理传播。首次类型检查中的通用 RenderTarget / WebGLRenderTarget 不匹配日志保留，当前使用实际运行类型检查收窄。最终构建仍有既有 vinext 路由静态分类提示。

证据分别在 `outputs/partitioned-shadow/` 与 `work/partitioned-shadow/`；`summarize-partitioned-shadow.py` 从 AX 原始文本提取每个 JSON 及 summary，不覆盖失败或冷态记录。

退出诊断后实际恢复 `http://localhost:3000/?render-worker=1&native-raf=1`：8868 实例、画面已缓存、独立机械计算 240 Hz、待推进 0.000 s。`final-normal-ax.txt` 和已查看的 `final-normal.png` 证明完整车辆再次显示，诊断覆盖层已移除；当前默认取景中车辆仍偏小，不能因此宣称最终写实展示/构图验收通过。

阶段归档 `E:/Maz543/restoration/partitioned-shadow-20260909` 逐文件 SHA-256 核对，不覆盖旧归档。下一步应针对实际动态显示成本继续推进，不重复把相同几组像素配对当作性能结论。两项新实验均关闭，原始完整机械/产品目标保持 ACTIVE，16 项验收 OPEN。
