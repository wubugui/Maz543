# MAZ-543A · Blender 机械解构

本项目提供 Blender 建模资产和可在浏览器操作的三维工作台。外观统一参考量产 MAZ-543A 双驾驶室照片；轮胎采用有产品规格资料的 VI-203 形态，不代表某辆早期车辆的原装轮胎。

## 可使用的文件

- `outputs/MAZ543A_Master.blend`：原始 Blender 外观网格、倒角、细分与厚度修改器、参考图对象、Cycles 灯光。
- `outputs/MAZ543A_Textured.blend`：烘焙 PBR 材质、可编辑网格、命名总成与已烘焙的机构动画。
- `public/models/maz543a-blender.glb`：浏览器实际加载的 Blender 导出资产。
- `outputs/D12A525A_Engine_Master.blend`：按原厂照片、525A 维修照片和 D12 剖面图重建的发动机，包含 148 个命名运动节点。
- `public/models/d12a525a-engine.glb`：独立加载的发动机模块；已附入两份整车 Blender 工程。
- 凸轮轴新增空心油道、径向孔、双孔可拆轴承座、22 齿互啮齿轮、24 齿进气组合齿轮与 41/10 齿调相套。原车相位已核对，升程、尺寸和完整上游传动仍待标定或补全。
- `outputs/MAZ543A_Suspension_Master.blend`：双扭杆、叉臂、轴管/花键、双筒减振器及半轴的可编辑母版；包含结构参考和关节动画。
- `public/models/maz543a-suspension.glb`：独立悬挂模块，浏览器使用四连杆和轮胎接地力求解驱动。
- `outputs/MAZ543A_Starting_Master.blend`：C5 惯性启动驱动、MZN-2 齿轮泵和照片拟合的 MN-1 定子，含 167 个可编辑部件、7 个运动节点及来源图。
- `public/models/maz543a-starting.glb`：独立启动模块，已附入两份整车 Blender 工程。
- `docs/STARTING_REFERENCE_REGISTER.md`：逐部件来源类别、确认参数与拟合尺寸；清单在 `outputs/starting-parts-register.json`。
- `docs/D12_REFERENCE_REGISTER.md`：发动机部件来源和尺寸状态；逐件清单在 `outputs/d12-parts-register.json`。
- `outputs/maz543a-textured-preview.png`：Blender Cycles 渲染。
- `docs/REFERENCE_NOTES.md`：图片出处、型号差异、参考尺寸及准确性限制。

## 浏览器操作

拖动旋转、滚轮缩放、点击选择部件。右侧可以启动发动机、调整油门/挡位/制动、操纵前两轴转向、展示悬架台架运动、打开车门和分离总成。提供透视、纵剖、标签、单独查看与当前姿态 GLB 导出。浏览器的 GLB 导出包含当前模型和贴图，不携带网页控制程序。

四扇门可分别开闭，角度连续变化。点击“发动机内构”进入独立检查，可切换“完整外观”“打开气门室盖”“曲柄与配气”，并暂停机构运动。新模型包含 48 个气门、四根凸轮轴与主副连杆铰接机构；不表示全部附件内构或真实启动过程已经完成。

点击“电启动机构”可分别观察 C5、预润滑泵及安装关系，移除外壳或移开电枢检查定子。引导启动先建油压，再带转发动机，发动机自行运转后退出启动驱动；断油后按惯性停机。原车分步操作提供独立搭铁、燃油、预润滑和启动控制。默认按钮为按住生效；可开启明确标注的网页辅助保持功能。慢动作与暂停共同作用于发动机、启动机和预润滑泵。

## Blender 动画

整车两份工程的发动机与启动机构使用同一套 0–600 帧、60 FPS 的启动及断油滑行采样。D12 独立母版保留 1–241 帧的 720° 配气与连杆检查循环。旧车体的门、转向和车轮展示键仍保留在早期时间段，整车所有系统的统一时间线尚未完成。需要观察内构时，可隐藏各总成外壳。

## 精度范围

本项目仍在建设中，完整验收要求见 `docs/ACCEPTANCE.md`，所有整车验收项保持 OPEN。模型未经原厂公差、实车扫描或试验标定，不是完整工程数字样机。

