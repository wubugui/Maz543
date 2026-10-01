# MAZ543 云开发权威进度记录

更新时间：2026-10-01 16:54 UTC。**每次开始任务先读本文件。**
本文件是唯一持续更新的工程进度入口；`CLOUD_HANDOFF.md` 是不可混淆的原始
迁移/生产基线，下面的历史段落保留旧证据。当前状态和工作流以本文件顶部为准。
独立研究、有限检查、发布成功均不代表整车验收：**16项仍全部OPEN**。

## 开工与完成一项时的固定流程

1. 先读本文件、`git status --short`、`git log -5 --oneline`，再检查正在运行的
   作业与已有终态报告。核实际环境和文件实体，不重复已完成的渲染/检查。
2. 只选择一个可明确验证的小项，写明输入SHA、具体改动、通过/失败条件及证据位置。
   不改生产默认，不把未知车型/批次、拟合尺寸或采样检查当原厂/连续证明。
3. 一项完成后，立即更新本文件和对应证据，**同一个提交记录改动与进度，立即
   正常push**，不等待整个阶段结束。失败但有价值的候选也明确标FAIL并及时提交。
4. 推送后核对远端分支SHA和树；新增LFS须有实体、上传终态以及针对性远端回取
   SHA验证。只有本地commit、LFS指针或准备上传不算已交付。认证/网络受阻时标明
   阻碍，先协调恢复推送，避免继续累积大量未推送成果。
5. 阶段报告和真实图片仍发项目既有Slack频道；区分原生/网页、生产/独立候选。
   私人目的地、凭据、签名URL和交付收据不进入这个公开仓库。

不再同步用户本机，不再为同步制作独立ZIP/分卷备份。GitHub的完整Git历史和LFS
是版本来源。只在证明远端可恢复后清理同内容缓存；不删除唯一未推材料、原工程
或改写历史。禁止强推、自动部署、付费扩容和擅自创建认证。

## 当前目标、发布依据与资产选择

目标仍是准确还原MAZ-543A：原比例与批次特征、真实零部件及装配、可编辑原生
机械、机械/电气功能、交互展示和实际画面。完整要求见`GOAL.md`、
`testcar/docs/ACCEPTANCE.md`、`testcar/MIGRATION_HANDOFF.md`。

- 独立开发分支：`development/cloud-maz543a-20260930`
- 最近已核实发布的HEAD：`f6d2454e3df436e2baaeeaef09a52d665caebbd4`（修复门整母版回归；模型仍cc47bf6）
- 该提交根树：`f3675dd072fa9ab5108153a5e7fa330ac0942ae2`
- 插件原生Git对象发布后远端ref/tree/parent及文件字节已核实，本地分支已对齐
- 原迁移分支保持：`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1`
- `migration/cloud-handoff/DELIVERY_STATE.json`确认完整快照，无待迁移文件；
  包含3484个实物源文件及100个原Git基线文件。稀疏检出不等于这些历史文件丢失
- 修复门整母版依赖回归已插件发布；本轮原驾驶室接触定位待立即发布。
  文档不能预先包含自身commit SHA，应以实际远端ref/tree核验为交付依据
- CLI设备登录仍被网络策略中断，不能声称恢复。代码/JSON/文档使用已授权GitHub
  插件原生blob/tree/commit/ref发布，不等待CLI；插件没有LFS上传接口，新大资产须
  先解决官方实体上传路线，不更改LFS属性或只发布缺失实体的指针

生产依旧为`rear-box-frame-20260930`，未被任何云候选替换：

| 资产 | SHA-256 |
|---|---|
| `testcar/outputs/MAZ543A_Master.blend` | `0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3` |
| `testcar/outputs/MAZ543A_Textured.blend` | `f927cfffae77e443fe6f7c8536bb2344d6b7694f335a071a26d4bba22e350f5d` |
| `testcar/public/models/maz543a-blender.glb` | `4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698` |

下一项装配检查应使用独立候选，不能误用独立仪表小场景作为整车：

| 用途 | 已发布文件及SHA-256 |
|---|---|
| 当前舱内/VA180 Master候选 | `testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend`；`8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70` |
| 对应Textured候选 | `testcar/outputs/cloud-va180-textured-20261001/MAZ543A_Textured.blend`；`6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266` |
| 开发专用GLB候选 | `testcar/public/models/review/maz543a-cab-va180-v1.glb`；`fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e` |
| 独立TEM15前脸iteration02 | `testcar/outputs/cloud-tem15-face-study-20261001/iteration-02/study.blend`；`a65ec84c7a03de257ad5971b9675bd4d83c5515a6429875e6d02418c760b3def` |

## 最近完成的小项、验证边界与证据

| 已发布提交 | 完成内容 | 实际检查与证据路径（均在testcar下） |
|---|---|---|
| `1b89f0d` | VA180局部研究装入原B4拟合孔的独立Master | `outputs/cloud-va180-panel-fit-20261001/`：四座椅保留、28追加对象身份、20宽阶段配对、192孔射线及192命中负控；已有3处装配干涉仍失败。原生全车/同机位近图已留存；4新LFS共71100371B全部远端回取SHA通过 |
| `43fc91e`、`139f671` | 原1977轮定位值和真实轮架拓扑只读诊断 | `outputs/cloud-wheel-alignment-20261001/`、`reference/wheel-alignment-source-20261001.json`：名义外倾幅值1°；1040mm参考直径前束，第一轴8–14mm，第二轴满载5–12/空载8–14mm。当前中性几何约0°/0mm，尚非载荷/胎压/滚动合格试验，未调车轮 |
| `664353c` | 支承螺栓原轴方向不足以接触上摆臂的定位 | `outputs/cloud-suspension-stop-axis-20261001/`：8站×136/138.5/141mm共24状态，完整螺栓XY投影与各上臂三角投影间隔4.0202–4.0488mm。仅这些状态的充分条件，不能称全行程证明；4新LFS共2975156B全部远端回取SHA通过 |
| `d1aa9ba` | Textured舱内/VA180和开发GLB，修正候选方向盘每帧姿态 | `outputs/cloud-va180-textured-20261001/`、`work/cloud-va180-web-20261001/`：261件/321姿态，顶点误差最大8.191µm；432原网格节点压缩流与原图像/纹理绑定/采样器保留；Khronos0错误0警告，Draco另解码。721候选姿态、480旧姿态、30选择条件、tsc/build通过。6新LFS共182630610B全部远端回取SHA通过；不等于真实网页验收 |
| `e4d3fec` | 补两件重编码原网格的UV检查 | `work/cloud-va180-uv-20261001/`：1200座椅底座三角+96方向柱三角，位置/UV角点与绕序一一匹配；最大UV误差0.0000893511/0.0001221895在12bit量化允许范围内。无像素一致性或网页声明，无新LFS |
| `cc47bf6` | 参考带1978护照照片的独立TEM15旧kg/cm²前脸 | `outputs/cloud-tem15-face-study-20261001/`、`reference/tem15-face-source-20261001.json`：iteration02九个闭合研究实体（含5个刻线/单位线实体，不是原厂部件数量）、36静态表面配对、腔体负控及可编辑曲线读回通过。真实正/斜图已看；未装车。6新LFS共3959535B在重置后全新Git/LFS恢复中逐SHA通过 |

