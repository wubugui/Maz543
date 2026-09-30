# MAZ‑543A 接手开始指南

**最新：[保守空间遮挡依赖实验](docs/OCCLUSION_TILE_REUSE_20260909.md) 已覆盖原始 Float32 变换和弹簧 morph 范围，静态/发动机/侧视开门/一挡/纵剖均取得 0 像素差；预算溢出保留全部原绘制。动态仅省 0–152 draws，12 帧平均工作约 1126 ms，仍约 0.6–0.8 FPS，默认关闭。下一步调查静态车体提供遮挡证明，避免内部运动件使证明失效。类型、构建及机械/导出/显示配置基线通过。完整 goal ACTIVE、16 项 OPEN。**

此前阶段：

**最新：[有序深度遮挡复用实验](docs/OCCLUSION_PREFIX_REUSE_20260909.md) 静态整帧 9305→3986 draws，发动机/开门/剖切均 0 像素差；但动态仅复用 0–1 次，仍约 0.8 FPS，保持默认关闭。最早变化的飞轮齿圈使几乎全部后续全前序证明失效；已避免每帧重复无效查询，下一步探索保守空间依赖。类型、构建及机械/导出/显示配置基线通过。完整 goal ACTIVE、16 项 OPEN。**

此前阶段：

**最新：[原生资源引用核查](docs/NATIVE_RESOURCE_RETENTION_20260909.md) 已确认完整装配仅多持有 30 份替换几何、约 1.42 MB，现已释放，不能解释数 GB 占用。当前整车 2691 独立几何、418.7 MB 底层缓冲、67 材质、10 贴图保留，完整侧视像素与绘制序列和前档相同；隐藏内构/共享缓冲/导出验证、类型及构建通过。普通预览 8868 实例、静止缓存、240 Hz/零积压正常，动态帧率仍慢。完整 goal ACTIVE、16 项 OPEN，继续主要显示负载和完整机械目标。**

此前阶段：

**最新：[文档退出资源清理](docs/VIEWPORT_DOCUMENT_LIFETIME_20260909.md) 已实际确认非 BFCache 的硬导航未执行 React cleanup，并在普通预览接入一次性 pagehide(false) 释放。主线程真实退出完成既有全部清理后，完整 8868 实例、静止缓存、240 Hz/零积压恢复；persisted=true 保留原状态。实验 Worker 硬导航已触发客户端清理，但没有取得完整释放回执。类型、构建和针对性生命周期测试通过，持续内存与动态帧率仍未解决。完整 goal ACTIVE、16 项 OPEN，继续保精度优化及完整机械目标。**

此前阶段：

**最新：[跨上下文固定源排序实验](docs/CONTEXT_DRAW_ORDER_20260909.md) 已记录完整绘制顺序，确认分配顺序随加载变化。受控固定源排序在侧视及右前门 99° 两组完整主线程/Worker 对照中，像素和绘制序列均相同；但与原排序仍有像素差，暂不默认启用。多次切换后进程私有占用约 5.6 GB，资源保留和动态性能仍待解决；全部模型/机械/质量保留，类型及构建通过。完整 goal ACTIVE、16 项 OPEN，继续显示优化和完整机械目标。**

此前阶段：

**最新：[解码器退出竞态](docs/OWNED_DRACO_LIFETIME_20260909.md) 已复现并修复延迟初始化/待解码/提交间隙的资源退出问题，实际普通预览恢复完整 8868 实例、静止缓存和 240 Hz 计算，类型与构建通过。此前巨大进程占用尚未全部归因。主线程/Worker 侧视及开门像素对照未通过，Worker、合批、分区阴影继续不默认启用；独立 Chrome 也为 Basic Render Driver，动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度显示优化及全部机械目标。**

此前阶段：

