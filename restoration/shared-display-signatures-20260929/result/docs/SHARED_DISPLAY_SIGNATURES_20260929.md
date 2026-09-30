# 共享显示资源检查（2026-09-29）

完整 goal 保持 ACTIVE，整车 16 项验收仍 OPEN。

本轮只减少判断是否需要重绘时的重复 CPU 工作：`DisplayFrameCache` 每次比较仍记录每个零件的矩阵、可见性、渲染顺序、几何和材质引用、morph 权重；同一次比较内，共享几何与材质只读取一次。去重集合每帧重新建立，因此仍检查直接材质修改、属性替换和更新版本。最后一个共享材质使用者的自定义回调也能阻止不安全的材质版本确认。

完整质量路径现在也使用既有的相机快速判定：相机一变就请求完整重绘，略过必然无法命中的整场景画面缓存检查；下次完整比较重新建立基线。没有省略颜色、透射、AO、阴影或零件绘制，没有改变建模、机械步长和导出内容。

## 验证

- 对保存的改前真实源码进行 1,212 次状态比较：逐件运动、隐藏/显示、材质和几何换绑、资源内容更新、morph、相机快速路径与恢复；结果一致。
- 既有 `verify-display-presentation.mjs`、`verify-rendered-material-versions.mjs` 通过，覆盖资源共享、拾取身份、实际小场景 GLB 字节不变和共享双面材质回调保护。
- 构造场景：3,043 个网格、600 份几何、67 个材质，交替次序测量 120 组 Node CPU 缓存检查。中位数 10.1363 → 5.1416 ms，p95 15.3297 → 8.2664 ms；签名数值 170,483 → 87,556。这不是整车 FPS 或 GPU 测量。
- 30 份运行模型、贴图、元数据、机械与导出相关文件与本轮修改前 SHA256 相同。
- TypeScript 检查与生产构建通过；本地预览 HTTP 200。

报告：`outputs/shared-display-signatures-20260929/signature-tests.json`。改前源码和哈希：`../restoration/shared-display-signatures-20260929/`。

## 精度边界与后续

9 月 28 日的普通入口仍使用交互近似显示：微小零件剔除、暂缓 GTAO、近似玻璃、降低运动阴影更新频率。历史约 60 FPS 不能作为全程原质量的验收。本轮未重写这项既有改动；后续优先对 `?quality=full` 验证连续相机运动、发动机、开门、透视/剖切、拾取和完整像素，再决定默认显示策略。

本轮浏览器控制返回 `nodeRepl.fetch request failed`，无法读取标签页，因而整车画面对照和真实 GPU 帧率仍未验证。不得用本轮 Node 微基准代替它们，也不得将既有 Basic Render Driver 和 GTX 970 的历史结果混用。

工业 CAD 参考采用共享表示和空间裁剪等方向，但不直接照搬降细节设置。Open CASCADE 将表示与业务数据分离，并提供 BVH 视锥裁剪；SOLIDWORKS 的大装配设置也包含降低显示细节的选项，这类选项不满足本任务完整精度的验收要求。

- [Open CASCADE visualization](https://sso.opencascade.com/doc/occt-6.8.0/overview/html/occt_user_guides__visualization.html)
- [SOLIDWORKS large assembly settings](https://help.solidworks.com/2024/english/SWConnected/swdotworks/r_Large_Assembly_Mode_SWassy.htm?id=5.11.3.7)

Blender 全部走 `http://denghong01:8765` Hub；禁止运行本机二进制。