最新开发GLB只在开发环境`?asset-review=cab-va180-v1`选择；生产及render-worker
入口回退生产。仪表/按钮仍是静态外观。云浏览器实际预览仍未通过，不能把代码
绑定测试或原生Cycles图叫作网页运行验证。

## 保留的失败、未解决事项

- `b9fb590`的顶点级Separate错误归档四个座椅基座，其“完整舱体保留/碰撞改善”
  结论已撤回。失败原件在Git历史中保留；修复版检查V/E/F选择和四个座椅语义身份
- 当前Master仍有方向柱/坐垫、左面板/内壁和LC22底座/内壁三处已知接触失败。
  不允许为降低碰撞计数移走应保留的车体；B4图注64与仪表识别冲突仍注明推断
- 旧三盖r3锁扣释放、前唇/格栅以及独立FG16的617三角对相交未解决；不能把
  盖面/轮胎/仪表的局部进步当作全车通过
- `work/cloud-va180-web-20261001/iteration-01-tangent-fallback/`保留首轮切线错误
  导出；最终临时原生三角化修复，源blend未保存。继承的多图像采样器警告仍记录，
  最终图像/绑定/采样器逐字保留已验证
- TEM15根目录首版指针帽缝重复顶点非流形；iteration02用原生Weld修复，独立位置
  集合完全不变，编辑Curve保留。首96sample图噪声/反光不合格，双图任务触发明确
  180秒截止；首斜图灯块遮挡刻度也保留。最终分段64sample原生去噪图只改善审图，
  没改几何；细刻线、字体、尺寸、1977批次和内部机构仍未验收
- 原厂11500±25mm长度与当前11269.1mm包络、非等轴载荷、悬架止挡/预载、右后电池箱
  和左过滤通风设备/543A油箱架的真实安装、多个机械内构及全车性能仍开放
- 现代UK143A厂家目录的24V/40–120℃/60mm/M5只属于该现代型号，不能直接当1977
  UK143的尺寸或用多型号分类配图替代已确认实物
- 现有1496门区间结果只覆盖生产四门44件对34个BL_Front件。新增仪表板、VA180和
  方向柱没有因此自动得到全连续装配证明；新44×261范围的独立证据见下文，
  仍不能向未检查的原驾驶室几何外推

## 2026-10-01环境变化与已恢复状态

13:26 UTC执行环境标识及工作目录创建时间发生变化，原工作区/工具/私有认证配置
不再存在。此前精确清理仅处理已核远端可恢复的重复包/回读缓存；项目随后仍成功
建模、渲染，并在13:23提交cc47bf6。不能据此杜撰环境变化的触发原因。

- cc47bf6普通Git+6个LFS上传会话已返回exit0，远端ref/tree匹配；项目成果保住
- 已正常从公开仓库重新稀疏clone到同名Maz543目录，现已对齐修复门回归提交f6d2454；普通Git对象
  refetch后检查4017个可达对象，无缺失。没有展开整份LFS历史
- TEM15本轮6个实体及当前VA180 Master（66069335B，8e962d6…）已实际恢复、
  SHA/字节数核对并checkout；其他生产/历史/候选
  大文件仍需按本次任务选择性恢复。**不要把指针文件当实体，或把此状态写成全仓库
  已物化恢复**
- 官方Blender4.5.13精确归档SHA匹配并恢复；系统Blender4.3.2不是已验证替代版
- Node24.19.0；使用锁文件和工作区npm缓存恢复577依赖成功。重置前tsc/build通过，
  不自动等同于新恢复环境重新通过完整运行/浏览器检查
- 未提交损失仅指已知的“候选四门对新舱内部件区间检查”草稿修改，尚未运行/验收，
  不在cc47bf6中，需从已发布原脚本重建。不要声称这项已完成或已恢复
- 新取得的原始参考照片/PDF不公开转载；若本地副本缺失，按已保存来源URL和SHA
  正常获取。未取得的源图不能靠文字猜测重建
- 15:21只读`gh auth status`显示未登录。旧私有配置未恢复，不读取/搬运凭据、
  不自行重新登录；由已授权主线程协调认证。公开仓库只读恢复不等于有写入认证
- TEM15正/斜视图均已完成分享，15:49精确线程读取确认两个文件；不要重复发送

## 当前已完成小项：舱内候选门依赖清单

`testcar/scripts/inspect-cab-door-dependencies.py`在精确4.5.13中只读当前8e962d6…
Master，frame0，不转门、不保存。实际12.965秒/峰1708608KiB，退出0，源SHA前后相同。
证据：`testcar/work/cloud-cab-door-dependencies-20261001/`的inventory.json、read.log、process.json。

- 四门44件；既定左右面板层级及五个保留舱件中261个相机筛选几何、78个被排除对象
  均有名字和原因。筛选标志不是实际成像可见性，也不能证明遮挡/物理存在