**最新：[静态/运动阴影分区实验](docs/PARTITIONED_SHADOW_EXPERIMENT_20260909.md) 已在完整发动机运行工况取得 0 像素差，1941 静态部件复用，381 运动部件更新；整帧 9305→7364 draws，仍约 0.6–0.7 FPS，暂不默认启用。额外影图估算 32 MiB，完整矩阵/变形及静态输入逐帧检查。此前原顺序合批也保持关闭。普通预览仍保留原完整阴影/静止帧缓存。goal ACTIVE、16 项 OPEN，继续显示性能和原车全部机械目标。**

此前阶段：

**最新：[原顺序合批实验](docs/ORDERED_BATCH_EXPERIMENT_20260909.md) 已修正显示材质克隆排序、批内原始排序与视锥输入，并在完整整车取得 0 像素差。最终 486 实例 / 30 批次，缓冲从约 393 MB 降至 104 MB，预热配对耗时收益很小，仍仅开发参数启用。普通预览保留定向阴影缓存，全部部件/机械/导出不变。完整 goal ACTIVE、16 项 OPEN，继续实际性能与完整机械工作。**

此前阶段：

**最新：[定向光跨帧阴影复用](docs/DIRECTIONAL_SHADOW_CACHE_20260909.md) 已接入普通预览，逐项精确比较阴影输入；静止与侧视对照 0 像素差，复用时少 2322 次绘制、约 540 万三角形，开门变化恢复重绘。12 帧顺序样本平均间隔改善约 4.8%，动态整车仍慢；WebGPU 适配器当前不可用。全部机械/导出/姿态保留。完整 goal ACTIVE、16 项 OPEN，继续保精度优化与机械实现。**

此前阶段：

**最新：[实际遮挡与透射绘制诊断](docs/OCCLUSION_AND_TRANSMISSION_PROFILE_20260909.md) 已核实玻璃透射预绘制与主颜色各处理 2315 次不透明绘制、约 539 万三角形，实际采样分别为 4 / 2。零样本记录不等于跨帧可隐藏；初次混合通道口径已更正。未启用遮挡剔除或缓冲复用，类型检查与构建通过，动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度优化和机械实现。**

此前阶段：

**最新：[独立显示清理与故障恢复](docs/WORKER_LIFECYCLE_20260909.md) 已修复初始化/运行异常的自有线程、画布、监听和请求清理，并通过浏览器内故障注入、同页完整重装和恢复后开门验证。全部 8868 实例、静止缓存、240 Hz 计算恢复，机械/导出/姿态源码未变。完整 Worker 仍为开发参数，动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度显示和机械实现。**

此前阶段：

**最新：[静止整车缓存与悬挂零位](docs/DISPLAY_NEUTRAL_CACHE_20260909.md) 已修正中性残力和透明双面材质版本造成的持续重绘。普通入口完整 8868 实例静止缓存有效，开门和悬挂激励可恢复绘制，240 Hz 求解保留。精确矩阵合批仍有 332 像素差，未默认启用；动态整车仍慢。完整 goal ACTIVE、16 项 OPEN，继续保精度优化及机械实现。**

此前阶段：

**最新：[完整逐帧计时与原生 Worker 动画帧](docs/FRAME_SCHEDULING_PROFILE_20260909.md) 已记录完整整车/运转传动的真实阶段耗时，并验证可选原生帧调度。传动样本帧间隔有所改善，整车仍慢；未降低几何、阴影、贴图或 240 Hz 求解。原生调度仍为开发参数，完整 Worker 默认发布门槛未通过。完整 goal ACTIVE，16 项 OPEN，继续实际绘制优化。**

此前阶段：

**最新：[显示资产精度与切线追踪](docs/DISPLAY_ASSET_PRECISION_20260909.md) 已核实旧 Draco 量化造成细面/切线损失；实际整车导出保护性修正 616 个切线，82 个真实表面问题仍未通过。两件原生对象的零量化压缩保持全部三角形角点属性逐位相同，尚未替换运行时资产。整车仍约 0.5 FPS；完整 goal ACTIVE，16 项 OPEN，继续保精度显示优化和机械实现。**

