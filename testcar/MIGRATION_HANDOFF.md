# MAZ‑543A 项目迁移与继续工作交接

记录日期：2026-09-06，Asia/Hong_Kong。原目录 `D:\testcar`。本文件记录迁移前的工作状态；迁移包是否完整、校验是否通过，以迁移目录内最终生成的清单和验证报告为准。

## 现在优先做什么

用户的电脑故障，当前优先任务是把项目、目标、进度、所有可取得的本任务对话、原生 Blender 文件、参考资料及依赖打包，方便整体拷到新电脑。建模已暂停。计划迁移包为 `MIGRATION_20260906/MAZ543_COMPLETE_20260906.zip`，内部为 `testcar/`、`external/`、`conversation/`、`migration/`。不要只复制 Git 已跟踪文件；大量母版、贴图、参考图片、工具和验证结果在被忽略的 `outputs/`、`work/` 等目录。

原建模目标尚未完成，目标工具在迁移前显示 paused。线程 ID 为 `01a06f8d-9cc1-7f81-a2a0-70ff399252b9`。迁移完成不等于建模目标完成。

## 用户要求与原始目标

用户要可在浏览器直接操作的 MAZ‑543 三维产品演示，要求准确外形、完整内构、每个部件按机械关系工作；明确要求使用 Blender 进行专业精细建模，并为各部件在网上寻找照片和资料作依据。用户反复否定卡通、简单形状拼接和仅外观展示，要求真实、准确、次世代写实。

项目目前选定量产 MAZ‑543A 双驾驶室作为外形参考版本。照片、目录和同系列发动机资料存在版本差异，不能混用后声称原车精确尺寸。轮胎参考 VI‑203 产品规格，不意味着某辆早期车的原装轮胎已被确认。

目标工具保存的用户目标原文：

> 精确外形核对、完整内构、每个部件的机械运行、浏览器最终写实效果验证  ，给完成为止！还有你车上啥东西都没有动画，车门不能开，发动机没有内构，不能真正的启动，悬挂也没有物理机械东海，还有很多其他的该有的动画都没有，你现在在座的其实就是一个虚拟的maz543产品演示，必须精确的反应产品属性，让我在这个app内直接就能看到这个车的所有功能，和机械内构和联动，所有的结构必须要机械仿真！！！！你必须十分的具体和精确，否则就不具有产品演示和属性！

最近关于质量的原话还包括：“把表现优化到完美写实啊，你现在这个太卡通了，各种都不写实！你最好去找照片照资料给我往死里参考！我要求要准确，真实！次时代！”、“请你使用blender进行专业建模，而不是随便拉两个简单形状！”、“对于每一个部件，你最好是在网上去找他的图片，然后再blender中进行精确的建模，越细节越好！”

## 验收现状：16 项全部 OPEN

正式清单在 `docs/ACCEPTANCE.md`。外形标定、双驾驶室内构、完整发动机、完整启动/停机、燃油进排气、润滑冷却、变速传动、八个驱动轮端、转向、物理悬挂、制动、电气驾驶室功能、其他底盘设备、浏览器全部功能、写实渲染性能、完整原生交付这 16 项都没有整体验收通过。

已完成的局部工作有真实可编辑 Blender 网格和验证，不能因此宣布整车完成。齿轮转动、几何闭合、无穿插、glTF 验证、TypeScript/构建通过各自仅证明对应范围。拟合尺寸、模拟力学参数、理想滚动关系都不是原厂测量或真实负载试验结果。整车此前在 RTX 4070 Super 上约 16–23 FPS，独立检查视图约 60 FPS；这些是此前浏览器观察，尚未通过最终性能或写实验收。

## 主要交付物与已经具备的局部功能