- 递归449个对象记录父级、修饰器、约束、动画、形态键及Boolean工具。10个Boolean
  没有直接引用四门移动层级；记录256 Bevel、30 Solidify、28 WeightedNormal
- 唯一动画为VA180按钮自属性press_mm=0的location.z驱动，表达式-p/1000.0，仍有
  GENERATOR曲线修饰器待详细检查。不能因当前值为0就宣称整个驱动恒定或无依赖
- 未做任何转门姿态回归/区间净空，新结果只称SCOPED_DEPENDENCY_INVENTORY_ONLY_NOT_CLEARANCE。
  旧1496配对结论不扩展；三处已有装配干涉和16项OPEN维持
- 本项已发布a4b66a6，5个文本文件公共fetch逐字核对、远端完整树匹配，无新LFS

## 最新完成小项：原生转门有限姿态回归

`testcar/scripts/verify-candidate-cab-door-poses.py`只读同一母版和上述固定清单，
4门各检查0、0.731、14.37、48.125、83.61、99度，按钮保持释放0mm。4.5.13实际
14.676秒/峰1724616KiB退出0，源SHA前后完全相同，无模型保存或新增LFS。
证据在`testcar/work/cloud-cab-door-poses-20261001/`：pose-report.json、read.log、process.json。

- 24姿态×261固定件，共6264次逐顶点及三角索引精确相等检查通过；恢复后也完全一致
- 264次移动件检查的顶点数量/三角索引全部保留；与刚体解析式最大误差
  2.261213740051484e-7m，低于20µm门；没有以放宽容差消除失败
- 按钮父级matrix_basis和press_mm在全部姿态精确保持；GENERATOR实际是一次多项式
  系数[0,1]，不叠加、不限范围、不使用影响量，驱动仍为-p/1000.0。完整参数已记录
- 结论仅SAMPLED_NATIVE_POSE_REGRESSION_PASS，**不证明连续净空、任意帧、按钮全行程
  或所有场景依赖**。未做三角碰撞检查，三处已知装配接触没有因此改善，16项仍OPEN

## 最新完成小项：冻结刚体全角区间包围

有限姿态回归已发布2e4b3bf，5文本文件/完整树实际回取一致。本项
`testcar/scripts/audit-candidate-cab-frozen-intervals.py`使用同一母版、依赖清单及
已发布姿态报告SHA，不重复运行已通过的姿态采样。4.5.13实际13.777秒/峰1725448KiB。

四门44件×261舱件=11484对，在各自带方向0–99°闭区间的冻结刚体解析包围中，
每对均以一个完整区间严格分离，0个UNRESOLVED。每个移动/固定包围都外扩20µm；
最小外扩后轴向间隙为0.00236010382611m。这是顶点三角凸包的充分分离界，不是精确最短表面距离。

每门逐对索引、证明状态、区间数量和正间隙写入
`testcar/work/cloud-cab-frozen-intervals-20261001/cab_pivot_00*.json`，
同目录interval-report.json含输入/报告SHA和边界，read.log/process.json保留实际终态。
母版没有保存，源SHA未变，无新LFS。

本报告本身仍只称CONDITIONAL_FROZEN_SNAPSHOT_INTERVALS_ONLY，后续依赖审查单独留证，
不能仅将此项与有限采样拼接成无条件的原生全连续通过。未含其他车体表面、按钮行程、
网页或厂家装配尺寸，16项仍OPEN；三处已知舱内相互干涉仍失败。

## 最新完成小项：严格原生依赖资格与拒绝控制

冻结区间已发布5d70628，9文本文件/完整树实际回取一致。新脚本
`testcar/scripts/audit-candidate-cab-static-dependencies.py`在精确母版frame0递归审查
431个对象/运动上下文：父级、Boolean对象/集合工具、动画/约束、形态键、Curve外部
bevel/taper及支持的局部修饰器。固定依赖进入移动门层级会拒绝，未知活动修饰器会拒绝。
只有精确名称的释放按钮单一自属性驱动、无action/NLA/关键帧/采样点、恒等[0,1]曲线
修饰器可按保持0mm域接受。结果0个issues，SCOPED_NATIVE_RIGID_DEPENDENCY_ELIGIBLE。

追加的真实Blender临时fixture不修改任何原对象且全部移除：静态基线接受，约束、
frame动画驱动、Boolean引用移动门件、Curve外部轮廓和未知Nodes五类分别拒绝。
含控制版实际10.900秒/峰1716804KiB退出0，源SHA前后相同；不保存blend，无新LFS。
证据在`testcar/work/cloud-cab-static-dependencies-20261001/`，首轮无控制读回也保留。

这把限定场景依赖、既有有限姿态回归与闭区间快照包围衔接起来，支持**此母版frame0、
按钮释放、其他控制固定时，44门件对选定261舱件的条件分离结论**。它不是Blender
浮点实现的形式化证明，不含render位移/材质、其他车体、按钮运动、网页或厂家装配。
此处为首次通用门结果；后续独立复审发现并修复的FONT依赖遗漏见下文。
16项仍OPEN，已有三处舱内静态接触仍失败。

## 最新完成小项：原驾驶室遗漏范围清点

严格依赖已发布a8721fe，7文本文件/完整树实际回取一致。
`testcar/scripts/inventory-original-cab-scope.py`读取相同母版的cab实际父树：598个后代，
532个几何对象，恰含已检查261固定件+44门件，另有227件没有进入这组配对范围。
其中145件对象自身hide_render=false，82件自身隐藏；**这不是最终成像可见性或
物理排除结论**，脚本逐件记录材质、原生评估顶点/三角数、包络、父树与渲染标志。

遗漏件包括原驾驶室外壳/侧壁/顶盖/窗框、镜架/雨刷、灯件、踏板等；名称不是厂家
语义身份验证。另有24个cab_/BL_Front_/BL_Door_命名查询找到的几何在cab父树之外，
例如保险杠、中央盖与支承件，单独列清，不随意并入或静默排除。
证据`testcar/work/cloud-original-cab-scope-20261001/inventory.json`及读回日志/进程报告。
4.5.13实际12.508秒/峰1709940KiB，源SHA未变，无保存/新LFS，无净空通过声明。