此前阶段：

**最新：[完整显示工作线程与无损封装](docs/RENDER_WORKER_20260909.md) 已在开发入口装配完整模型并直连 240 Hz 机械计算，界面不再依赖绘制线程返回仪表；350 MB 整车 Blob 导出的全部二进制载荷与原封装一致。整车仍约 0.3–0.7 FPS，完整校验发现 698 个切线错误尚待追踪，独立显示未默认启用。完整 goal ACTIVE，16 项 OPEN，继续保精度优化。**

此前阶段：

**最新：[独立机械调度](docs/SIMULATION_DISPLAY_SCHEDULING_20260909.md) 已把原求解器放入固定 240 Hz Worker，保留内部悬架 480 Hz 与所有几何，显示迟滞不再丢弃机械时间；延迟一致性、真实 Worker 阻塞试验和网页启动/停机观察通过有限检查。GPU 绘制仍慢，整车性能与物理精度未验收。完整 goal ACTIVE，16 项 OPEN，继续保精度优化。**

此前阶段：

**最新：[CAD 显示优化](docs/PERFORMANCE_CAD_DISPLAY_20260908.md) 已启用每帧单次阴影、严格显示缓存、按时间相机缓动及原生资源释放。静态机构检查恢复响应；整车仍由 Basic Render Driver 软件渲染，性能未解决。合批仅保留开发实验，因画面差异/内存和热身收益不足未默认启用。完整 goal ACTIVE，16 项 OPEN，优先继续保精度性能工作。**

此前阶段：

**最新：[四工作轮变矩器总成](docs/CONVERTER_FOUR_WHEEL_ASSEMBLY_20260908.md) 已保存并导出 180 个实体的泵轮、涡轮、双导轮总成，应用新增 /converter，装配拆看与导出核对通过。叶型/尺寸仍为拟合，液力和闭锁动力学未完成。整车现场报告 Basic Render Driver、约 2698 万三角形及 0 FPS，必须继续核查性能。完整 goal active，16 项 OPEN。**

此前阶段：

**最新：[全表面接触与积分误差](docs/CONVERTER_STRIP_SURFACE_CONTACT_20260908.md) 已新增全带面/滚柱接触，38 个静态形态原生保存及实体读回检查通过；最大计算应力约 9.36 GPa，真实弹性范围未通过。10 N·m 连续诊断到 1.187 秒后失败，时间积分能量误差待解决。完整 goal active，16 项 OPEN。**

此前阶段：

**最新：[弯带与外圈接触及连续受力](docs/CONVERTER_STRIP_POCKET_CONTACT_20260908.md) 已修复扩大压缩范围中约 16.4 μm 的带材穿透，补足楔面反力与根部载荷；39 点原生检查及 352 段接触求解通过有限验证。连续外载试验已开始，10 N·m 场景进入未核查范围后中止，尚未发布动态结果。完整 goal active，16 项 OPEN。**

此前阶段：

**最新：[图件纠错与弯带弹簧研究](docs/CONVERTER_STRIP_SOURCE_CORRECTION_20260908.md) 撤回旧圆线螺旋弹簧的原车结构假设。新弯带已有 26 个独立平衡、原生实体读回与网页逐点比对；应用新增 `/strip-spring` 可查看变形。固定座、材料、强度、连续受力与整车联动仍未通过，完整 goal active，16 项 OPEN。**

此前记录（旧圆线台架仅保留内部一致性证据，不能作为原车弹簧验收）：

**最新：[单向离合器连续台架](docs/CONVERTER_CONTINUOUS_BENCH_20260908.md) 已保存 201 组联动姿态，弹簧实体与受力一致性、600 个帧间检查和网页顶点比对通过；应用新增可操作回放入口。双导轮流体与整车联动未完成，完整 goal active，16 项 OPEN。**