| 位置 | 内容与状态 |
|---|---|
| `outputs/MAZ543A_Master.blend` | 可编辑整车母版，外形修改器、参考图、各详细模块及局部机构动画 |
| `outputs/MAZ543A_Textured.blend` | 整车 PBR 与导出母版，具有烘焙动画；导出需要的三角化与作者母版拓扑有差别 |
| `outputs/D12A525A_Engine_Master.blend` | 详细 D12 发动机；当前 2,046 个登记件、169 个姿态绑定。48 个气门、四根凸轮轴、主副连杆、正时齿轮及循环水泵已有局部几何验证 |
| `outputs/MAZ543A_Suspension_Master.blend` | 1,716 个登记件、16 根扭杆、80 个姿态绑定；四连杆、双扭杆、减振器和竖向接地力求解已做局部验证，安装硬点和力学参数未标定 |
| `outputs/MAZ543A_Starting_Master.blend` | C5/MZN 167 个登记件、7 个运动变换、8 张打包参考。电流、预润滑压力、惯量、啮合和调速采用未标定的集总模型；气启动和完整电机/油路仍缺失 |
| `outputs/MAZ543A_Cooling_Master.blend` | 双风扇、离合器、上下传动箱；最新弹簧修改后 1,241 个网格/曲线对象、254 个姿态绑定。新几何尚未导出到浏览器 |
| `outputs/MAZ543A_Cardan_Master.blend` | 独立万向轴：213 个网格、190 个姿态绑定，叉、十字轴、滚针、密封及花键。尚未装入整车形成闭合传动链 |
| `docs/`、`outputs/*register*.json` | 来源、尺寸状态、验收边界及逐件登记。注意部分计数是历史增量，不能直接当作当前最终数量 |
| `work/reference-docs/` | 已下载资料、照片、目录图及处理文件；网页文本或拦截页不能冒充完整手册或实物图片 |

浏览器可分别打开四扇门，查看发动机内构，使用引导/手动电启动，检查悬架台架、冷却系统、上下齿轮箱、独立万向轴，暂停/慢放/移开局部外壳。变速传动、制动、转向液压、电路等仍有大量简化或缺项。

六个当前浏览器 GLB（2026-09-06 迁移准备时读到的文件大小）：

| 文件 | 字节数 |
|---|---:|
| `public/models/maz543a-blender.glb` | 20,332,232 |
| `public/models/d12a525a-engine.glb` | 9,996,432 |
| `public/models/maz543a-suspension.glb` | 8,154,920 |
| `public/models/maz543a-starting.glb` | 792,512 |
| `public/models/maz543a-cooling.glb` | 14,224,176 |
| `public/models/maz543a-cardan.glb` | 907,380 |

这些大小是快照定位信息，不是文件哈希。迁移完整性请看迁移包的清单和 SHA‑256 验证结果。

## 最新未收尾增量：冷却离合器接触与回位弹簧

这部分必须首先收尾，不能将当前浏览器当成最新 Blender 几何的预览。

1. `lib/cooling.ts` 已加入轴向位移/速度、磁力、法向接触力、磁隙、滑差功率等状态。通电后先建立电流和轴向运动，摩擦面真正接触后才施加干摩擦扭矩；开路时保留很小的轴承阻力。回位采用弹簧/阻尼和单向行程止挡。`components/workshop.tsx` 已显示电流、位移、磁隙及接触状态。
2. 当前数值参数包括 1.5 mm 行程、2.1 mm 释放磁隙、0.6 mm 吸合磁隙、6 kg 等效轴向质量、20 的阻尼；弹簧使用线径 1.4 mm、平均直径 49 mm、5 圈、10 mm 模型自由段及拟合预压。尺寸、钢材模量、磁力规律、质量、阻尼均未经原车实测标定。不得将 0.02833 秒吸合时间或约 4,049.6 N 接触力宣传为 MAZ 数据。
3. `scripts/cooling-clutch-spring.py` 已在冷却母版替换左右压缩弹簧，并新增四个环形支座。`work/clutch-spring-update.log` 明确记录 `CLUTCH_COMPRESSION_SPRINGS 1241` 和正常退出。弹簧沿 X 的仿射缩放仍会改变线材截面，是近似，不是完整弹性体仿真。
4. `scripts/blender-cooling.py` 已集成上述弹簧修复，未来完整重建会执行。不要为了导出而重新运行整个重建链，避免覆盖已修复的外形/材质/机构。
5. `scripts/rebake-powertrain.py -- --refresh-cooling` 已运行结束。`work/rebake-powertrain.log` 中 Starting、Cooling、Cardan、整车 Master 和 Textured 五份文件全部有保存记录，最后为 `Blender quit`。它更新共享姿态，并把新冷却模块附入两份整车母版；没有生成新的浏览器冷却 GLB。
6. `scripts/verify-cooling.mjs` 已通过当前接触模型的数值检查。`outputs/clutch-contact-verification.json` 记录接触前 33 个采样无干摩擦扭矩、吸合磁隙 0.6 mm、释放 2.1 mm。这不是整套电磁/机械/热学能量验收。
7. **`scripts/verify-clutch-contact-native.py` 已写但尚未运行。** 迁移准备时 `outputs/clutch-native-contact-verification.json` 不存在。该脚本计划检查左右两侧五个位移下的真实摩擦/磁隙及弹簧与输出轴、磁体、两处滚针外圈的 BVH 穿插，不覆盖完整离合器或整车碰撞。
8. **浏览器冷却 GLB 仍为旧几何，缓存参数仍为 `interface-4`。** TypeScript 新姿态会驱动旧弹簧网格；这属于待修复的 native/web 不一致。冷却参考索引仍是旧 1,237 件状态，尚需重新附入资料/更新清单。最后一次整站构建通过发生在最终弹簧常数和姿态修改之前，不可声称最新整体已构建验证。