## 最新完成小项：独立复审与FONT依赖门修复

原驾驶室清单已发布77a6243，5文本文件/完整树回取一致。独立只读复审使用另一套
三角函数极值枚举重算11484对，与保存间隙逐项差0，最小仍2.360103826112736mm。
435个实际对象全部OBJECT parent，无rigid_body/pose/外部Curve/Text Object指针；
四门铰链单位旋转/缩放，实际父对象为EMPTY。源SHA不变，当前精确范围条件结论保留。

复审同时复现一个**通用检查器漏洞**：遗漏FONT.follow_curve依赖，固定frame0仅
转另一个铰链0.7rad，34个文字顶点最大位移2.765747175m，旧audit却返回空issues。
精确母版没有这个指针，所以不把通用漏洞误写成当前母版已经失效；旧失败证据完整保留。

修复后统一拒绝data Object指针（包括follow_curve）、非OBJECT parent、rigid/pose和
外部库输入，普通对象与hinge共用检查。补证据完整性：11×261索引笛卡尔积、名字顺序、
角度方向、24实际姿态及固定/按钮保持记录，不能只信status标签。
`scripts/test-cab-dependency-guards.py`只加载空白小场景，实际旧门接受/新门拒绝同一
变形文字；静态文字仍接受，特殊hinge/刚体/armature负控和6类证据破坏负控通过。
独立复审者再次只读核新diff及测试结果，未发现新增假通过。

证据在`work/cloud-cab-independent-review-20261001/`：原始独立脚本/291601B JSON、
冻结旧checker、README、小fixture结果与日志。原脚本按历史原样保留；稳定回归入口
为上述test脚本+冻结旧checker，另有仅改路径且未重跑的独立复核replay供按需使用。
**本次没有重新加载整母版运行修复门**，用小fixture回归+先前独立435字段实测衔接；
不重复已有整车/区间检查。日志保留默认只读配置目录的非致命扩展缓存警告。
20µm是本检查采用的数值保护量，不是已推导的全角度Blender浮点误差上界；有限
姿态的0.226µm观测误差不能替代该推导，条件结论保留这项限制。
没有新LFS、模型保存、厂家尺寸或网页验收，16项继续OPEN。

## 最新完成小项：修复门整母版依赖回归

检查器修复/独立证据已发布c617567，10文本文件实际回取逐字一致。随后只重跑修复后
依赖门一次，输出到新`work/cloud-cab-static-dependencies-guarded-20261001/`，旧报告
完整保留，不重复此前几何/区间重算。精确4.5.13、Master SHA相同，10.347秒/峰
1716008KiB退出0：431检查0issues，配对/名字/角度/24姿态证据完整性门通过，原六个
小fixture分类检查仍通过。源SHA前后相同，无模型保存或新增LFS。

本项补上先前文档“修复门尚未整母版再跑”的待办，仍只表示限定依赖资格无误拒；
20µm数值保护量、未检查227件/其他车辆表面、网页及厂家装配的边界保持不变。

## 最新完成小项：原驾驶室145件接触定位

修复门回归已发布f6d2454，5文本文件/完整树实际回取一致。新脚本
`scripts/locate-original-cab-door-contacts.py`只读原树外于261范围的145件（仅按对象
自身hide_render=false选择，未用集合状态静默排除）。44×145=6380对，全角冻结
包围6262对分离，118对重叠未解决。未以包围重叠直接断言碰撞。

四门各0/15/45/75/99度共20实际姿态，145固定件顶点与三角索引都保持。零epsilon
原生BVH表面检测记录40个唯一对象对、80个姿态接触实例：门壳从15度起与原侧壳
有候选，大角度还涉及三角窗框/玻璃；闭门与cab_0063以及侧铆钉有候选。铰链、密封件
可能有设计接触，BVH计数不是穿透深度，不能直接当厂家装配失败或因零命中就判通过。

证据`work/cloud-original-cab-contact-location-20261001/`含四门逐对/逐姿态/前8个
命中三角索引、来源SHA、摘要和实际日志。4.5.13实际12.302秒/峰1735828KiB，源SHA
未变，无模型保存/新LFS。82个自身隐藏件和24个父树外名称查询几何仍未覆盖。
这组结果保持CONTACT_LOCATION_ONLY_NOT_ACCEPTANCE，不能晋级整驾驶室/全车。

## 下一个具体动作与完成条件

1. 先核本小项远端发布，每次开工先读本文件。独立复审已完成这组限定范围，
   不外推到新227件或其他车辆表面
2. 修复门整母版依赖回归已完成，不再重复。对实际侧壳/三角窗接触候选，先核
   当前运动pivot与实际三个铰链几何轴是否一致，再用截面/体积或源图区分接触与穿透。
   只按已量得的几何/明确参考解释，不凭消除BVH数量挪走车体或座椅
3. 保留118未解决包围、82隐藏件、24父树外查询结果与三处旧舱内接触。缺原厂装配
   尺寸标FITTED/OPEN，不新增尚无正式上传路线的大资产
4. 每个可验证小项立即更新本文件、提交并通过插件发布核验；不等阶段结束

## 精确版本与恢复命令

以下用于新的空目录，正常官方读取；已有目录先读进度/检查状态，禁止覆盖现有未提交
成果。共享磁盘有限，不使用`git lfs fetch --all`或全历史无筛选checkout。

```bash
GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0 git clone --filter=blob:none --no-checkout --single-branch --branch development/cloud-maz543a-20260930 https://github.com/wubugui/Maz543.git Maz543
cd Maz543
git lfs install --local
GIT_LFS_SKIP_SMUDGE=1 git sparse-checkout init --no-cone
GIT_LFS_SKIP_SMUDGE=1 git sparse-checkout set --no-cone '/AGENTS.md' '/CLOUD_HANDOFF.md' '/CLOUD_CONTINUATION.md' '/GOAL.md' '/.gitattributes' '/.gitignore' '/testcar/*' '!/testcar/outputs/' '!/testcar/work/' '!/testcar/public/models/' '/testcar/outputs/cloud-tem15-face-study-20261001/' '/migration/cloud-handoff/'
GIT_LFS_SKIP_SMUDGE=1 git checkout development/cloud-maz543a-20260930
git rev-parse HEAD 'HEAD^{tree}'
GIT_TERMINAL_PROMPT=0 git ls-remote origin refs/heads/development/cloud-maz543a-20260930
```