**最新：[单向离合器连续接触](docs/CONVERTER_CONTACT_20260908.md) 已实现滚柱/内圈/楔面与弹簧受力的独立求解，负扭矩自然保持、正向越程；三种步频与 400 个实际网格姿态回放检查通过。连续弹簧网格、保存的动态原生文件、双导轮流体及网页整合尚待完成。完整 goal active，16 项 OPEN。**


**最新：[变矩器双单向离合器](docs/CONVERTER_FREEWHEELS_20260908.md) 已建独立 Blender 组件，共用内圈、两套楔形外圈、滚柱和弹簧；68 个封闭实体、72 个端点检查及渲染已完成。当前仅离散几何检查，未安装到整车/网页，连续滚动、楔紧受力及双导轮流体驱动仍待实现。完整 goal active，16 项 OPEN。**


**最新：[带载起步诊断](docs/TRANSMISSION_LOADED_LAUNCH_20260908.md) 已运行 12 组质量/分动挡/挡位场景及 240/480/960 Hz 步长检查。40.6 t 倒挡起步约 3.04–3.62 秒，接合加速度尖峰在细步长仍存在；固定转速台架不代表原车通过。当前运行质量仍 20.55 t，543A 型号质量、变矩器、惯量与阀体须联合核对。完整 goal active，16 项 OPEN。**


**最新：[接合计时定义](docs/TRANSMISSION_TIMING_DEFINITION_20260908.md) 已对照 1973/1977 原文核实。带载起步 ≤3 秒与压力完全建立 2–3 秒是不同指标；当前一挡/倒挡第 3 秒仅达主路的 16.7%，95% 诊断约 4.17 秒，仍 OPEN。保留原参数，继续核对弹簧及阀体尺寸。完整 goal active，16 项 OPEN。**


**最新：[回位弹簧与推杆](docs/TRANSMISSION_SPRING_COUNTS_20260908.md) 已按 30 / 16 / 16 / 30 修正并同步，1,755 节点；大离合器双推杆、导套、销及穿孔已补，正式几何、台架和网页接合/回位检查通过。拟合大组应力约 2.09 GPa、95% 压力约 4.17 秒，原厂线径/自由长度/预压与计时定义仍须核实，不可调参掩盖。总 goal active，16 项 OPEN。**

此前记录（冲突时以最新记录为准）：

**最新：[摩擦面油槽](docs/TRANSMISSION_GROOVES_20260908.md) 已建并同步原生与网页，23 片、双面实体槽及实际接触半径检查通过。网页新增单片/油槽近看，显示效果仍有不足。下一步必须校正当前每组 8 根的回位弹簧：目录要求 30 / 16 / 16 / 30，并联合修正推杆、导套、旋转套槽、供油避让和总刚度，禁止暗调参数保留旧性能。总 goal active，16 项 OPEN。**

此前记录（冲突时以最新记录为准）：

**最新：[共用离合器零件](docs/TRANSMISSION_COMMON_PARTS_20260908.md) 已统一并同步原生/网页，68 个实例、6 个目录件号组的实际几何一致。下一步补原文要求的螺旋/径向排油沟槽与接触检查；两组大离合器约 3.025 秒压力建立仍未通过严格上限。总 goal active，16 项 OPEN。**

此前记录（冲突时以最新记录为准）：

**最新：[三挡宽环形活塞与接触收敛](docs/TRANSMISSION_DIRECT_AREA_20260908.md) 已同步网页和原生，三挡在相同拟合负载场景中不再持续打滑。下一步核对一挡/倒挡的共同零件和小盘组共用关系；原厂尺寸及全部 16 项仍 OPEN，完整 goal active。**

此前记录（状态冲突时以最新记录为准）：

**最新：[液压与传动受力联动](docs/TRANSMISSION_HYDRAULICS_20260908.md) 已接入网页并通过原生台架读回。压力求解驱动活塞、摩擦容量和实际转速；三挡持续打滑仍未通过，下一步联合核对受压型面和负载模型。全部 16 项 OPEN，完整 goal active。**