发动机曲柄连杆、凸轮挺柱和悬架四连杆采用几何约束；悬架竖向求解包含扭杆弹性、减振和单向轮胎接地力，参数未标定。电启动采用集总电气、油路、惯量与调速扭矩模型；燃烧热力、气启动、完整电路和油道仍未完成。变速、转向液压、制动及其他车辆功能仍有简化或缺项。照片或剖面支持的结构，与没有原厂尺寸的拟合部分，分别记录在来源清单中。构建通过不代表写实或工程精度验收通过。

## 本地运行与验证

需要 Node.js 22.13+。运行 `npm install` 后执行 `npm run dev`。生产构建使用 `npm run build`。

### 完整静态诊断候选（独立开发入口）

`npm run prepare:static-diagnostic` 从已发布的
`outputs/cloud-native-static-suspension-20261002` 的 171 个有序原始 parts 恢复
`work/native-static-preview/native-static.glb`。恢复脚本核对每块和完整文件的长度、SHA，
不会覆盖已有文件。缓存已存在时可直接启动；若校验失败，请保留该文件另行核对。
这份 134,267,928 字节 GLB 的唯一 Git 表示仍为 parts + manifest + restore，
缓存受现有 `/work/` 忽略规则保护，不复制到 `public` 或新增 LFS 对象。

运行 `npm run dev:static-diagnostic`，打开
`http://localhost:3001/diagnostics/native-static/`。截图固定镜头入口为
`?view=overview`、`?view=front`、`?view=side`、`?view=rear`。
“保存当前视图 PNG”下载真实 WebGL 画布，在画面外加 64px 诊断状态标题带，不修改模型像素。
页面仅移动相机，使用真实 GLTFLoader 和 OrbitControls；原始节点姿态、完整导出范围与
导出材料保持，不导入旧 vehicleViewport 或动力学/legacy overlay。开发服务和浏览器
均核完整 SHA-256 后才解析；资产未恢复或不匹配会明确停止，不回退其他模型。
浏览器须使用 localhost 或 HTTPS 安全上下文，以便执行 SHA-256 校验。

页面显示“待核对诊断候选”、法线/联合属性 FAIL、2299 issues、16 门 OPEN 和静态
frame 0。加载成功仅代表实际解析及第一帧 render，不能代替真实浏览器截图、材料/法线
检查或整车验收。观察灯光不代表 Blender shader 等价。为云端诊断限制像素比 1、
画布最多 1280×800，且只在相机/窗口变化时重绘。

`npm run build:static-diagnostic` 仅核验该独立页面可打包，输出在
`dist/static-diagnostic-check`，不含模型及仅开发期的资产路由，不能作为可独立部署站点。
原 `npm run dev`、`npm run build` 和生产默认入口不变。

`node scripts/verify-model.mjs` 检查轴距、活塞行程、连杆定长、转向中心、内外轮转速、制动保持、有限变换、导出的关节名称与 glTF 文件。该检查不等价于浏览器视觉检查。

`node scripts/verify-d12.mjs` 另行检查新发动机的主副连杆闭合、180/186.7 mm 标称行程拟合、上止点关系、凸轮与平面挺柱接触、148 个导出节点及 glTF。数值一致性不等于原厂尺寸认证。

凸轮轴重建流程：先运行 `node scripts/prepare-d12.mjs`，再用项目 Python 执行 `scripts/prepare-cam-profiles.py`；在 Blender 后台执行 `scripts/update-d12-cams.py`、`scripts/verify-cam-native.py` 和 `scripts/verify-d12-native.py`。确认后运行 `node scripts/prepare-starting.mjs`，再在 Blender 执行 `scripts/update-starting-assets.py`，让两个整车工程、启动序列和浏览器模块保持一致。`--sleeves-only` 用于只重建调相套；`--render-only` 只更新材质/法线和检查图，不重跑已经完成的齿轮网格检查。

在浏览器选择“发动机内构 → 凸轮轴与齿轮”，可切换缸列、放大齿轮端并暂停观察。原始图号、传动比和未完成部位见 `docs/D12_TIMING_SOURCE_NOTES.md`。

## 资产重建