如果部分克隆导致LFS扫描逐个获取小Git指针，可正常一次补齐普通Git对象：

```bash
GIT_TERMINAL_PROMPT=0 git -c pack.threads=1 -c gc.auto=0 -c maintenance.auto=false fetch --refetch --no-filter --no-tags --no-write-fetch-head origin cc47bf6a3188e50b9d7cbe2d8c546886b6ea1ae0
GIT_TERMINAL_PROMPT=0 git -c lfs.concurrenttransfers=2 -c lfs.fetchrecentalways=false lfs fetch --include='testcar/outputs/cloud-tem15-face-study-20261001/**' --exclude='' origin cc47bf6a3188e50b9d7cbe2d8c546886b6ea1ae0
# checkout使用明确文件；仅目录尾斜杠不会物化这些文件。
git lfs checkout testcar/outputs/cloud-tem15-face-study-20261001/study.blend testcar/outputs/cloud-tem15-face-study-20261001/iteration-02/study.blend testcar/outputs/cloud-tem15-face-study-20261001/iteration-02/front.png testcar/outputs/cloud-tem15-face-study-20261001/iteration-02/front-lighting02.png testcar/outputs/cloud-tem15-face-study-20261001/iteration-02/oblique-lighting02.png testcar/outputs/cloud-tem15-face-study-20261001/iteration-02/oblique-lighting03.png
```

每个恢复实体应以`git show REV:path`中的LFS oid/size为准核SHA/字节数。
其他任务只添加实际需要的稀疏路径和LFS include。远端完整性验证应从新的空LFS
校验目录实际获取相关新OID；不能用本地`.git/lfs`已有对象冒充远端回取。

Blender官方精确归档：
`https://download.blender.org/release/Blender4.5/blender-4.5.13-linux-x64.tar.xz`，
378033952B，SHA-256
`da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91`。
先校验再解包到项目外专属工具目录。当前路径为
`../maz543-tools/blender-4.5.13-linux-x64/blender`，版本4.5.13、build`daeeeca98fb0`。
官方目录页曾返回402而精确归档正常返回；不要把具体工具错误泛化为政策拒绝，
也不绕过真正认证/TLS/访问拒绝。

```bash
# 从仓库根目录；缓存放在允许写入的工作区，避免默认home目录缺失。
cd testcar
npm_config_cache="$PWD/../../maz543-tools/npm-cache" npm ci
node node_modules/typescript/bin/tsc --noEmit
npm run build
# Native脚本从testcar运行，例如：
../../maz543-tools/blender-4.5.13-linux-x64/blender -b --threads 2 --python scripts/verify-tem15-face-study.py -- --directory outputs/cloud-tem15-face-study-20261001/iteration-02
```

新环境的认证检查只用已授权配置中的`gh auth status`，不打印token，不把凭据放进
仓库。写入认证由主线程确认后，用正常pre-push钩子上传LFS，再非force推独立分支；
匹配远端SHA/tree和实体回取后才报告发布成功。

---

# 历史工程记录（保留证据，不作为旧流程的执行授权）

2026-10-01 correction: the `b9fb590` cab-panel fit trials used a defective
vertex-only Separate selection and inadvertently archived all four seat bases.
The saved second trial has 0 remaining seat-base vertices and 5,400 archived
vertices instead of the intended 1,800. Its complete-cabin preservation claim
is withdrawn; its images/contact counts cannot establish an assembly improvement.
Original production and the independent panel study are unaffected. Preserve the
failed model files and their Git history; corrected trials require per-seat identity, geometry/UV and
actual render-path checks. See the corrected fit-study README and saved
`separation-inspection.json`.

The original full migration remains commit
`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1` on
`migration/maz543a-20260930`. Subsequent cloud work is on the separate
branch `development/cloud-maz543a-20260930`. At the original publication checkpoint, commits through
`63fe135bf1b1c9237c6158519fb77203a9f9a6be` were published by normal Git/LFS push
and independently verified. Later published checkpoints are recorded above. Keep the original migration history and
all failed candidates. All 16 whole-vehicle acceptance gates remain OPEN.

## Production still unchanged

The unique production version remains `rear-box-frame-20260930`, with the
three SHA-256 values in `CLOUD_HANDOFF.md`. No cloud candidate below is a
replacement for the production masters or production GLB.

## Current reviewable work

- Three-cover r3: `testcar/outputs/cloud-cover-service-r3-20260930/README.md`.
  Two editable portable vehicle candidates. The closed front lip/cover overlap
  was removed, but latch release still interferes and the lower lip intersects
  the grille. Discrete service states, fitted mechanism; overall FAIL.
- Tyre lettering: `testcar/docs/CLOUD_TYRE_LETTERING_20260930.md` and
  `CLOUD_REVIEW_ENTRY_20260930.md`. The portable v2 export reproduces exactly;
  its development-only review selector retains the normal production default.
  This is not actual cloud browser acceptance.
- Reference calibration: `testcar/docs/CLOUD_REFERENCE_CALIBRATION_20260930.md`.
  Original 1977 table establishes 543A length11500±25 mm; current two native
  envelopes are11269.1 mm. Published front/rear unloaded group loads differ
  from the equal-load numerical initialization. No global scale or physical
  constants were changed just to match one number.
- FG16 study: `testcar/outputs/cloud-fg16-study-20260930/README.md`.
  Independent editable hollow-shell/optical/glass structure, actual Cycles
  exterior and section. The shareable blend omits newly obtained manual scan
  pixels. Optical element/base still has617 rigid triangle intersections;
  connectivity, dimensions and installation remain OPEN. The local packed
  research copy and iterations are not on the public-ready whitelist.