Earlier stage record (superseded where noted):

**最新：[三挡旋转供油与支承轴承](docs/TRANSMISSION_ROTARY_FEED_20260908.md) 已验证并同步，795 节点。四组工作腔为重建几何，继续按原文建立供油控制、压力、活塞和摩擦扭矩关系；原厂尺寸与整车 16 项验收仍 OPEN，完整 goal 保持 active。**

Earlier stage records (chronological progress, superseded where noted):

**最新：[中间壳体与 2/R 工作腔](docs/TRANSMISSION_CASE47_20260908.md) 已建并同步，
736 节点。继续三挡旋转壳体 46、固定支承 50 和供油密封；四组换挡动力学未完成。**

**最新：[一挡后盖工作腔](docs/TRANSMISSION_FIRST_BOOSTER_20260908.md) 已重建，
动/静密封和贯通进油孔已检查并同步原生与网页。其余三组工作腔、真实供油和
压力/扭矩求解仍 OPEN，完整 goal 保持 active。**

**最新：[盘片滑动齿槽](docs/TRANSMISSION_SPLINES_20260908.md) 已同步原生和网页。
继续按原图修正液压腔及一动一静的密封圈，再推进换挡受力。完整 goal 仍 active。**

**最新先读 [摩擦片接触记录](docs/TRANSMISSION_CONTACT_20260908.md)：四组盘片压紧、
圆钢丝弹簧变形和有限状态装配检查已落实，网页及两份整车已同步；液压、花键、
摩擦扭矩及整车完整验收仍 OPEN。以下较早阶段记录按时间保留。**

**先读最新 [两排行星机构记录](docs/PLANETARY_CORE_20260908.md)：浏览器与两份
整车原生已替换旧三组齿轮，尚需完整装配/接触审计与换挡动力学。原始 goal 仍 active。**

**最新传动增量：倒挡速比、高低挡、转速检查、动力暂停/慢动作已修正并验证。
原车传动外观和图 42 剖面已缓存并查看。下一步重建两排行星机构，详见
[传动续做记录](docs/TRANSMISSION_REFERENCE_NOTES.md)。完整 goal 保持 active，16 项仍 OPEN。**

**最新续做：原始完整 goal 已在本任务设为 active。已修复弹簧压缩时钢丝被压扁
的问题，并加入完整弹簧检查视图，详见 [2026-09-08 续做记录](docs/CONTINUATION_20260908.md)。
整车 16 项仍 OPEN，万向轴安装冲突仍未修复。旧 `clutch-contact-20260908` 已由
`spring-round-wire-20260908` 取代。下面的记录保留此前增量的历史状态。**

**2026-09-08 当前状态：已恢复到 `E:/Maz543/testcar`，并完成本轮冷却
native/web 同步。先读 [本机恢复与续做记录](docs/RESTORE_20260908.md)。
下文为 2026-09-06 迁移时指南，其中“未运行验证 / 旧 GLB / 旧参考计数”
已由新记录中的实测结果更新。下一项是万向轴原装安装关系，16 项整车验收仍 OPEN。**

更新于 2026-09-06。先读本文件，再修改模型。

本指南在迁移主快照之后补充。**备份已经完成并通过校验，模型仍未完成。** 旧交接文件里“计划打包、等待校验”的措辞属于历史状态。本轮只编写交接文档，没有重新建模、导出或执行尚未完成的模型验证。

## 1. 你要继续完成什么

用户要一个可在浏览器操作的 MAZ‑543 机械产品演示。当前项目采用 MAZ‑543A 双驾驶室作为参考，要求 Blender 专业精细建模、准确外形、完整内构、逐部件机械联动，以及真实的材质、光照和细节。每个部件应尽可能寻找原车照片、手册和零件目录，以资料确定几何和装配关系。