原手册还要求夏季/电气故障时的机械锁定和相应刷架、电线处理。该机构与维护流程尚未实现；锁定螺栓准确数量、位置及尺寸尚未核实，不要编造。

## 另一个明确缺陷：安装万向轴不闭合

`scripts/audit-cardan-installation.py` 已从实际整车母版检查接口，报告为 `outputs/cardan-installation-audit.json`，状态 OPEN；另有 `outputs/MAZ543A_Cooling_Installation_Audit.blend` 和 `outputs/cardan-installation-audit.png`。

两侧现有十字轴中心距约 270.36057 mm；按代码定义的有向关节角为 101.45383°、144.63093°。独立检查机构已验证范围仅 230–270 mm、0–30°，所以当前安装不能由该已验证机构直接连接。这里的角度不是无向轴线夹角，也不是原厂允许角度。不得通过任意移动齿轮箱/风扇或扩大“通过范围”制造合格结果，应继续找原装安装照片和尺寸确定真实轴向及位置。

此审计脚本最后加了标题和视口隐藏设置，但最后一次对应渲染未确认完成；现有输出可能还是前一版，没有最新标题。原计划向 README/ACCEPTANCE/Cardan 说明追加审计结论的补丁未应用，本交接文件补存该事实。

驾驶室中央下方开口已按照片拟合放宽到约 1.49 m（此前约 1.11 m），前格栅加宽。当前第 0 帧风扇罩与内壁的交叉已修复；完整运动全程、隐藏深度和装配标定仍未通过。部分旧文档还写着“每侧 32 组穿插”，应阅读日期更晚的 `docs/CAB_PHOTO_FIT_NOTES.md`，不能把旧缺陷描述当成当前检查结果。

## 照片与资料证据边界

`docs/PART_PHOTO_WORKFLOW.md` 说明逐件索引规则。冷却母版此前打包 9 张资料，其中只有 1 张总成实物照片；49 个对象引用该照片的可见特征，绝不代表 49 张照片。已接受的独立精确部件照片数为 0。Cardan 有 4 张打包参考图，213 个网格逐件索引。新增四个弹簧支座还需更新参考登记。

关键资料：

- MAZ 1977 技术说明：<https://djvu.online/file/zjMdLY3MFjmTL>。已查网页文本，不能说本地保存了整本扫描手册。
- MAZ 1973 冷却章节：<https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm>。
- D12 家族手册：<https://neva-diesel.com/f/rukovodstvo_d12.pdf>，本地 `work/reference-docs/D12-manual.pdf` 为 235 页扫描；与 MAZ D12A‑525A 的具体版本差异仍需核对。
- 最近看过的本地图包括 `MAZ1973-0575.jpg`、`MAZ1973-0582.jpg`、`543-fan-install.png`、`543-upper-exploded.png`、`543-1308509-lower-photo.png`。
- `work/reference-docs/MAZ1973-0588-response.html` 是约 246 字节的站点响应/拦截内容，不是有效参考图片。

## 新电脑恢复