- Door angle intervals: `testcar/docs/CLOUD_DOOR_INTERVALS_20260930.md` and
  `testcar/outputs/cloud-door-intervals-20260930/REVIEW.md`. Actual four doors,
  44 moving parts against34 added front parts:1496 sufficient swept-box
  separation results over the complete0–99° interval. Explicit static/rigid
  dependency checks, independent pose comparisons and between-sample collision
  negative control are retained. This excludes original cab/frame/interior,
  other vehicle interactions and real browser operation; it is not whole-car
  continuous clearance acceptance or formal machine-arithmetic certification.
- Equipment and suspension sources: `testcar/docs/CLOUD_EQUIPMENT_REFERENCE_20260930.md`
  and `SUSPENSION_REFERENCE_REGISTER.md`. Original variant/revision distinctions
  and remaining hardpoint/stop/installation unknowns must be preserved.
- Torsion installation datum: `testcar/docs/CLOUD_SUSPENSION_INSTALLATION_20261001.md`.
  Original p320 resolves136–141mm as the lower-arm head-centre vertical difference
  during installation, not wheel travel. Existing unadjusted support bolts are
  separated from the arms in24 actual diagnostic states. Four isolated editable
  reference scenes and the original module archive are saved;680 object-pose
  comparisons preserve all evaluated vertices/topology. This does not repair
  stop support, adjustment or preload.
- Battery structure: `testcar/outputs/cloud-12st70-structure-20261001/README.md`.
  Original1977/1983 sources support wood case, two steel bands and three actual
  four-chamber ebonite tanks. The independent73-part candidate retains12 real
  cavities and source curves; all73parts closed after native seam welding.
  Cell plate packs, terminal hood, overall cover, exact carrying hardware and
  four-unit vehicle installation remain missing. The70/70M figure/text variant
  distinction and incomplete fitted envelope remain explicit.
- Complete current-production front/rear views:
  `testcar/outputs/cloud-whole-production-20261001/render-manifest.json`.
  Fresh actual Cycles renders fit all measured vehicle-envelope corners in the
  image and use the unchanged production Master. They do not depict the cloud
  component candidates as installed.
- Battery enclosure forms: `testcar/outputs/cloud-12st70-enclosure-20261001/README.md`.
  The original73 parts are retained exactly; two native fitted forms add the
  documented pressed-wood overall lid and terminal hood. Generic1983 fig4 does
  not identify a production variant or provide fastener locations. Initial
  lid/hood intersection was retained and corrected in this independent study.
  Current147 new-part pairs have whole-box separation or empty native Boolean
  intersections; this excludes fasteners, retention and actual removal motion.
  The two display offsets are not a factory service mechanism. All16 remain OPEN.
- Photo-observed hood grips: `testcar/outputs/cloud-cover-grips-20261001/README.md`.
  Four actual photographer-sourced MAZ543A-labelled views distinguish the two
  transverse top grips from the separate narrow front-edge fasteners. The
  independent two-vehicle candidate adds only the missing grips. Original8712/
  6932 geometry-object snapshots match; grip topology and four attachment
  diagnostic poses were read back. Oldr3 interference and all16 gates remain
  OPEN. Same-camera before/after plus a whole-candidate native view are saved.
  The source register has URLs/attribution/limits, without newly obtained photo
  pixels. Continue photo-guided broad cover contours; do not invent latch axes.
- Photo-guided continuous hood relief:
  `testcar/outputs/cloud-cover-contour-20261001/README.md`. Two editable vehicle
  candidates use native local-position Geometry Nodes before the original
  Solidify to add broad lands and grip troughs. The45mm fit is not an OEM
  dimension. The28mm shallow-cosine first iteration is retained because its
  actual images expressed the source shape too weakly. Both new files reopen;
  zero amplitude recovers the input panel vertices/indices exactly. Five
  discrete diagnostic states show at most2.173um local vertex-set variation;
  existing lock/lip failures and all16 gates remain OPEN. Current detail/whole
  native images were completed and source-SHA-checked; no repeated rendering
  is needed on continuation. Sources remain the normally obtained A-labelled
  Flickr/Fototruck photographs, without photo pixels in new public assets.

- Hood/tyre composite: `testcar/outputs/cloud-hood-tyre-composite-20261001/README.md`.
  Integrates the second continuous hood candidate with 144 native wheel glyphs.
  Both saved masters pass scoped glyph geometry checks; 8570 Master and 6926
  Textured unrelated objects preserve evaluated geometry, authored UVs, modifier
  inputs, transforms/parents and material slot names. Strict evaluated-UV
  bitwise preservation remains FAIL (3170/2277 objects); repeated evaluation of
  the unchanged input also shows small UV variation. No threshold exemption,
  production promotion. A real combined whole-vehicle native image and two raw
  GLB exports are retained. v1 hood quantization fails; v2 raises position
  precision and passes limited decoded hood/glyph transport. Neither is
  browser-tested. A separate packed candidate preserves414 unrelated mesh
  nodes, with16 new/changed primitive streams checked. Development-only
  `asset-review=hood-tyre-v1` entry and build checks pass; actual browser remains
  untested. See its STATE.

- Left-driver side candidate: `testcar/outputs/cloud-left-driver-side-20261001/README.md`.
  Original1977 source confirms the inherited steering/pedals were in the right
  cabin. Seven retained controls (788 vertices) and the steering group move by
  the existing fitted cabin spacing to the left. Native separation and fresh
  paired-file preservation checks pass; exact shapes/positions remain fitted.
  Actual viewport binding-statement tests address the legacy per-frame pose
  reset without renumbering pivots. Source rig and production remain unchanged.
  Check this candidate's STATE before rendering or continuing; no browser pass.

## Verified environment and remaining access limits

Official Blender4.5.13 LTS, build `daeeeca98fb0`, was verified. Thread limits are
recorded per run; recent Cycles work used two CPU threads.
After the former shared tools directory became unavailable, the same official
archive was downloaded and verified at a MAZ-specific tools location outside
this repository. Archive SHA-256:
`da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91`.
Locate the installed binary in the active environment; do not assume the old
`/workspace/shared` path exists or install tools into the source tree.