用户明确不接受卡通、简单形状拼接、互不关联的转动、只有外壳和假装完成。`docs/ACCEPTANCE.md` 的 **16 项整车门槛全部 OPEN**。局部网格、动画或构建通过不能代表整车完成。原目标因迁移暂停，未被标记完成。

## 2. 先读这几份文件

1. 本指南：接手顺序与第一项工作。
2. `MIGRATION_HANDOFF.md`：完整目标原文、模块进度、最后修改和未完成事项。
3. `docs/ACCEPTANCE.md`：整车验收标准；带旧日期的发现须与最新文件核对。
4. `docs/PART_PHOTO_WORKFLOW.md`、`docs/COOLING_REFERENCE_NOTES.md`、`docs/CAB_PHOTO_FIT_NOTES.md`、`docs/CARDAN_REFERENCE_NOTES.md`：近期资料与几何问题。
5. 对应源码、Blender 脚本和 `outputs/` 报告，核对真实输入、输出、时间和结果。

需要历史原因或用户原话时，再定向搜索解压后的 `conversation/raw/` JSONL 和可读 Markdown。`conversation/latest-deltas/` 是主快照之后的补档，索引有字节偏移和合并 SHA-256。不要一次读入数百 MB 原始记录，也不要只依赖摘要。

原线程：`01a06f8d-9cc1-7f81-a2a0-70ff399252b9`。原始记录用于查证和续做；没有承诺新电脑会自动恢复同一个侧栏任务或账号登录。

## 3. 恢复与第一次启动

搬运目录为 `MIGRATION_20260906/COPY_THIS_FOLDER`。三份分卷合计约 4.77 GB，`MERGE.cmd` 会逐卷校验、合并并验证整包。主包校验覆盖 263,947 个源文件，包括隐藏文件、未提交内容、`.git`、`node_modules`、`outputs`、`work`、Blender、外部参考和工具环境。

若本指南来自搬运目录：先合并并完整解压主 ZIP，再将 `AGENT_GUIDE_UPDATE.zip` 解压到同一个父目录。补充包只更新 `testcar/AGENT_START_HERE.md` 与 `testcar/NEXT_AGENT_PROMPT.md`；也可手动复制旁边这两份文件。

```text
恢复目录/
  testcar/       项目根目录；开发命令从这里执行
  external/      参考照片与外部运行环境
  conversation/  原始对话、补档、目标与任务元数据
  migration/     主快照的恢复及启动说明
```

先读 `migration/READ_ME_FIRST.md`。查看现有网页可直接双击 `migration/START_LOCAL.cmd`，打开 `http://localhost:3000/`，无需先全量重建 Blender 资产。

手动启动示例：在上图中的 `testcar` 目录打开 Windows PowerShell。

```powershell
$mazProject = (Get-Location).Path
$mazBundle = Split-Path $mazProject -Parent
$mazNodeDir = Join-Path $mazBundle 'external/nodejs'
$mazPython = Join-Path $mazBundle 'external/codex-dependencies/python/python.exe'
$mazBlender = Join-Path $mazProject 'work/tools/blender-4.5.13-windows-x64/blender.exe'
$env:PATH = "$mazNodeDir;$env:PATH"
node --version
& $mazPython --version
& $mazBlender --version
$env:MAZ_NODE_PREVIEW = '1'
$env:NODE_USE_ENV_PROXY = '0'
npm run dev -- --host 127.0.0.1 --port 3000
```

Node 要求 22.13+；随包环境针对 Windows x64。移动过目录就调整变量。Node 预览开关用于绕过旧电脑的 workerd 故障，不代表云端 Worker/D1/R2 已验收。

重建前处理旧绝对路径：部分脚本和 Blender 图片外链使用 `D:/maz543-references`。按恢复说明放回该位置，或系统地重定向并核对。完整依赖审计在 `MIGRATION_DEPENDENCY_AUDIT.md`。普通几何预处理使用随包 Python 3.12，`work/pythonlibs` 的 Shapely 为 cp312；凡 `import bpy` 的入口都必须由 Blender 执行。