1. `node scripts/prepare-blender.mjs` 导出简化机械机构底稿。
2. 用项目 Python 运行 `scripts/prepare-cab-profile.py`，再用 Blender 4.5 LTS 后台运行 `scripts/blender-model.py` 创建原生外观网格和母版。
3. 运行 `scripts/blender-export.py` 展 UV、烘焙基础色/粗糙度/法线/AO/金属度，并导出压缩 GLB。
4. `node scripts/bake-animation.mjs` 生成机构动画采样。
5. Blender 运行 `scripts/blender-animate.py` 校正门轴、保存动画工程并导出中立姿态模型。
6. `node scripts/prepare-d12.mjs` 生成新发动机的关节采样。
7. Blender 运行 `scripts/blender-d12.py` 创建发动机原生母版、两张检查渲染和独立 GLB。
8. Blender 运行 `scripts/attach-d12.py` 将新发动机附入两份整车工程，移除旧简化发动机，导出独立车体 GLB。
9. `node scripts/prepare-suspension.mjs`；Blender 运行 `scripts/blender-suspension.py` 生成悬挂模块和表面贴图。
10. Blender 运行 `scripts/attach-suspension.py` 将悬挂附入两份整车母版，并校正轮胎旋转原点。车体 GLB 排除单独下载的发动机与悬挂。
11. `node scripts/verify-suspension.mjs` 校验闭合与竖向动力学；Blender 运行 `scripts/verify-suspension-native.py` 检查实际母版关节与减振器间隙。
12. `node scripts/prepare-starting.mjs` 导出启动、油泵和 D12 同步姿态；Python 运行 `scripts/prepare-gear-profiles.py` 生成齿形（依赖 Shapely；本地位于 `work/pythonlibs`）。
13. Blender 运行 `scripts/blender-starting.py` 创建启动母版和独立 GLB；`scripts/update-starting-assets.py` 将其及同步发动机时间线写入两份整车工程。仅修改启动网格时可用 `scripts/attach-starting.py` 刷新模块。
14. `node scripts/verify-starting.mjs` 检查启动/停机、独立手动电路、几何相位与 GLB。Blender 运行 `scripts/verify-starting-native.py` 检查实际齿面、定子间隙并输出局部渲染；`scripts/verify-starting-installation.py` 检查整车安装和发动机时间线一致性。
15. `node scripts/verify-model.mjs`、`node scripts/verify-d12.mjs`、`npx tsc --noEmit` 和 `npm run build` 完成相应资产与应用检查。实际浏览器观察记录在 `docs/BROWSER_QA.md`。

参考图在建模脚本中默认读取 `D:/maz543-references`；移动项目时请更新该路径。参考照片不嵌入网页模型贴图。Blender 二进制与工作缓存位于被忽略的 `work` 目录。


正时传动增量：用项目 Python 顺序执行 `scripts/bevel_geometry.py`、`scripts/prepare-timing-spurs.py` 和 `scripts/prepare-timing-caps.py`，再在 Blender 执行 `scripts/update-d12-timing.py` 与 `scripts/verify-timing-native.py`。最后执行启动序列准备、`scripts/update-starting-assets.py` 和现有导出检查。重建凸轮轴后需要重新执行正时增量，以替换早期的凸轮轴锥齿轮部分。原车齿数与重建尺寸的区别见 `docs/D12_TIMING_SOURCE_NOTES.md`。

循环水泵：浏览器选择“发动机内构 → 循环水泵”，可以合壳、剖开、观察轴封和叶轮底部、暂停或慢放。按原车图 28 建模，尺寸、轴承规格、流量和载荷仍待标定。先执行 `node scripts/prepare-d12.mjs` 和 `node scripts/prepare-starting.mjs`，再用 Blender 运行 `scripts/update-d12-water.py`、`scripts/verify-water-native.py` 和 `scripts/update-starting-assets.py`；导出后执行 `node scripts/verify-water-web.mjs`。重新生成正时轴时，需再生成水泵以恢复其输入联轴器。图号与精度边界见 `docs/D12_WATER_PUMP_NOTES.md`。