Node dependencies and actual TypeScript/build checks previously passed in
this cloud workspace. Native Cycles images are genuine model renders, not
webpage screenshots. The cloud browser returned `net::ERR_BLOCKED_BY_CLIENT`
for the local preview, so browser checks remain blocked pending a supported
preview route. Do not change network/security settings or use a different
browser to bypass that denial.

The earlier Library/bundle-to-Windows transfer plan is cancelled. It is retained
only as historical context: five incremental checkpoints were backed up before
normal cloud Git authentication became available. All five are now ancestors of
the published development branch. All91 associated new LFS entities were actually
recovered from GitHub and SHA-verified on2026-10-01 before deleting duplicate local
packages. Historical Library deliveries were not deleted. Do not recreate that
transfer plan, make new independent backup ZIPs or resume desktop synchronization.
The current workflow, authentication boundary and recovery commands are above.

## Independent cab-panel study, 2026-10-01

`testcar/outputs/cloud-cab-panel-study-20261001/` retains an editable standalone
study of the distinct Fig101 left and Fig102 right panels. Fresh native readback
checks 247 closed finite positive-volume solids and 57 real through-holes with
positive/negative controls. Three actual Cycles views were inspected; appearance,
factory dimensions, conflicting source captions and cabin installation remain
OPEN. No vehicle master or browser asset was changed. All 16 vehicle gates stay
OPEN. This stage originally followed externally backed-up checkpoint `01097c9`; its
model and image entities are now retained in the published Git/LFS history.

The subsequent panel-study checkpoint `f619cb66959533f13ddee5aba53739ebbab98d5c`
was also externally saved and officially read back, with its full archive hash
and all four new LFS payload hashes verified. The historical archive chain was
`4f28bd4 -> 01097c9 -> f619cb6`. This checkpoint is now in the published Git/LFS
history; the former desktop-transfer plan is cancelled.

## Cab-panel fit trials, 2026-10-01

Two independent Master installation trials are retained in
`testcar/outputs/cloud-cab-panel-fit-20261001/`. Both keep the new study size
and inherit a legacy dashboard proxy anchor, never a factory datum. The first
centre-plane trial has 2 panel-to-existing rest surface intersection pairs. The
second driver-facing-plane trial has 15, including steering-wheel interference.
Both preserve 247 closed solids / 57 through-holes in fresh readback; that does
not accept either installation. The second reader exits 2 on surface contacts.
The early report claimed only dashboard/gauge proxies were archived and unrelated
geometry was unchanged. That claim was withdrawn: defective Separate selection
also archived all four seat bases. Preserve these failed trials, but do not reuse
their lower contact counts as an improvement. Source metadata and the fit trials
remain unaccepted. No browser asset or production was changed.
The old steering-column/seat intersections are separately retained in
`cloud-left-driver-rest-audit-20261001`, not solved by a new instrument layout.


Third panel trial restores the exact four seat bases and adds independent
saved-file identity and ViewLayer/camera eligibility checks (7,708 original
meshes, 362 study descendants, 248 eligible objects, zero scoped failures).
Panel installation still has 15 rest surface-intersection pairs. Two actual same-camera seat-base comparison images are now complete and
inspected. They show the restored front-left base, including the still-failing
legacy steering-rod intersection. The earlier exit137/no-PNG attempt is retained;
its cause is not established. No whole-vehicle gate passes.


Corrective checkpoint `8cb82c90245f92c9d0fdb9ad7da3053aa77f0d18`
was externally saved with all three new LFS entities. All archive payload hashes,
four official read-back parts and the reassembled archive SHA-256 passed. The historical
external recovery chain was `4f28bd4 -> 01097c9 -> f619cb6 -> b9fb590
-> 8cb82c9`. The defective b9 trials remain as withdrawn historical evidence.
External storage does not confirm desktop synchronization or GitHub publication.


The independent `cloud-steering-photo-hypothesis-20261001` native candidate
follows the photograph-supported upper-rearward column direction and makes the
whole wheel/column coaxial. It preserves the old wheel centre, angle magnitude
and column bottom Z as FITTED; bottom X and length are refitted, not factory
mounts. Fresh readback retains all10,405 objects and four seat bases in the stated
identity scope. One column/cushion and two unchanged panel/wall object pairs
remain failed; reader exits2. Two actual native Master inspection images (matched footwell and left-cab overview)
have been rendered and inspected; blank gauges and prototype materials remain
unaccepted. No production or
browser changes. All16 gates remain OPEN.


Checkpoint `63fe135bf1b1c9237c6158519fb77203a9f9a6be` and its complete
increment after8cb82c9 are externally saved. The official single-archive route
and whole-file readback succeeded, including all3 new LFS payload SHA checks.
Recovery chain now ends `... -> b9fb590 -> 8cb82c9 -> 63fe135`. This describes the historical backup state only. Normal Git/LFS publication
was subsequently completed; current delivery state is at the top of this file.


Historical independent VA180 front study before504c1d5: `cloud-va180-face-study-20261001`.
Original1977 operation paragraph plus three inspected firsthand product photos
support a curved upper display, opaque lower cover, correction screw and
independent pushbutton. Unknown manufacturer/batch dimensions, font, button
stroke and minor/voltage markings are not claimed calibrated. Root trial and
iteration02 retain backing/control and backing/case contact failures. Iteration03
has10 closed study solids,3 actual openings,45 scoped rest pairs with no unexpected
intersections, and sampled independent button return. Its two native images were
inspected; side-face shading was subsequently refined in iteration04. No vehicle/panel
installation or production change, all16 OPEN. The later504c1d5 publication and remote entity checks are recorded below;
this paragraph does not prescribe a new archive workflow.


## Verified GitHub publication, 2026-10-01