首次运行先记录整车前方、侧面、冷却离合器的实际画面、错误和性能。旧截图、旧日志、旧 FPS 均不代表新机器实测。

## 4. 必须先处理的版本差异

| 项目 | 此次接手文档核对时的状态 |
|---|---|
| 冷却原生母版 | 新弹簧和四个支座已保存；parts register 为 1,241 件 |
| 五份 rebake | Starting、Cooling、Cardan、Master、Textured 均已保存，日志以 `Blender quit` 结束 |
| 冷却参考索引 | 仍是旧 1,237 件；需要刷新 |
| 浏览器冷却 GLB | 仍是旧几何，14,224,176 字节，缓存参数 `interface-4` |
| 冷却求解器 | TS 已加入轴向运动、接触、摩擦和释放；网页当前用新姿态驱动旧网格 |
| 原生接触验证 | 脚本已写但未运行；`outputs/clutch-native-contact-verification.json` 不存在 |
| 原生/安装验证报告 | 早于最终弹簧修改，不能作为这轮通过证据 |
| 构建 | 之前通过的记录早于最终弹簧常数与姿态修改，需要验证当前版本 |

若新目录已有后续修改，以实际源码、资产和报告为准；先理解差异，保留已有工作。

## 5. 第一轮：收尾冷却离合器，验证 native/web 一致

先检查 `git status --short`。很多关键资产被 Git 忽略，修改前另存本轮涉及的母版。不要 reset/clean，也不要无条件全量重建，覆盖已完成的驾驶室、材质和机构修复。

以下命令逐条执行并检查退出码，失败时先处理原因，再推进依赖步骤。

**A. 先验证已有最新几何。**

```powershell
& $mazBlender -b --python-exit-code 1 --python scripts/verify-clutch-contact-native.py
```

此脚本只在内存中修改风扇/弹簧姿态，不保存母版；写 `outputs/clutch-native-contact-verification.json`。检查左右各五个位移下的真实摩擦/磁隙和指定障碍物穿插。失败就修实际几何或坐标关系，不要扩大容差掩盖问题。它不覆盖完整离合器或整车碰撞。

**B. 修改求解器后，先生成当前缓存和姿态。**

```powershell
node scripts/prepare-starting.mjs
node scripts/prepare-cardan.mjs
```

前者编译 TS 并生成 601 帧 cooling/starting/engine 姿态；后者依赖前者产物。`verify-cooling.mjs` **只读 `work/compiled/cooling.mjs`，不会重新编译 TS**。不能用旧缓存的通过结果证明新代码正确。未修改求解器时，先核对已有产物，不必无目的重写。

**C. 几何验证通过后，更新资料、导出和原生装配。以下步骤会写入文件。**

```powershell
& $mazBlender -b --python-exit-code 1 --python scripts/cooling_references.py
& $mazBlender -b --python-exit-code 1 --python scripts/export-cooling-native.py
& $mazBlender -b --python-exit-code 1 --python scripts/rebake-powertrain.py -- --refresh-cooling
```

- 参考脚本保存 Cooling 母版并更新 reference JSON。应核对真实对象数量，不能只修改报告数字。
- 导出脚本三角化上下传动箱的大于四边形面，先保存母版，再在内存合批并覆盖 GLB。保留 `blender-cooling.py` 的 `# Batch only` 导出入口约定。GLB 不带动画，浏览器通过语义节点实时驱动。
- rebake 会覆盖五份母版的相关动画，并替换两份整车母版中的旧 Cooling 总成；它不导出 GLB。先确认姿态输入正确，并保留其他已完成修改。
- “附加参考前后机制摘要不变”只证明那一次操作。后续三角化/重烘焙会改变摘要，最终状态需要新的证据；按实际修改同步参考元数据及两份整车母版。

**D. 对最终保存的资产检查，再做实际浏览器验收。**