先阅读迁移包 `migration/` 下的恢复说明、源路径映射和验证报告，确认解压文件校验一致，再启动项目。可把 `testcar/` 恢复到 `D:\testcar`，也可放其他位置，但必须处理绝对路径。`external/` 下的原始参考目录和外部运行时按迁移清单恢复。对话在 `conversation/` 内；它保存用于继续工作的历史证据，不表示新安装的 Codex 会自动恢复原线程 UI、登录或正在运行的进程。

项目内已有 Blender 4.5.13 LTS：`work/tools/blender-4.5.13-windows-x64/blender.exe`。旧外部路径包括 `D:/maz543-references`、`C:/Users/wubugui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`、同运行时下的 Poppler，以及 `C:/Program Files/nodejs`。不要把旧用户名路径误认为新机器必然存在。Shapely 的 cp312 库在项目 `work/pythonlibs`，应由相匹配的外部 Python 使用，不能直接塞进不匹配的 Blender Python ABI。

建议启动（在恢复后的项目目录，用已恢复的 Node 22.13+）：

```powershell
$env:MAZ_NODE_PREVIEW = '1'
$env:NODE_USE_ENV_PROXY = '0'
npm run dev -- --host 0.0.0.0
```

浏览器访问终端实际报告的地址，通常为 `http://localhost:3000/`。Node 预览模式绕过此前本机 workerd 连接故障；它不能验收 Worker/D1/R2 等行为。首次可使用迁移的 Windows `node_modules`；如果新机器平台/版本不兼容，再根据 `package-lock.json` 安装依赖。不要在仅需浏览已有模型时先重建所有 Blender 资产。已有 `dist/` 也不是最新修改的验收证明。

## 新机器继续建模的具体顺序

1. 读取本文件、`NEXT_AGENT_PROMPT.md`、原始目标与对话，确认迁移校验完成。检查 Git 工作区保留了所有未提交/未跟踪文件，不要 reset 或清理 `outputs/`、`work/`。
2. 先运行已有 `scripts/verify-clutch-contact-native.py`；若发现穿插或错误间隙，修复实际几何并重复对应验证。原生检查没有通过前不要直接宣布新离合器完成。
3. 用 `scripts/export-cooling-native.py` 导出当前冷却母版；这个脚本会三角化上下传动箱的多边形并保存母版，再批处理静态部分导出。核对网格层级、枢轴和 254 个姿态绑定。
4. 用 `scripts/cooling_references.py` 更新逐件资料，确认新的对象数并保留机构数据；将资料变化同步到整车工程。更新 `components/vehicle-viewer.tsx` 的冷却 GLB 缓存参数，消除旧 `interface-4` 缓存。根据改变范围重新附入/检查两份整车母版，保留正确驾驶室和材质。
5. 运行相应 `verify-cooling-native.py -- --no-render`、`verify-cooling-install.py`、`node scripts/verify-cooling.mjs`、`npx tsc --noEmit`、`npm run build`。涉及生成姿态的更改，应先执行 `node scripts/prepare-starting.mjs`，再按需要用 `rebake-powertrain.py` 同步五份工程。不要用会整体重建/替换几何的旧脚本无条件覆盖最新成果。
6. 在实际浏览器检查合壳/开壳、左关右开、0.6→2.1 mm 磁隙、弹簧压缩/释放、停电滑行、暂停/慢动作与整车安装。记录实际截图和性能，不能以脚本成功代替观察。
7. 收尾后更新来源、验证日志和文档。随后继续研究原装万向轴安装关系，再逐项补全整车系统。逐部件资料应区分原车实物照、同系列照、目录/剖面图和猜测；缺资料就标出缺口，不能用合成图片或近似零件当作原始证据。

Blender 后台命令模板（当前目录必须为项目）：

```powershell
$mazBlender = Join-Path (Get-Location) 'work/tools/blender-4.5.13-windows-x64/blender.exe'
& $mazBlender -b --python-exit-code 1 --python 'scripts/verify-clutch-contact-native.py'
```

以上是恢复后的建议步骤，**迁移任务期间没有执行这些未完成的验证/导出**。对模型的最终完成判断必须回到 16 项完整验收，不得把局部改善和迁移成功混为一谈。