Normal non-force push published `63fe135bf1b1c9237c6158519fb77203a9f9a6be` to
`development/cloud-maz543a-20260930`. Independent remote ref and GitHub commit/tree
reads match root tree `7255a6709fa28f2c58c59340cb200a64caf0317e`; migration remains
`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1`. All91 newly reachable LFS objects
(1,838,047,263 bytes) completed standard Git LFS upload/existence confirmation.
Four representative production/candidate Master and GLB entities were freshly
downloaded by official Git LFS into an initially empty separate store; all four
byte counts and SHA256 values matched (171,551,481 bytes). The remaining87 were
not individually re-downloaded. The first scan failure is retained; normal Git
metadata refetch resolved it before successful remote retrieval.

The workflow after normal Git publication became cloud development -> GitHub ->
stage Slack report. The latest requirement above now makes the push immediate
after each completed verifiable item. Desktop synchronization is cancelled. Historical Library deliveries remain retained; new duplicate backup packages
are not part of the current workflow. No production asset was promoted, and all16 gates remain OPEN.

## Subsequent verified checkpoint and wheel-alignment diagnosis

VA180 partial study iteration04 is committed and normally pushed at
`504c1d5093b1c7f16a1879f41cba44a1ef111633`. Remote ref and root tree
`558038801839fcae1b86f5aae54dce5887cd0feb` match. All9 new LFS entities
(15,203,039 bytes) were freshly downloaded by official Git LFS into an empty
verification store and passed byte/SHA checks. Both actual native study images
were delivered to the dedicated progress channel. It is still an independent,
partially referenced device study; not installed or factory-dimension validated.

Original 1977 manual pp24/316–317 now establish a nominal steered-wheel camber
magnitude1° and positive toe ranges at1040mm reference diameter. The new read-only
`cloud-wheel-alignment-20261001` diagnosis measures actual production front tyre
profiles at neutral pose: camber approximately0°, simultaneous static sidewall
rear-minus-front separations approximately0mm on both front axles. This exposes a
nominal geometry gap, not a load/pressure/rolling-qualified alignment test. Source
SHA is unchanged. No adjustment is made until native carrier/hub/suspension
semantics and measurement conventions are resolved. All16 gates remain OPEN.

The next independent `cloud-va180-panel-fit-20261001/MAZ543A_Master.blend`
appends the retained partial VA180 study at the existing B4 fitted hole. All10,405
old objects are retained; exactly8 B4 proxies are hidden and preserved. Fresh
readback retains all four seat-base regions and reports no scoped identity
failures. All28 appended objects match their source identities and expected
uniformly scaled world transforms. New-vs-existing static surface contacts are0
across20 broad-phase pairs;192 actual plate-opening rays pass with a192-hit
disabled-Boolean negative control. These are scoped checks, not assembly
acceptance. Existing column/cushion and two panel/wall failures, caption64 conflict,
fitted dimensions and incomplete calibration marks remain unresolved. Two actual
same-camera native close-up images and one current-candidate whole-vehicle image
have been rendered and inspected. The whole view retains the complete vehicle
envelope in frame; its small internal instrument is not visible at that scale.
Production remains unchanged and all16 gates remain OPEN.

The retained support-bolt issue is now narrowed in
`cloud-suspension-stop-axis-20261001`. At all8 stations and each136/138.5/141mm
installation setting, the full native bolt's XY convex hull is separated from
every upper-arm triangle projection by4.0202–4.0488mm. Original-axis vertical
translation therefore cannot make those surfaces touch at those24 sampled poses.
This is a numerical sufficient condition with20µm guard, not a continuous
suspension-interval proof. Earlier25.44mm AABB separation remains a lower bound,
not a screw adjustment distance. Existing simple shaft/nut positioning and actual
support hardware require reference-grounded revision; no guessed bore locations
or bolt extension have been applied. Three original sampled pose reports, an
eight-station readback, native isolated views and a scientific projection plot are
retained. No geometry is modified and all16 gates remain OPEN.

The independent `cloud-va180-textured-20261001` native sibling now reproduces the
published cab/VA180 Master edits while retaining its Textured baseline's own seat
UVs/materials. Fresh native identity and four-seat preservation checks pass. The
new development-only `cab-va180-v1` GLB transports 261 geometry parts and 321 poses
(maximum vertex error 8.191 micrometres), preserves 432 existing mesh-node streams
and the original ordered images/texture bindings/samplers. Native tangent fallback
from the first export is retained as failed evidence; native temporary n-gon
triangulation resolves it in the final export. One inherited exporter sampler
warning remains; final sampler/image preservation is exact. Khronos validation
has zero errors/warnings, with the Draco payload checked separately by decoding.
Candidate-only steering binding preserves the fitted native rest tilt and spins
about the wheel's local axis across721 synthetic actual-loop states, while480
legacy states and30 selector cases pass. TypeScript/build pass. No real browser
validation is claimed. Existing installation failures, fitted dimensions, source
caption conflict and all16 vehicle gates remain OPEN.

Follow-up `work/cloud-va180-uv-20261001` now checks the two inherited re-encoded
meshes' actual native triangle-corner UVs against decoded Draco data. All1200
seat-base and96 column triangles have a bijective position+UV/winding match;
maximum UV-coordinate errors0.0000893511/0.0001221895 fit the declared12-bit
quantization allowance. UV seams are not averaged or wrapped. Four synthetic
controls cover cyclic reorder and rejected position/UV/winding corruption. This
narrows the earlier UV transport uncertainty only; rendered-pixel equality and
actual browser validation remain unverified. No geometry changes, all16 OPEN.

Reference research has located original TEM15 product photographs, including a
kg/cm² instrument shown with a1978 passport. A separate MPa×0.1 specimen is kept
separate. The partial independent `cloud-tem15-face-study-20261001` uses only the
clearly observed face forms/numerals/units, with all metric geometry and angles
explicitly fitted. First native pointer cap duplication failed the manifold gate;
iteration02 repairs exact duplicate seams with native Weld and retains the Curve
source. Nine closed solids,36 static physical pairs, cavity/control and portable
text checks pass; no installation, internal mechanism or calibration acceptance.
Modern official UK143A catalog dimensions were also read as original pixels but
are not silently applied to the1977 non-suffixed UK143. All16 remain OPEN.