```powershell
& $mazBlender -b --python-exit-code 1 --python scripts/verify-clutch-contact-native.py
& $mazBlender -b --python-exit-code 1 --python scripts/verify-cooling-native.py -- --no-render
& $mazBlender -b --python-exit-code 1 --python scripts/verify-cooling-install.py
node scripts/verify-cooling.mjs
npx tsc --noEmit
npm run build
```

修改 `components/vehicle-viewer.tsx` 中的冷却 GLB 缓存版本，避免继续取 `interface-4`。native 校验覆盖选定姿态、计数和风叶–护罩样本；installed 校验覆盖局部姿态/安装点对齐，**不等于整车碰撞或机械闭合验收**。遗漏 `--no-render` 会额外执行 Cycles 渲染。

实际浏览器检查合壳/开壳、左关右开、暂停/慢动作、弹簧压缩与释放、摩擦接触、断电滑行及整车安装。0.6→2.1 mm 磁隙是当前拟合目标，不是已标定原车尺寸。留下新截图、操作步骤、观测和性能。通过后只关闭这轮增量，再按完整证据推进整车门槛。

## 6. 随后的明确缺陷与资料纪律

优先研究真实冷却万向轴安装关系。`outputs/cardan-installation-audit.json` 测得当前整车约 270.36057 mm 十字轴距、有向角 101.45383° / 144.63093°，不在当前独立机构已验证的 230–270 mm、0–30° 范围。独立 Cardan 能演示不等于已经安装闭合；不要随意挪动齿轮箱/风扇或放宽通过范围。数字描述当前重建模型，不是原厂允许值。

随后回到 16 项验收，按准确原装设备清单补全传动、转向、制动、电路、油路/气路等。不能根据网页已有按钮反推系统已完整实现。

每个部件记录对象名、来源 URL/本地文件、版本、可见特征、尺寸依据、不可见结构、拟合参数和验证方法。区分原车照片、同系列照片、目录剖面与推测；新资料应实际打开查看。冷却参考中的“49”是同一张装配照片的引用次数，不是 49 张照片；当前独立精确部件照片接受数为 0。约 0.02833 秒吸合时间、约 4,049.6 N 接触力等是未标定模型结果，不是 MAZ 实测性能。缺资料就保留缺口，合成图不能代替原始证据。

## 7. 代码入口与第一轮交付

| 入口 | 作用 |
|---|---|
| `components/workshop.tsx` | 控制界面、操作参数与状态展示 |
| `lib/mechanics.ts` | 主仿真推进与模块协调，追踪实际 `advance` 路径 |
| `lib/starting.ts`、`lib/cooling.ts` | 启动、转速相关状态、冷却接触、热网络及姿态 |
| `lib/d12.ts`、`lib/d12-timing.ts` | 发动机与正时运动 |
| `lib/suspension.ts`、`lib/cardan.ts` | 悬架与独立万向轴约束/姿态 |
| `components/vehicle-viewer.tsx` | 六个 GLB 加载、语义节点绑定、可见性、镜头与渲染 |
| `scripts/prepare-*.mjs` | 生成 Blender 使用的姿态与缓存 |
| `scripts/*.py`、`outputs/*.blend` | 原生几何、层级、材质、参考和动画 |
| `public/models/` | 浏览器实际使用的资产；只保存 `.blend` 不代表网页已同步 |

注意米/毫米、局部/世界坐标和 Blender/Three.js 轴转换；核对脚本实际转换，不能把同名轴直接当成同一坐标。

第一轮结束应留下：明确的问题与修复说明、可编辑母版、匹配网页资产、最新来源与验证报告、实际浏览器截图，以及尚未完成的内容。第一次接手回复先说明恢复状态与版本差异，然后推进第一项验证。用户已明确要求的常规建模和修复按任务继续，不必把每个可逆步骤都变成重复确认。不要从零重新生成一个简化 MAZ，也不要把备份完成当作模型完成。