双风扇冷却系统：快捷入口“冷却系统”提供左右离合器开关、手动百叶窗、暖风水阀、温度和流量读数，以及左风扇离合器和下传动箱的独立内构近景。实际 Blender 模块为 `outputs/MAZ543A_Cooling_Master.blend`；1,237 个网格/曲线对象和 254 个姿态绑定不代表原车 BOM。先运行 `node scripts/prepare-starting.mjs`，再用 Blender 运行 `scripts/blender-cooling.py`、`scripts/rebake-starting-native.py`、`scripts/update-starting-assets.py`、`scripts/install-cooling-assets.py`。检查脚本为 `verify-cooling.mjs`、`verify-cooling-native.py` 和 `verify-cooling-install.py`。原始图号、拟合参数与缺失机构见 `docs/COOLING_REFERENCE_NOTES.md`；完整冷却系统和整车仍未验收。

下传动箱重建：先用项目 Python 执行 `scripts/prepare-cooling-lower.py`，再执行启动姿态准备与 `scripts/blender-cooling.py`。建模脚本会调用 `cooling-lower-detail.py` 和 `cooling-lower-surfaces.py`，生成原生几何并烘焙铸壳法线/粗糙度。`verify-cooling-lower.py` 检查实际齿轮与铸壳网格、轴承外廓并渲染检查图。只重新导出已有母版时使用 `export-cooling-native.py`，无需重新烘焙；最后运行 `install-cooling-assets.py`、`verify-cooling-install.py` 和 `sync-cooling-notes.py`。32:20 齿数、局部尺寸仍是拟合值。

上齿轮箱：先运行 `prepare-cooling-upper.py` 和 `prepare-starting.mjs`，再用 Blender 执行 `update-cooling-upper.py`、`verify-cooling-upper.py`、`install-cooling-assets.py` 和 `verify-cooling-install.py`。浏览器“冷却系统 → 检查左上齿轮箱”提供独立检查。上下齿轮箱的局部齿轮已重建，但安装位置和完整传动闭合尚未通过核验。

万向轴接口：`cooling_interfaces.py` 按万向轴展开图统一四孔连接，孔距、外径与配合仍是估算值。Blender 执行 `update-cooling-interfaces.py` 可只替换四个法兰并导出，之后执行 `verify-cooling-interfaces.py` 检查实际贯穿孔和闭合网格，再安装到整车并检查同步姿态。完整重建上下齿轮箱也会调用同一接口函数。

万向轴独立检查：浏览器“冷却系统 → 检查万向轴”提供 0–30° 工作角、0–40 mm 花键伸出量、开壳和启动联动。先运行 `node scripts/prepare-cardan.mjs`，再用 Blender 执行 `scripts/blender-cardan.py`，随后运行 `node scripts/verify-cardan.mjs` 和 Blender `scripts/verify-cardan-native.py`。母版为 `outputs/MAZ543A_Cardan_Master.blend`，包含 213 个网格及 190 个运动节点。该模块尚未安装进整车传动链；来源、拟合尺寸和已发现的驾驶室/风扇罩冲突见 `docs/CARDAN_REFERENCE_NOTES.md`。可运行 `scripts/audit-cooling-installation.py` 重查实际装配网格。

本地预览故障恢复：若 Miniflare/workerd 的本机连接持续超时，可在当前 PowerShell 进程设 `$env:MAZ_NODE_PREVIEW='1'` 后运行 `npm run dev -- --host 0.0.0.0`。此模式使用 vinext 的 Node 开发服务，保留 Sites 插件，适用于当前不依赖 Worker 绑定的客户端模型页面；不能用于验证 Worker/D1/R2 行为。`npm run build` 始终保留原有 Cloudflare 发布配置。

逐件照片依据：使用方法和当前缺口见 `docs/PART_PHOTO_WORKFLOW.md`。
冷却母版已打包 9 张资料、索引 1,237 个已建模对象；其中仅 1 张是总成实物照，
不代表每个零件已有独立照片或精确尺寸。完整重建冷却模块前，用外部 Python 执行
`scripts/prepare-cooling-references.py` 生成原始目录 GIF 的兼容 PNG。
`blender-cooling.py` 自动附入资料；仅更新现有冷却母版的依据时，在 Blender 执行
`scripts/cooling_references.py`，它会保存、重新打开并检查机构数据没有变化。
