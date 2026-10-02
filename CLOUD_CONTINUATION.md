# MAZ543 云开发权威进度记录

更新时间：2026-10-02 16:08 UTC。**每次开始任务先读本文件。**
本文件是唯一持续更新的工程进度入口；`CLOUD_HANDOFF.md` 是不可混淆的原始
迁移/生产基线，下面的历史段落保留旧证据。当前状态和工作流以本文件顶部为准。
独立研究、有限检查、发布成功均不代表整车验收：**16项仍全部OPEN**。

## 2026-10-02 16:08 UTC：已发现的旧成果实体积压清零，完整插件外存/独立恢复证据齐全

- 余11原PNG已ddab60961d4f791460330d3301c094563b28e853（tree e7a433fd）发布。
  新空bare17对象事前全不存在，独立回取17路径13860399B全字节相同；11图共
  13648230B全部原尺寸/模式/RGBA摘要精确。无新渲染、重编码或图像转换。
- 已补齐的唯一实体为2份原生源（合计167989796B，以215有序原始块可无损还原）
  和13原PNG（合计16809648B，直接图片blob）。两源均从远端干净恢复并经官方
  Blender实际fresh-open，终验分别bf88d253/e619c37发布实读。新图片终验随本记录
  立即插件发布。总清单见cloud-generated-view-delivery-20261002/delivery-index.json。
- 已扫描MAZ生成目录及仓库内ignored outputs/work，未发现额外未交付blend/glb/png；
  参考书扫描不混成自制成果、既有已跟踪基线不重复备份。当前已识别资产积压0。
- 上传优先、插件唯一上传、完整实体+实际读回再下一项的要求继续有效。16整车门
  与历史碰撞/转向/CV/全时间线问题仍OPEN。旧GUI启动及旧trial01发送拒绝保持独立
  停止，不借本次Git成功重试；后续具体开发仍须从既有缺口和原真实模型推进。

## 2026-10-02 16:02 UTC：两原生源终验全部发布，余11原图blob已齐，继续完成外存闭环

- 门轴终验e619c37c5d28afeb14ccdec47c3a49c0b0ea86da（tree ff6943d8）15文本
  292983B已插件逐文件实读，原源67.9MB/两原PNG完整恢复、native fresh-open通过。
  前轮源bf88d253亦已完整恢复；两份唯一新增原生模型均已可从Git无损恢复。
- 其余11张原始PNG全部直接经插件返回预期blob SHA，共13648230B，最大1630258B。
  原像素/压缩/文件未改，无新渲染。新目录cloud-generated-view-archive-20261002
  提供索引、原SHA、RGBA摘要与历史证据链接；失败踏步/不同迭代明确标历史候选。
- 现在发布精确11路径的普通Git例外/索引，随后新空bare独立回取全部图并复核原
  字节与解码RGBA；终验继续插件发布后才清除待交付状态。没有重复已保存门轴2图
  或任何模型，也不把只读原书扫描放进自制工程图片。

## 2026-10-02 15:52 UTC：早先门轴原生源与两原图完整外存终验通过

- 原源67937160B/3b230c12及两张原PNG已4a4c1d45插件完整发布，142路径72.88MB
  在新空bare独立回取全字节相同，87块在干净路径精确还原。此前新检查器的全MESH
  假设错误原报告保留；依据原库存的36MESH/8CURVE修正已2b9a4687发布并24文本
  358655B独立回取。没有重做/更改源模型，也未重跑旧44姿态机械试验。
- 修正后的实际fresh-open10.904371秒exit0：10434对象、7470mesh名/拓扑计数、44门
  绑定/评估拓扑、36原始网格签名、8原生曲线结构及16driver通过，51保护输入未变。
  两原图真实字节和RGBA解码已核。原生源的唯一Git表示是可恢复的87原始块，图片
  是直接原PNG。完整终验随本进度插件发布，旧local-only标签已在旧README顶端更正。
- 已补齐两份唯一新增原生模型及门轴2图。仍有11张已生成工程PNG待按原字节补齐，
  清单在cloud-native-door-axis-20261002/asset-backlog.json；先完成这些既有资产外存，
  再进行下一开发。全车16门、6原闭门接触等机械限制全部保持OPEN。

## 2026-10-02 15:44 UTC：门轴原字节及两原图已远端完整核回，存档核验类型假设已定位

- 4a4c1d45d1f0e8a0e0d259d40944aa39415d300b（tree f13c07fe，parent bf88d253）
  已发布87原始源块/两PNG/脚本。新空bare139对象事前全不存在，独立取回142路径
  72883682B全部长度/SHA精确；干净还原67937160B/3b230c12，两原PNG及RGBA解码通过。
- 官方Blender确已打开远端恢复源，首轮11.249919秒exit1；新增存档检查错误假定
  44件全MESH而被拒。原10434对象、7470 mesh名/拓扑计数、16driver门此前均过。
  既有已发布原车库存和rod构造证明实际36 MESH+8 CURVE（4门缝闭环、4开放把手）。
  模型/所有保护输入未变；不把本次检查器错误说成新模型损坏或机械失败。
- 失败脚本/原日志/终态与精确分类准备已保存cloud-door-source-delivery-20261002。
  修正按固定名单逐件核类型/父绑定/评估拓扑，36网格签名与8原生曲线分别核。
  先发布此失败与修正，再实际fresh-open；原运动证据和16整车门/6原接触不放宽。

## 2026-10-02 15:32 UTC：继续补齐早先唯一门轴源与原关/开图，未开始下一开发

- 前轮48dbc498完整交付终验已发布bf88d2530a098de43bc851bed752def4987a4de3，
  17文本410145B逐文件插件实读，模型完整远端恢复/fresh-open链闭环。
- 全MAZ云端生成目录按SHA查重：另有67,937,160B门轴原生源3b230c12，及13张
  原始工程PNG未在当前树找到同普通blob或LFS指针。只读书页不是本项目生成图，
  不混入这批成果。逐项先完整外存验证，再进入下一开发，资产清单保留未完成项。
- 本项门轴源唯一表示为87个≤768KiB原始二进制块，全部经插件返回预期SHA；
  同源closed.png(1576059B)与open99.png(1585359B)直接原PNG blob亦已成功。
  只给这89条精确新路径普通Git例外，未改变此前LFS资产或全局规则。
- 正按正确parent/full tree非force发布，随后从新空bare独立回取全部数据，精确
  还原并实际fresh-open。本轮只核存档加载/闭门原生driver与数据一致性，不重跑
  原44姿态试验，不新增渲染/模型，不放宽16整车门及6原闭门接触。其余11张PNG
  在本项闭环后继续补齐，不能宣称所有旧成果已经全部外存。

## 2026-10-02 15:09 UTC：前四轮原生模型已完整插件外存、独立远端恢复及实际fresh-open通过

- 发布9816a3306eda83ef73165ae54e15dcd52239abbd，tree c4f78b9e、parent6e5203e，
  142路径包含128原始二进制块与14文本；插件ref/tree/parent实际核回，非force。
- 新空bare事前证实167目标对象均不存在，无alternates/本地对象来源；从公开远端
  独立读回全部167路径101791267B，逐文件长度/SHA256/Git SHA全同，前后ref相同。
  128块在干净目录精确恢复100052636B、整SHA48dbc498原blend。原42文本证据亦从
  远端包独立还原2647291B。不是只上传脚本或LFS指针，也不称直接单blend对象上传。
- 官方Blender4.5.13实际打开这份远端恢复文件，14.013131秒exit0，8522对象、132
  raw/128evaluated网格、7材料图、所有世界矩阵/父关系/原动作数据精确通过；恢复
  源/脚本/证据全未变，未读原云端候选、未保存/渲染/推进帧。完整原始终验在
  testcar/work/cloud-native-source-delivery-20261002。终验随本进度立即插件发布。
- 本项实体外存验证已通过。模型仍是有限frame0前四轮候选，时间线、转向/CV、实装
  与16项整车门仍OPEN；未完成的新候选画面和既有独立阻断没有被这次交付改写。

## 2026-10-02 14:59 UTC：128个原生二进制块均获插件SHA确认，准备完整远端恢复核验

- 当前唯一canonical表示是128个≤768KiB原始二进制块，全部经GitHub插件create_blob
  返回预期SHA；总100052636B/整SHA48dbc498保持。只有这128个精确新路径取得普通
  Git例外，既有LFS规则和资产未动。此前12×8MiB仅为失败历史，不是第二份源。
- part044曾遇技术断开，原调用终态后先查预期对象404，再原payload重试成功；
  全部128单块时间/返回SHA见part-upload-verification.json。没有盲重发未知写入。
- 此处确认的是完整实体块已创建；还必须在新空目录独立从公开远端取回全部原字节，
  精确重建原blend并用官方4.5.13实际fresh-open，随后插件发布终验。未完成前不跨下一项。
  GitHub保存的是可无损恢复的原生模型，不宣称单个blend对象已直接上传。

## 2026-10-02 12:32 UTC：轮候选文本外存已恢复，剩余只读/画面失败如实保存

- 用户新的明确上传指令后，原第7分片按原目标/原字节成功；最初6个blob先逐字节
  回读相同，没有重传。完整26路径1592703B已通过插件blob/tree/commit/nonforce ref
  发布为a0997f7d38effe4539b18a15e2b281038a4aa3c5，根树d93daa115568dbb3bf68087d3564002413d9edc3、
  parent5e36960f；全部26文件逐字实际读回。本地分支已CAS对齐该远端，原本地5508d7a
  所代表的树完整交付；此前第7分片两次拒绝属于历史阻断，不再说本阶段文本未push。
- 新100052636B、48dbc498候选实体仍仅云端，未上传LFS；脚本/验证已交付不等于
  模型实体交付。不得只传缺失实体指针或擅改attributes绕行。此前报告与GUI启动的
  两次拒绝保持各自停止，本次Git授权不被扩到那些动作。
- 原6e的9个NODES只读实际13.658638秒正常exit0：8风挡图匹配旧13-node/15-link
  精确局部条款；原前盖为14-node/16-link，实际幅值0.04500000178813934m，有3个
  SMOOTHERSTEP和COSINE。9图无嵌套/group/object/data动画或bakes；场景无animation/
  handlers/cache_files/刚体世界。8518对象身份/矩阵及源SHA保持；没有推进帧、修改/
  保存模型、导出或渲染。仅图库存，既有全场时间线门仍BLOCKED，未泛化NODES权限。
  testcar/work/cloud-textured-node-read-20261002/以普通JSON引用表保留10原文本266636B，
  包含原9记录和其清单；已独立还原所有原文逐字节核对。
- testcar/work/cloud-saved-wheel-view-20261002/保留下述未成图过程的16原文本40786B
  及清单，逐字复制校验。它没有PNG/新blend输出，也没有把失败改写为成功。

### 本地画面检查终态：2026-10-02 11:59 UTC

- 对已保存48dbc498候选的frame0单图只读检查：15.526秒呈现前保护通过，随后
  20.290秒子进程SIGKILL(-9)、wrapper1；不是240秒超时。峰RSS1992300KiB，
  0 PNG、无native最终报告，源文件SHA保持。后续exec rlimit均unlimited且cgroup
  内存事件不暴露，不能据此宣称OOM或平台时限。原失败保留，不自动重跑。
- 拟在独立云桌面终端用同源/同脚本/同画面参数对照执行上下文，但实际启动工具
  被自动审批首次及原参数一次授权重试均拒；保持停止，不第三次或换启动路线。
  view-02目录/launch均不存在，未运行Blender。没有新实体或实图，也没有重发旧图。
- 同级maz-saved-wheel-view-20261002保留呈现脚本、runner、准备、view-01原始
  ready/log/heartbeat/process及GUI未启动状态。原四轮模型构造和fresh-open结论
  不受此独立画面失败改写；当前图像/外存阻碍仍须如实保留。

## 上传优先的强制工作顺序（2026-10-02用户最新明确要求）

云电脑成果上传GitHub是最高优先级，且上传只通过GitHub插件。开始下一项开发、
建模或试验之前，必须先把本项全部成果（包括模型实体）完整上传，并实际读回核验。
上传失败时，优先修复上传和在授权范围内合规重试；不继续跨到下一项或积累新成果。
仅有文本/脚本提交、LFS指针或本地保存均不能代替模型实体的完整交付。100MB前轮
候选实体尚未上传，所以本项仍未完成；当前工作只处理待发记录、插件实体能力与
合规可恢复的上传方案。禁止换用CLI、用户本机中转或其他存储方式冒充插件上传。
仍尊重安全拒绝，不用改编码、代理、其他agent/入口迂回；必需权限或能力缺口只报
精确阻塞。未经明确决定，不擅改既有attributes/LFS规则或伪造实体已上传。

## 2026-10-02 12:54 UTC：只处理本项完整实体上传，不再跨新工作

- 剩余9图只读/未成图记录已正常发布df82b40b75942a3f6236ae7aa35f71f88beb6e35，
  28路径265513B、tree dc9f8b10、parent a0997f7，逐文件实读相同。本地已对齐。
- 本项模型100052636B=95.417629MiB，未超过GitHub普通文件100MiB上限。不能再
  把阻碍归咎于文件超过100MiB。现GitHub插件无LFS或release资产上传动作，但
  create_blob支持标准Base64 API输入，fetch_file(base64)已实读现有192420B WASM
  并全字节核同；133403516字符的完整模型请求承载能力尚未验证。
- *.blend LFS来自571b25b的工程迁移约定。当前已审定的唯一方案是只为这一新候选
  精确路径使用普通Git二进制例外，完整.blend原字节一blob上传、确认后才与例外/
  文档原子非force发布并独立回取；不改既有LFS资产，不在仓库放编码文本/碎片。
  详情testcar/docs/PLUGIN_ENTITY_UPLOAD_20261002.md与对应plan.json。
  目前attributes未改、实体未上传、整项未完成。没有据此恢复被拒的Slack/GUI动作。

## 2026-10-02 13:22 UTC：整文件插件请求实测IPC超限，当前只处理无损实体交付

- 原100052636B完整缓冲/整SHA/133403516字符Base64已核，通过create_blob发起时
  实报code-mode IPC frame length 133403855 exceeds 67108864 bytes。不是GitHub100MiB
  限制，也不是安全审批拒绝；预期单blob61f801a0随后插件查询404，确认不存在。
- 当前已选择唯一canonical有序原始二进制parts方案：12块，每块≤8MiB，合计恰
  100052636B，整SHA48dbc498不变。testcar/outputs/cloud-textured-front-wheel-20261002/
  保存manifest、原始.bin块和严格还原器。GitHub表示将是可无损恢复的完整原生源，
  不是直接的单.blend blob，不是Base64文本/缺块pointer或另一个冗余备份。
- attributes只为这12个精确新路径加普通Git二进制例外；原*.blend/其他LFS全局规则
  及既有资产不变。还原器7项完整性控制已过：完整、缺块、损坏、乱序、整SHA错误、
  不安全路径、既有输出保护。先全量校验，写入再校验，原子安装，不覆盖原文件。
- 本提交准备仍不能称完成交付：必须全部块经插件上传、独立远端取回并在干净目录
  精确还原原字节/SHA、实际native fresh-open通过、终验记录再次插件发布，才允许
  下一项。当前不继续设计、建模或机械试验；旧Slack/GUI二拒保持停止。

## 2026-10-02 14:24 UTC：首8MiB调用已取消且对象404，恢复为128个更小完整二进制块

- cell545的首块8MiB已完整准备11184812字符并进入create_blob，后在约2897.7秒
  等待后被中断；实际工具终态为user cancelled MCP tool call，不是安全拒绝。
  原调用已Script completed，预期7b35465a blob插件查询404，确认0块成功，未盲重发。
- 同一canonical原字节表示技术适配为128块、每块≤768KiB；整100052636B/SHA48dbc498
  不变。此前8MiB准备清单仅作为失败过程文本保留；实际源唯一表示采用当前128块。
  attributes例外仅覆盖这128个精确新路径。还原器/schema/全量完整性门不放宽。
- 每次插件请求须落开始时间、目标SHA及确认结果，配进行中状态；不再让一个调用
  无状态挂近50分钟。所有块上传、独立回取、干净恢复和native fresh-open及终验
  发布之前，本项仍未完成，不开展下一工作。

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
- 最近已核实发布的HEAD：`ddab60961d4f791460330d3301c094563b28e853`（剩余11原PNG与完整索引17路径已全字节回取/RGBA核同；两原生源已完成恢复和终验）
- 该提交根树：`e7a433fd70ca1c5ba47199a53e96d6a961d71f49`
- 插件原生Git对象发布后远端ref/tree/parent及文件字节已核实，本地分支已对齐
- 原迁移分支保持：`4f28bd4618ca7e272f6049b9f615821b8e0bb8f1`
- `migration/cloud-handoff/DELIVERY_STATE.json`确认完整快照，无待迁移文件；
  包含3484个实物源文件及100个原Git基线文件。稀疏检出不等于这些历史文件丢失
- 原生四门控制45文本及关/开图证43文本均已逐个远端读回，两张真实PNG已
  授权渠道上传且文件/线程回读。踏步真实位置失败117文本已逐个读回；失败侧图已授权渠道交付及文件/线程回读。
  失败侧图32文本与下框修正75文本均已完整逐个读回，阶段报告已授权渠道
  发送并回读。原短下阶6组交叉的22文本已实读，阶段报告也已回读；原书恢复
  记录的2文本已实读。本轮已直接读1977原书相关页像：A型图2与驾驶室图101/102
  支持下阶定性区域和两踏面/三支承，2文本和阶段报告均已实读，尚无毫米安装尺寸。
  本轮阻止packer无声继承门14bit旧流，真实Textured门内存18bit有限误差通过；
  **旧GLB未改变，仍FAIL**，不是已重导出/上传或网页验收。39文本与阶段报告均已
  实际读回。手册5扫描单元及VHÚ馆藏照片补查2文本也已实读，未取得新下阶硬点。
  本轮读当前母版前4轮104接口，固定现有硬点无法闭合轮顶向外1°；
  21文本与阶段报告已实读。随后0°原生父链/鼓旋转候选两次均未通过：
  01旋转未实际发生、其PASS已撤回；02真实旋转首样本刚体误差210.655µm，
  不放宽20µm门。失败17文本与阶段报告均已实读；首站双父链诊断已确认
  同两字模在原源中就超差，共用186件整条观察完全一致。鼓已测到真实随转的
  有限收益，但整个候选仍FAIL。原生Apply已在72个字模上执行并保留Solidify和源FONT；
  中性776件与8个真实旋转/4次还原记录通过，但120秒超时发生在最终外部对象/
  源SHA/总报告完成前，超时证据已完整发布。随后同范围索引优化实际101.482秒
  exit0，最终9626外部矩阵/源SHA/字体保护和负控表已落盘，原生限定范围通过。
  没有保存新模型/GLB；跨两次fresh-open的301组合UV/材料hash不同，原因待定位。
  文档不能预先包含自身commit SHA，应以实际远端ref/tree核验为交付依据
- **当前2.2m下踏步拟合布局安装FAIL**：第二踏面侵入8个原轮胎/轮毂/轮辋对象。
  下框raw-index闭合不代表有效实体，已见重合点/零面积面；其solid有效性UNKNOWN。
  不安装、不移轮胎、不删旧件；原生下框构造已有独立修正，仍须按真实下阶
  基准与参考重新定位，不能把原理/拓扑通过当实体或安装认证。
- **原有短下阶也不能用作合格安装基准**：原curve与胎体/3个vent命名细节件、末横条19与
  胎体/0.635轮环，共6组严格非共面表面交叉。没有由此选定替代尺寸或挪轮。
- 新原生四门轴控制候选仅在云工作区：`MAZ543A_Native_Barrel_Axis_Controls.blend`，
  67937160B、SHA `3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f`。
  已保存并独立fresh-open通过，但**LOCAL_ONLY_LFS_BLOCKED，不在GitHub**；只保留一份，
  原8e962d6母版不动。本候选仅修原生门控制，未合并140头部修复或踏步布局
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

## 2026-10-02 10:59 UTC：真实Textured前4轮已保存，独立fresh-open通过限定范围

- 原6e源实际构造52.730708秒exit0，独立重新打开12.253417秒exit0，均确认正常
  子进程终态、未超时、原99960163B/SHA不变。已保存真正可编辑候选，并非只完成检查。
- 新增4个原生EMPTY关节框在原主销轴上；原carrier与固定制动器连接对应关节框，
  原4鼓连接对应spin，共12条原父边变更。4spin从QUATERNION改XYZ，与原Euler
  曲线字段一致；8旧父坐标action只分离并设fake user保留，全部552原action关键帧/
  handle数据未改。没有Apply已烘焙字模、造替代FONT、手写网格、删件或挪其他系统。
- 128移动网格中性最大顶点误差0.070460µm<原2µm门；本地几何、UV、实际corner/
  vertex/polygon法线、已读拓扑与材质保持。4轮各0.731/π共8个实际属性旋转，最大
  刚体误差0.315052µm、圆周路径误差0.201747µm<原20µm门；固定制动器位移0，
  鼓/胎均实测运动，8样本后4次恢复精确。有限样本不等于连续机械净空或运动证明。
- 8518原对象保留，8358范围外中性矩阵完全不变，82原材质、132已读raw保持。
  新文件fresh-open得到8522对象，全部保存矩阵/父链/552action数据、132raw/128
  evaluated记录与7个所选原shader图精确回读。保存前全部15个FILE图像已打包，
  Render Result为VIEWER且无需外部文件；没有重新渲染或更改原图像资源。
- 新文件仅云端：maz-textured-front-wheel-fixed-20261002/fixed-01/
  MAZ543A_Textured_Front_Wheel_Parent_Study.blend，100052636B、SHA
  48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea。
  **LOCAL_ONLY_LFS_BLOCKED，不在GitHub**；原生脚本/全证据可重放，新模型实体没有
  上传路线，不能发布缺失实体指针或把binary改编码塞进Git文本。生产默认不变。
- 全过程固定frame0，未执行原全场31/91时间线；9个原NODES资格仍BLOCKED，旧
  trial01失败保留。切换XYZ是实际模式修复，不宣称时间线/转向/CV/悬架安装通过。
  原exact132 MetricUV intake仍BLOCKED，4支承的原evaluated UV差异单独保留；
  其raw、位置、已读拓扑与真实法线受保护，未放宽通用UV门。16整车门仍OPEN。
- testcar/work/cloud-textured-wheel-fixed-20261002/保留42文本2647291B，两个进程
  原生日志/准备/终态、实际构造与fresh-open脚本、原材料/动作记录和独立结果核算。
  普通JSON表已独立恢复全部42原文及final清单逐字节核对；未包含模型/PNG/GLB字节。
  下一项做保存候选真实可见画面，并继续查未分类前盖图/后续导出与网页父链接入。

## 2026-10-02 10:43 UTC：Textured真实修复前置门拒9个原NODES，构造尚未开始

- 首次真实Textured前4轮修复trial在10.756761秒child/wrapper1终态；CPU2，未超时，
  子进程退出与原6e SHA不变均实核。已完成原160对象/128网格的身份及逆依赖intake；
  新增全场时间线前置门在原舱盖/风挡9个NODES处拒绝，未创建joint、改父级/旋转
  模式、改action、保存、导出或渲染。不是完成模型，不把失败回写为PASS。
- 拟定的原生操作只新增4个EMPTY关节框、重接原carrier/固定制动器与4鼓、保留但
  分离8个旧父坐标action，并把4spin设为XYZ以使用原Euler动作；不Apply已烘焙的
  72 Textured字模，不构造替代FONT。实际几何/动作样本、保存和fresh-open均未到达。
- 拒绝对象为BL_Front_cover_front_panel，以及左右各一的BL_Front_windshield_gasket、
  BL_Front_windshield_glass、TOOL_Windshield_gasket_inner、TOOL_Windshield_opening。
  不默认白名单NODES；下一步静态核已有精确cab配置和实际图的时间/Simulation依赖。
  旧配置的stationary VIEWPORT资格不能直接扩成全场时间线资格。
- 为相对资源恢复原路径语义，已把原6e已有LFS缓存实体逐字节恢复到其正确跟踪路径
  testcar/outputs/cloud-va180-textured-20261001/MAZ543A_Textured.blend；99960163B/SHA相同，
  工作树保持原跟踪内容，没有认证/网络调用或新增LFS。没有新二进制资产。
- testcar/work/cloud-textured-wheel-trial01-20261002/保存24原文本1674758B，包括失败
  原生日志、输入、脚本、完整intake和进程终态；普通JSON引用表独立还原全部文本及
  final清单并逐字节核对。原exact132 UV失败继续BLOCKED；16项整车门仍OPEN。

## 2026-10-02 09:43 UTC：5件最小诊断量化MetricUV差异，真实法线稳定

- 仅原4kingpin+brakes_0003，原6e源一次打开、frame0三轮读；13.919930秒child/
  wrapper0，确认退出、未超时，原SHA不变。没有修改/关闭modifier，没有Apply、
  改父级、保存/导出或渲染。是完整诊断采集，不是机械或画面验收。
- 四主销跨evaluated mesh返回的MetricUV有限数值变化为1–4 ULP，最大绝对差
  2.384185791015625e-7 UV单位，不是NaN/Inf或符号零变化。阶段0的8组轮次比较
  共2824个标量变化，全部3读取阶段共8472个变化记录；不是唯一loop数量。独立
  从每条浮点值重建float32位型，逐条核对有限值绝对差和同符号uint32差，均相符。
- 三轮的完整已读拓扑（含edge端点、loop→vertex/edge、polygon区间、triangle→
  vertex/loop/polygon）、位置、真实corner/vertex/polygon normals、smooth/sharp/
  seam与元数据逐位保持；五件raw前后保持，8518原对象身份/矩阵、材质保持。
  同一evaluated mesh内，初读UV、读三角拓扑后、读真实法线后均相同；bulk与直接
  RNA逐项读取float32位型相同。鼓对照无UV变化。不能唯一定位某个modifier/具体
  舍入实现，也不能把三个样本当所有未来评估的误差上界。
- 已实核4件共用S543_machined_steel的唯一5-node/4-link图：Object坐标明确接
  Noise.Vector→Bump.Height→Principled.Normal→活动Surface，无Image/UV/Attribute/
  Group节点或Displacement连接，Anisotropic=0。图与首次intake记录完全相同，
  当前shader不读MetricUV；这仍不等于已验证图像一致或可放宽任意UV要求。
- 首次6944344的exact-UV FAIL不改为PASS，不移除4个支承件、不添加通用UV容差
  白名单，不把本结果外推为Master301条摘要同因。后续Textured父链候选将保持
  原raw数据/所有部件，继续独立记录原4支承评估差异，并验证实际128个拟移动
  网格及支承的几何/法线/矩阵；中性/刚体几何原2µm/20µm门不放宽。
- `testcar/work/cloud-kingpin-uv-repeat-20261002/`保存23原文本5090519B，含
  每个变化标量及loop/vertex/edge/polygon身份、真实法线/拓扑摘要、原生脚本/日志/
  终态与独立数值复核；普通JSON引用表已独立恢复并逐字核全部23文本及源清单。
  没有把blend/glb/png编码为文本，也没有新增LFS实体；16项整车门仍OPEN。

## 2026-10-02 09:04 UTC：真实Textured轮组只读，首次UV复读门仍BLOCKED

- 单次真实6e406e源读取15.979524秒，child/wrapper exit1、未超时、确认退出。
  173结构对象/132几何摘要及全8518对象简要逆依赖已读；源99960163B及SHA前后不变，
  没有Apply、改父级、保存、导出或渲染。frame0显式求值，不是任意时间线资格。
- 72前轮字模全是MESH且modifier=0，原SOURCE_FONT/profile在该Textured内不存在；
  旧构造脚本确实用evaluated mesh快照导入，不应复用Master的72 Apply。拟移动子树
  精确160对象/128MESH，另4kingpin及其支承/祖先合计173结构；不套Master776计数。
- 128拟移动几何在同进程复读保持；8518对象身份/矩阵、原材质记录保持，源SHA保持。
  限定逆依赖扫描0外部引用、0不可读项；包含modifier ID-property覆盖、constraint
  嵌套target、对象/数据/material/world driver与node引用，未知粒子/pose/非简单
  driver显式拒绝；不是任意插件handler/缓存/非ID链或渲染位移的普遍证明。
- 唯一拒绝：4个S543_i_steering_kingpin的evaluated authored_geometry_uv和uv_layers
  摘要在同进程复读时变化。其他记录的几何位置/索引/拓扑/材料字段不变；法线本项
  未记录，第二次完整摘要及UV数组也未保存，因此不能给数值幅度或根因。首次
  READ_ONLY_INTAKE_BLOCKED保留，不移除4件、不白名单UV、不放宽原门。
- 四原简化鼓实际均148顶点，100环顶点拟合半径0.335000023m、宽约0.130000101m，
  圆心/残差及4kingpin竖轴符合原作者参数的2µm门；不是厂家鼓内腔/轴承配合认证。
  原850导出名完全一致，当前参考的261几何/321pose原本没有轮组原生数据。
- `testcar/work/cloud-textured-wheel-intake-20261002/`保留准备与唯一实际读取27原
  文本1673455B、执行脚本/输入/终态/原日志；普通JSON表可精确恢复所有文本与源清单，
  已独立逐字核对。没有新增模型资产、图片或LFS实体。实际运行前后观察HEAD2a825d4，
  准备引用的原证据仍固定Git3a7bd132，二者明确区分。
- 下一项只聚焦4kingpin实际材质的UV使用路径及读数差异/法线，不重复全车读取。
  原首次失败保存后再设计最小诊断，不能由这4个Textured对象推断先前Master301
  摘要同因；父链移植、导出合并/网页、原厂外倾/转向CV及16项整车门仍OPEN。

## 2026-10-02 08:37 UTC：修复网页缺轮时的轮站错配

- 原viewport跳过缺少的carrier后，把压缩数组序号当作原轮站：真实生产和cab候选
  GLB节点图中移除首站，下一站位置错2.375m；移除站3，站4位置错4.065787m。
  这是缺失部件条件下实际旧循环的错误，不是现有完整资产已经缺轮。
- 新`lib/nativeWheelBindings.ts`按8站原carrier/spin/brake身份完整核对，明确保存
  station；缺件、重名、错误source侧或非旧父链在任何native树替换之前抛出。
  `vehicleViewport.ts`已实际接入，逐帧使用station而非数组位置；正常旧父链保持
  原位置/旋转公式。尚未适配的新joint父链被明确拒绝，不能再先清空suspension
  然后错误挂接。没有启用虚构候选入口，也没有改变当前模型实体。
- 真实生产4aa0a228（371节点）、cab fde04（850节点）和相同fde04的axis模式，
  各97帧共200887次世界矩阵逐系数比较，与旧循环正常行为差0；source数组和binding
  数组分别重排仍差0。171个缺件/重名/错误侧/新父链负控全拒绝，失败前原target树
  parent/TRS和renderedRoot未改。包含原故障见证，未解Draco或模拟浏览器截图。
- CPU2有界JS检查4.184秒、完整tsc 2.723秒、聚焦lint 0.917秒、前端build 20.338秒，
  全部exit0且未超时；构建仍有原环境代理提示、插件耗时及大chunk提示，原日志保留。
  这是代码/节点数据验证，未运行浏览器/GLTFLoader/GPU，不称网页验收。
- 实际故障路径继续用已有回调：主线程仅onError，原生成模型仍显示并动画，
  nativeLoaded=false且不发native ready；worker异步fatal停止两个worker并清理
  API/canvas，不自动回退主线程。本项没有改该产品流程。
- `testcar/work/cloud-wheel-binding-20261002/`保留检查报告、历史两模式记录和
  最终三模式记录、CPU限制/终态、构建/类型/lint原日志；验证脚本在
  `scripts/verify-native-wheel-bindings.mjs`。旧review入口只保留已有证据边界。
- 下一项真实Textured轮组只读身份检查：其72前字模来自原生evaluated mesh快照，
  现有保存清单无source FONT/原profile，不能直接照搬Master的72 Apply。将核实际6e
  数据与依赖后再决定父链移植；原厂外倾、转向/CV、连续净空及16项整车门仍OPEN。

## 2026-10-02 08:17 UTC：原生胎字放大观察完成

- 同一站0中性原生重放109.641492秒exit0，实际HEAD954b9c4，方法验证仍属于66085d7。
  原8e962d6源SHA前后不变；本次只18字模/1站操作，完整4站资格和全场景依赖保护保留，
  不把一图作为新的4站机械验证。10246固定原矩阵最大误差0；20见证还原0；18源FONT/
  Solidify/可见性和原材料/世界/对象身份最终检查通过，cleanup_errors为空。
- 与先前全轮中性图相比，相机世界矩阵、灯光、材料、几何、分辨率和Cycles设置相同；
  仅正交范围2.60m改为0.5432866216m，并做原生camera shift取景。实际1100×1000
  图中1500x600-635与VI-203多数轮廓可读，末端仍被原车体件局部挡住。短放射杆与字形
  明确是不同细节。不因先前单字约3–13px就扩大或重做字形；本图也不证明原厂字体/
  尺寸、全字无遮挡或唯一渲染原因。原短阶干涉、外倾0°及简化鼓继续保留，16项OPEN。
- 原PNG1105956B，SHA915c9d6985ad560e61c2e7ffe0c8ba02b815ff7699d0d65307eb1cb4fec28fa6，
  已经授权渠道交付并实际回取：返回编码少511B，但全部RGBA像素完全相同。图片仍
  不在Git/LFS；没有新blend/GLB，不发布缺失实体的LFS指针。
- `testcar/work/cloud-tyre-letter-closeup-20261002/`保存19原文本1788790B及源清单，
  用可读脚本/普通JSON表保留精确原字节。单独进程恢复并逐文件对照全部19文本及清单
  完全一致。原始日志、心跳、源/runner/plan和原生终态均保留，不包含图片实体或私有
  交付收据。取景前准备文档精确复制为reviewed-plan，明确它是事后归档副本。
- 下一项：处理已定位的候选轮组导出和网页装配/绑定兼容。旧导出排除S543父层，旧网页
  会清空suspension，且缺前轮时会压缩轮站索引；必须在独立候选范围改正，保持生产
  资产/入口与原几何，先核真实Textured身份再构造，不默认Master对象等同Textured。

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
- 已正常从公开仓库重新稀疏clone到同名Maz543目录，现已对齐铰链轴诊断提交bcb05506；普通Git对象
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

## 最新完成小项：运动pivot与实际铰链圆柱不同轴

145件定位已发布101508f，9文本文件1004451B逐字回取/完整树一致。此前约1MB
单tree.content请求长时间无结果，4011秒后明确取消；期望tree只读404、远端ref仍旧。
随后按原字节逐blob+小tree引用成功，未删证据或重跑定位。以后逐调用及时yield，
异常数分钟未返回先报阻塞并查终态；不将大批次等待算作有效工程进展。

`scripts/inspect-door-barrel-axis.py`只读同母版，实际四门各三个铰链圆柱：每件原始
48顶点/两个24点圆环，轴向主成分、圆环半径及共轴检查通过；评估质心与原始质心
差小于0.055µm。每门三个圆柱轴彼此共线，但与运动Empty轴平行偏置约70.342mm，
组成是纵向18mm、横向68mm。运动99度时实际圆柱中心从闭门位置位移约106.977mm，
说明它们绕偏置轴公转，未围绕自身共同轴转动。

这是现有模型内部运动/铰链几何的不一致，不是厂家轴尺寸测量。原脚本使用
start+0.018与side*1.548生成圆柱；旧rebase只将Empty的X移到start，侧向仍1.48，
也明确只保证网页/原生一致与闭门外形。此次测量没有改动任何模型或删除车体。
证据`work/cloud-door-barrel-axis-20261001/`含原始/评估轴、圆环、每门五姿态中心轨迹、
来源脚本SHA与原生日志。4.5.13实际13.974秒/峰1737248KiB，源SHA前后相同，无新LFS。

## 最新完成小项：共同圆柱轴的内存运动对照

轴诊断bcb05506已发布并逐字回取。18:18插件读取曾同时HTTP401、报告发送取消，
18:19–18:50中断不计开发；恢复后只读确认ref/完整线程，未重复诊断或不确定外部写。
本项`testcar/scripts/trial-door-barrel-axis-motion.py`复用原轴80例的已发布SHA证据，
只在内存把开门矩阵改为绕实测圆柱共同轴，闭门basis直接精确复制，源模型不保存。

实际4门×0/15/45/75/99度共20姿态：原轴表面接触实例80→共轴试验6。全部15/45/75/99度
样本零BVH表面命中，闭门原有6例完全保留（四门对cab_0063、两后门对侧铆钉）。
145固定件顶点/三角索引与10386个其他对象世界矩阵全部精确保留，44门件闭门及最后
恢复后几何精确相同。铰链圆柱中心最大漂移0.334µm，不再发生约107mm公转。

4.5.13实际16.873秒/峰1726008KiB，无规则违反，源SHA未变。证据
`work/cloud-door-barrel-motion-trial-20261001/`含逐姿态对照、保持检查、中心轨迹和日志。
这只是内部运动一致性试验，没有新母版、GLB或网页行为修改，亦无新增LFS。
**有限样本零命中不证明连续净空/排除包含体**；旧261件的原轴证明不能自动用于新轴。
其他门、82隐藏件、24父树外几何和厂家坐标/真实铰链内构仍开放，16项不变。

## 最新完成小项：新轴的完整角度冻结区间定位

共轴内存试验在19:26恢复插件发布为a8e72d60，完整tree/parent/ref及5文件实际回取
逐字相同，本地对齐；前次tree已存在而commit未推进，不重复创建tree或运行试验。

`testcar/scripts/audit-barrel-axis-frozen-intervals.py`从实际frame0冻结顶点，以发布试验
同一轴点和`world @ (p + Rz(theta) @ (local-p))`重算四门带方向0–99°闭区间，
涵盖44件×(261旧舱件+145原驾驶室件)=17864对，无重复或漏对。

- 17812对以保守顶点/三角凸包区间包围分离；52对未知，每门13对，全部属于新增145范围
- 原261件对新轴的11484对也均冻结分离，但不能挪用旧轴证明；本次独立重算并保留证据
- 六个闭门表面接触候选全部留在含0°的未知区间，没有把闭门接触或重叠包围判为通过
- 最多6层/127格，每个细分对保留所有分离及未知子区间；完整范围被覆盖，预算耗尽仍未知
- 两侧包围各外扩20µm。此值仍不是已推导的Blender全角浮点误差界；新增145件未自动取得
  旧261件的严格原生依赖资格。只称CONDITIONAL_BARREL_AXIS_FROZEN_INTERVAL_LOCALIZATION_ONLY

4.5.13实际11.953秒/峰1712072KiB，源码SHA未变，不改/保存母版、不新增LFS。
证据`work/cloud-barrel-axis-frozen-intervals-20261001/`含4门逐对/子区间、输入SHA、
综合报告及进程日志。首次相对脚本路径启动没有载入脚本却退出0，失败日志/记录单独保留
在attempt-01-relative-script-path；正式运行改绝对路径并启用--python-exit-code 1，
读取报告终态而不只信进程退出码。独立轻量复审用另一套标量极值枚举1000组，
核完整配对、58个细分对/2204叶覆盖、输入SHA与6闭门保持；系数式与独立旋转式
最大差8.88e-16m。可重放脚本为scripts/review-barrel-interval-evidence.py，结果为
同目录review-result.json；不重跑Blender、不冒充原生几何重新提取。
16项仍OPEN，无原生全连续净空/生产/网页验收。

## 最新完成小项：闭门接触的原始组件来源定位

新轴17864区间定位在19:40完成发布05e1a49，完整tree/parent/ref及13文本实际回取
逐字相同。此后仅通过正常官方LFS读取恢复既有mechanical-seed.glb，8588120B，
SHA-256为5c5849b68a5fa62e903b46b5554b8eb942495eabb3a12cb26caf24742cd9681c，
不是重新生成或新上传资产。当前lib/maz543.ts门位置与该历史seed的manifest不同，
不能用现在的TS脚本重新生成后冒充原始输入。

`testcar/scripts/inspect-closed-door-contact-components.py`只读8e962d6…母版frame0，
重新得到原6个闭门表面候选、190个三角对，逐例数量与已发布试验完全一致。
记录原始索引连通组与仅数学意义的精确重合坐标组，**不在Blender焊接/拆分任何对象**。

- cab_0063当前1536个定向三角角点逐字精确匹配历史seed中的同一对象；16个坐标连接组
  各自完整匹配一个源组。源17组中剩余96三角/148顶点组的位置也单独记录，这只说明
  不在当前这一个对象中，不是整车丢件声明。100µm角点破坏和反绕序负控均拒绝
- 四个门壳的闭门接触分别落在cab_0063组1/2/9/10，纵向中心约-4.18/-3.89m、
  横向中心±1.455m，高度1.23–1.45m。真实两层各24点圆环及两端中心验证支持
  约50mm直径/220mm高的垂直24棱圆柱几何身份；这不是厂家零件语义/安装尺寸认证
- 两个后门还分别命中各自side_rivets的50/51/52三个坐标连接组，共6个侧铆钉形状。
  全部命中三角索引、组件包络与当前原始/评估几何精确一致记录保留

正式4.5.13运行10.252秒/峰1737568KiB，母版与seed的SHA前后不变。证据在
`work/cloud-closed-door-contact-components-20261001/`。首轮只凭包络叫圆柱的不足记录
保留在attempt-01-bounds-only-shape-label，正式版追加真实圆环验证后才使用形状名称。
结果仅CLOSED_SURFACE_CANDIDATE_COMPONENT_PROVENANCE_ONLY：没有删柱、移车体、挪铆钉、
转门或保存模型，没有新增LFS、生产替换、渲染/网页或整车验收；16项仍OPEN。

## 最新完成小项：新增145件严格依赖拒绝与真实节点图清点

来源定位5ce3f03在19:51完成发布，8文本实际回取一致。本项
`testcar/scripts/audit-added-cab-dependencies.py`从已复审的旧checker用AST选取原样的
三个guard函数，只更换被审范围为145新增固定对象及实际递归引用，不修改旧checker。
实际153对象/上下文检查，137个选定对象无issues，8个选定对象受10条拒绝影响：
两顶盖SUBSURF、4玻璃/密封件NODES，以及Boolean所引用的4个门窗切割工具NODES。
因此严格结果为**SCOPED_ADDED_CAB_DEPENDENCY_FAIL_CLOSED**，不是145件通过。

8个真实节点图各13节点/15连接，当前读得Position、SeparateXYZ、Math、CombineXYZ、
SetPosition及Group输入/输出；Math运算含SUBTRACT/MAXIMUM/MULTIPLY/ADD。
完整节点类型、插口默认值、链接、修改器设置、ID指针及动画信息留证。
这些清单**尚不等于已证明节点图静态资格**，没有默认允许NODES或SUBSURF。

证据`work/cloud-added-cab-dependencies-20261001/`。正式4.5.13实际10.064秒/
峰1705828KiB，母版SHA不变、没有几何变更/保存/新增LFS。首轮读取SUBSURF不支持的
IDProperties时报错并退出1，独立保留attempt-01-subsurf-idproperties；只修序列化，
没忽略依赖拒绝。52未知区间、六闭门接触及16项OPEN均保持。

## 最新完成小项：实际开发入口的共轴开门修复

145依赖fail-closed已发布0116ef69并7文本实际回取一致。本项在
`lib/reviewVehicleAsset.ts`增加独立开发选择`?asset-review=cab-va180-axis-v1`，
继续读取原fde04e48…GLB全部24743400B，不新增/重编码资产。实际逐帧绑定在复制原
source姿态之后执行实测原生轴的`p-R*p`位移，四門闭门位置保持原样。旧cab-va180-v1
可做原运动对照；生产、非开发环境和render-worker继续回退既有生产选择。方向盘
仍使用已验证舱侧位移与绕拟合柱轴的姿态修正。

`verify-barrel-axis-pose-binding.mjs`运行真实createMAZ543/model.update及实际绑定语句，
读取原GLB节点树，并实际Draco解码20个门网格，不以简化物体替代资产：

- 2069状态含四门分别0–99°每0.25°、混合姿态、反复开关；闭门30816次节点世界矩阵
  与旧绑定逐位一致，826其他节点共1708994次世界矩阵/显示标志对照精确一致
- 12个实际铰链组件各192个独立坐标/380三角，与原生评估计数一致。原生轴常量未改，
  最大质心漂移12.509µm，仍低于原20µm运动门；旧绑定负控复现106.983mm公转
- 独立矩阵公式最大差4.44e-16m。候选GLB原字节SHA、source门姿态、5类旧入口运动
  保留；这只是数值状态检查，不是原生/网页全连续浮点或净空证明
- 暴露并保留既有门网格14bit量化：位置范围1.26999998m、步长77.519µm，包络尺寸
  与原生偏差最高54.479µm。**原20µm包络传输检查仍失败，未提升为通过**。
  首轮误用包络中心/尺寸匹配导致0个组件识别，已保留并在最终脚本继续复现该失败；
  正式识别使用实际192点质心、380三角与量化网格限定组件，未放宽20µm运动门

原721方向盘/480旧绑定、36选择器条件和6种真实导出器元数据fixture通过；针对本项
三代码文件lint、tsc及vinext build退出0（build119.802秒）。原机械源码与实际pose
block保持字节一致，6个闭门接触、52未知区间、继承压缩误差及16项OPEN继续保留。
证据`work/cloud-barrel-axis-web-20261001/`含所有终态/失败识别/量化摘要/构建日志。
**没有浏览器实际画面验收、原生母版保存、生产晋级、新LFS或部署。**

## 最新完成小项：精确局部节点配置与406固定件依赖资格

开发入口修复0b9d029b已发布，27文本逐字回取一致。发布时整树核对先发现build.log
的5个裸CR被通用文本读取改成LF，错误临时tree没有创建commit/ref；改用原始bytes的
普通Git base64 blob后完整根树匹配才发布。**今后日志/文本发布读取必须保留原字节，
使用read_bytes().decode而非通用换行read_text；这不改变任何LFS属性或实体要求。**
两份零字节日志也已通过逐文件空内容读回确认。

本项`cab_static_local_modifier_guard.py`只允许固定源中10个精确修改器配置：
8个局部位置数学节点图及2个固定视图顶盖SUBSURF。配置文件在
`reference/cab-static-local-modifier-profiles-20261001.json`，SHA固定为
e2893870a7edf3243d0f75c0fd0b4849b9f121eeec99ec2264cf3f67dae7f762。
逐一核真实RNA的对象/修改器/节点组身份、全部节点和默认值/插口/15链接、动画、
ID指针、嵌套/未连接节点、缓存/修改器输入、场景简化和执行handler。不是按类型放行。

`cab_reviewed_dependency_context.py`绑定未修改的旧checker完整SHA，只在固定上下文
那一处unsupported分支接入此窄规则，旧对象/祖先/Boolean/移动层级/按钮全部规则保留。
空白小场景10正例及49局部负例通过；另外原递归组合拒绝动画父级、移动Boolean操作数
和未知上游修改器。最初小场景构造探索不是源模型验证；正式集成fixture可独立重放，
生成的微型链接库只放临时目录，不作为待上传模型资产。

`audit-complete-cab-static-local.py`随后真实只读相同8e962d6…母版，406固定件+44门件
递归582对象/上下文，10个精确局部配置全部匹配，0个issues，结果
SCOPED_406_FIXED_44_DOOR_DEPENDENCY_ELIGIBLE。frame0、按钮释放、VIEWPORT，factory-startup
且禁用自动脚本。实际10.109秒/峰1713524KiB；耗时不是隔离性能基准。原生源SHA不变。

证据`work/cloud-static-local-cab-20261001/`含fixture、组合负控、真实母版报告、运行
日志及模块SHA。依赖资格只解决这组场景的依赖前提，**不解决52个重叠区间、六个
闭门接触、隐藏件/其他门/父树外对象、渲染或网页精度**；16项仍OPEN，无新LFS。

## 最新完成小项：侧壁低穹头支承与门洞投影

精确局部依赖扩展4488fac8及回放文档修正800738a2已发布，最终13文本原字节回取一致。
`scripts/inspect-side-rivet-support.py`只读母版：两侧各75个低穹头，每个24顶点/38三角，
基圈8点加中心共9条法向射线。整体与各自side_monocoque沿Y包围轴相隔
11.999965mm，足以证明**与这个命名侧皮不直接接触**，不外推到未查零件。

- 各侧72个头的9样点均命中固定侧皮；其中70个样点处于同一平面，2个跨倒角
- 各侧50/51/52号组件的9样点全部穿过侧皮空洞而命中后门壳，恰对应保留的闭门接触
- 平面候选共140个；10个没有同一平面支承。**9点采样不是完整基圈面积覆盖证明**，
  不可据此直接删件、改孔位、宣称装配合格。下一步先核八边形全足迹覆盖再做原生贴合候选

同阶段已实际看过Michael Benolkin拍摄的Duxford右/左舱近照（Cybermodeler图07/12），
定性支持：两门下方有连续固定门槛带，长踏步及三处可见吊挂位于其下，固定紧固线
位于门缝外侧。部分吊挂有绞纹/套筒外观，柔性钢丝绳只是待核假设。两图是同一馆藏
MAZ-543车辆，不能证明1977 MAZ-543A批次、尺寸、孔数或头型；未公开转载源像素。
来源URL/作者/SHA/边界见reference/cab-sill-step-rivet-source-20261001.json。

证据`work/cloud-side-rivet-support-20261001/`。正式4.5.13实际10.748秒/峰1723880KiB，
源码SHA不变、不改任何几何/可见性/父级/闭门姿态。正/负射线控制通过，逐点命中面
和组件关联保存。16项仍OPEN，无新LFS。

实际云Chrome工具可用，但打开开发URL被客户端以ERR_BLOCKED_BY_CLIENT拒绝，页面
未载入，故开闭、重复操作、旧/生产对照与截图均没有运行。8个既有GLB实体共
100016672B已核SHA/大小，不等于网页通过。原有界服务命令中断exit130，后续命令
见生成锁且HTTP连接拒绝；跨命令命名空间的监听/锁状态不能冒充已确认清理。
未换主机/端口/浏览器或改网络绕过。详情为同目录browser-validation-limit.json。

这次资产准备重应用稀疏规则，移出了95份原已物化但未列在规则内的已提交工作文本；
初次探测在开模前缺输入退出1，日志保留。已从发布HEAD逐文件恢复4579610B，未覆盖
任何不同现有文件，也未重跑旧研究；母版SHA未变。**已有工作区不要为取几份文件重应用
sparse规则**；优先从Git对象精确恢复缺失文本、显式LFS checkout所需实体。独立exec的
PID命名空间不可用于判断别的会话进程，禁止按碰巧相同PID误杀。

## 下一个具体动作与完成条件

1. 先核本小项远端发布，每次开工先读本文件。共轴运动已接实际开发绑定，保留旧入口
   A/B；不要把其数值检查说成浏览器/完整原生验收，实际画面仍需验证
2. 先为140个有限采样平面头部计算完整八边形支承，再用原生工具研究贴合实际侧皮；
   10个缺平面支承者和六闭门接触保留不动。原四根柱与连续踏步/门槛关系需继续参考约束。
   不凭名字或计数删除原件，厂家尺寸/批次仍OPEN
3. 精确局部配置窄扩展已在母版通过限定依赖资格；不能将此当作接触/整车通过。
   继续实际门槛、侧壁紧固件与踏步的结构修正，保留原始身份和所有原件。
   52未知区间、其他门、82自身隐藏件、24父树外几何仍开放
4. 每小项立即更新文档、提交并插件发布核验。新LFS官方上传路线未通，不积压大母版；
   CLI认证继续停止重试、不访问凭据、不同步本机。厂家轴/内构与全部16项验收仍OPEN

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

## 最新完成小项：140头部完整底面覆盖与原生安装修复试验

侧壁支承诊断ea9329f已验证完整tree/parent/ref和12文本。此轮对原8e962d6…母版
执行可重放`scripts/trial-side-rivet-native-attachment.py`，不是只写检查或新造替代件。
先用实际原蒙皮外平面三角做完整8边底面数值覆盖，两侧各70个头部通过后，才通过
Blender原生EDIT/Translate将原24顶点/38三角头部沿法向内移11.999964714mm。

- 140底面以凸多边形差集核未覆盖区域，不能用总三角面积或9点探测假装完整覆盖。
  1e-14m²显式门槛，局部最多64三角/4096碎片；实际最多27三角，保留各底面/
  原三角ID/未覆盖多边形/重叠重复判定。这里是Float64数值判据，不是形式证明
- 3360已动顶点原生读回平移误差0，1120底环顶点对原蒙皮平面误差0；原形状、
  X/Z位置、拓扑/UV/材质绑定保持。10个不支持头部（四个跨倒角、六个投影后门）
  共240顶点精确未动，不删不藏。没有移动车体或四原柱以消除接触
- 7468其他原生mesh的位置/索引拓扑/材质/UV签名精确不变；10434对象的矩阵、
  父级、data身份和可见性精确不变。此签名不声称覆盖全部custom attribute或RNA
- 44闭门评估网格/三角索引精确不变；88门/两原铆钉对象配对仍104接触三角对；
  全部六个原闭门对象对及190三角对精确保留，不能报告净空通过
- coverage helper固定SHA a7e000b9…，20主测（含300随机）通过；独立55例中42例
  以精确有理数竖向分片并集对照。早期helper审计查出的下溢、循环排列重复及
  聚合溢出问题已在原生试验前修复并以测试保留，没有用失败helper动模型

最终固定输入/失败失效版本4.5.13实际23.333秒、线程1、峰1921356KiB，exit0；
不是隔离性能基准。进程记录script/report SHA，开始即写IN_PROGRESS，不让失败复跑
沿用旧PASS。证据`work/cloud-side-rivet-attachment-20261001/`。源文件SHA前后精确不变；只在
运行进程内做拟合安装修复，没有保存新blend、导出新GLB或声称LFS实体已上传。
GitHub发布的是重放脚本和证据，可在既有已发布源上恢复这一步；新实体官方上传
路线仍缺，不能更改LFS规则、编码资产或只推空指针。照片只支持固定蒙皮表面
安装关系，不认证现有头型/数量/间距、12mm改量、铆杆/孔或目标1977/543A批次。

后续：对该原生试验作明确标注的真实局部同机位审图；继续查10个疑难安装头部与
原柱的参考语义，不能为追求零接触擅移。整车动态/浏览器/连续净空未验收，16项OPEN。

## 最新完成小项：原生安装修复的真实同机位近图

140头部试验1bee95d已核完整tree/parent/ref、19文本逐字回取。此轮
`scripts/render-side-rivet-native-attachment.py`分别打开原源和重放后的内存试验，
实际Cycles CPU2/32samples原生去噪，各出1200×900近图，两图像素已直接审看。
中心为底部门槛行原头部60，金色/绿色仅为审图材质；同一机位、灯光、颜色设置
精确匹配，实际几何在渲染设置前后签名相同。before70.980秒、after75.238秒
均exit0，script开始/结束SHA相同；不是隔离性能基准或真实网页验证。

- 原图表现原头部与皮面分离、软影移开；后图表现同一原头部内移后的贴合阴影，
  11.999964714mm测量来自上一项顶点验证，不由图片像素推算
- 中央目标完整入框，标签可读。周边有头部位于近图外/画面边，不称全车或所有件
  完整入框；两张孤立视图不能覆盖全部10疑难头部、六闭门接触或原涂装
- 首版过曝/字幕被前景遮挡失败保留。仅修审图灯光/显式AgX/字幕深度，未改车体
  几何或相机；首轮after的进程脚本SHA在结束时才读，误记录已更新磁盘脚本，
  元数据缺陷及真实执行脚本另存并明确纠正，最终改为前后固定SHA

证据`work/cloud-side-rivet-render-20261001/`。最终before PNG1094170B/SHA27bcb092…、
after1090464B/SHA3b0aed9f…，文件在工作区外等待已授权阶段图片发送；它们尚未
通过Git LFS发布，不以编码或空指针冒充版本实体。本提交仅图脚本/实际终态/
SHA/审图文字证据。原blend未保存，生产/网页未替换，16项仍OPEN。

## 最新完成小项：四接触柱的精确旧踏板来源链

82cb961图证据18文本/完整tree/parent/ref已实际回取；最终两张真实原生近图已在
用户指定阶段渠道完成实体上传、线程附件回读及文件读取。PNG仍不称Git LFS交付。

只读历史编译源`work/compiled/maz543.mjs`（blob5fc94089…）第154–175行，
精确复现四旧支承X−5.09/−4.18/−3.89/−3.01m、侧向±1.455m、高1.23–1.45m、
半径.025m的来源参数。它们跟随固定cab中的门下平台创建，与移动门dg中的
半径.032/长度.13铰链形状不同。因此“固定踏板支承”是有源构造依据的角色推断，
不是厂家零件认证；不能继续按未知门铰链或整件cab_0063处理。

- cab_0063是同材质批次：源17组为8踏板支承+8座椅靠背连杆+1控制杆。当前16组
  精确保留8支承与8靠背连杆，控制杆seed8仅不在此批次；严禁整批删除/挪移
- 生成器先合并同材质兄弟再编号，所以对象名没有物理部件语义。原seed根明确
  标“estimated geometry; not factory CAD”；steel材质名也不是实物材料证明
- 原生生成器只清shell/door/body子树，保留cab直属旧批次，再另加0.90–1.13m
  曲杆踏步与每侧20踏条，解释两种作者方案共存；尚不证明旧平台盒是否都仍在
  当前母版，更不是已授权/已验证的替代或删旧依据
- 当前TS的门间隔不同，重生将使支承最多移280mm，因此不用它冒充原seed。
  原始编译文件/输入SHA和当前组件→seed→角色映射已独立读回留证

证据`work/cloud-step-support-provenance-20261001/`。两侧原照片像素仍支持连续
长踏板/三处低于门槛的悬挂件，而非原两短平台/四直杆；但目标车型批次、尺寸、
材料和隐蔽连接未定。下一步只读核旧四平台与当前完整踏步/门槛的实际共存，再
按完整安装结构做保留原件的独立原生拟合试验。本项未转门、改几何/显示或保存
模型，不靠减少碰撞计数删物体，16项仍OPEN。

## 最新完成小项：旧四踏板与后加低位踏步实物共存

984d29f来源链完整tree/parent/ref与6文本已回取，阶段报告已交付。本轮先用独立
纯Python解码器从原5c5849…seed及精确旧编译blob识别cab_0062材质批次的四平台
组0/1/6/7：每组24索引顶点、8独立角点、12外向闭合三角，源Float32角点精确匹配。
再以4.5.13只读实际8e962d6…母版，48个原定向三角各自精确出现一次；循环绕序
允许，反绕序和100µm单角破坏拒绝。四平台确实仍在，而非仅代码留下的假设。

实际50个指定对象无缺失，包含两旧材质批次、两侧皮、两后加Curve踏步、40踏条、
四闭门壳；原生曲线的控制点/倒圆/父级及真实评估包络留证。四旧平台对各自侧皮
110/64/102/60个三角表面候选，未在该限定范围发现旧平台对门/低位踏步/踏条
的表面候选。接触不自动判为误装、体积穿透或安装通过，不因共存就删旧。

证据`work/cloud-native-step-assembly-20261001/`，重放脚本
`lookup-legacy-step-platforms.py`及`inspect-native-step-assembly.py`。原生16.913秒/
线程1/峰1917980KiB/exit0，不是隔离性能基准。源SHA前后不变，不动、不藏、不拆、
不保存任何件；48三角数值仅旧源身份证据，非替代新LFS模型的编码。首次decoder
误给未支持--seed参数的使用错误及尾随tail造成shell0状态均保留，不接收失败输出；
正确调用有真实subprocess exit0。接下来用原图支架/连接身份指导整套原生结构研究，
严分后来目录与1977目标批次，16项仍OPEN。

## 最新完成小项：历史原图补证三支承与双踏面下框

cab1e79的14文本/完整tree/parent/ref均已核。此轮从正常加载的Sinref第018章图像
取得真正JPEG片段并看过图92/93，不再把早期246B重定向HTML叫原图。图像/图注
经核，1973年版仍只是站方归属，未得到封面/版权页；没有可见印刷页码，不杜撰页数。

两图与博物馆两侧照片、后来2008目录27图相互支持：**一套连续下框、两个踏面区、
三个下悬/支承位置**。“连续踏板”不等于一整块实心长板，不能把图中的两踏面区
合成一块。后来目录还可见每套三上部带斜撑支架，但没有标出车体隐蔽硬点。

- 图93短注17“трос”指上方驾驶室翻转机构插图，不能借此认定下部踏步为钢索
- 三支承本身不证明其柔性、材料、绳股、截面或接头；不能默认为三根钢索或刚杆
- 2008目录列543-8405012-10及M8紧固件，但修订不互换警告只是经销商说明，
  且图画两套、条目数量1仍有范围疑问，不移植这些尺寸/BOM到1977目标
- 1977DjVu实际页仍停Continue，没取得扫描像素；该版/MAZ-543A批次对应仍OPEN

`reference/cab-step-primary-topology-20261001.json`保存原URL、图号、SHA/像素尺寸、
已见事实与推断边界。原照片/扫描/目录像素只作本地研究，不随GitHub转载。本项
没有改模型/保存资产；下一步补140头部修复的门运动限定检查，再做明确拟合的
整套布局研究，不凭未明材料或目录尺寸造精确件，16项仍OPEN。

## 最新完成小项：140修复头部与共轴门的完整6160对范围

d94ebfc图证2文本/完整tree/parent/ref已实际读回。本轮导入原样ec323735…原生
头部修复脚本，在同源8e962d6…上保留真实修复前/后闭快照，再计算44门件×140
实际改动头部=6160对，包含3080同侧及3080异侧组合。使用已发布实测桶轴
p+R(local−p)、各侧带方向0–99°完整闭区间，不是仍存错轴的旧pivot，也不是网页。

修复前后各6160对均由一整区间包围分离，0未决/0新增未决。每移动/固定盒均外扩
20µm，最小正轴向界间隙均13.511261445mm；这是充分包围分离界，不是最短距离。
3080同侧界间隙保持，3080异侧界间隙因内移缩小约12mm但仍分离，**不称全面改善**。
原max_depth6/max_cells127不变，重叠负控保留64未决叶；漏对、重复替代、漏异侧
负控均拒绝。44闭门网格/索引和四控制矩阵精确不变，重放报告与1bee发布证据逐字一致。

4.5.13/线程1实际40.685秒/峰2113008KiB/exit0，源/执行脚本SHA前后相同，不是
隔离性能基准。此次没有实际转门，不新增原生依赖/姿态/全角浮点误差证明；20µm
仍是采用的保护量，不能称已证明Blender误差界。不外推10未改头部、6原闭门接触、
全车或网页，原6接触和16项OPEN保持。

证据`work/cloud-repaired-head-sweep-20261001/`。完整10原生文本3411672B使用
普通JSON字典表无损表示为717382B，保留每一配对/数值/轴/clear与unresolved字段；
双SHA清单区分原生字节和compact字节，解码后逐文件原字节/SHA精确一致，旧detail
SHA仍有效。另次独立读回完整6160覆盖与符号区间通过，没有为发布丢掉证据或编码
模型绕LFS。可重放审计/便携runner/编解码/轻量验证四脚本随提交；runner仅语法/help
检查，未再次运行Blender。原模型未保存或导出，新原生轴控制候选另行研究、不得
混淆本项已验证范围。

## 最新完成小项：双踏面/三支承的独立原生布局

f3ac77e已核完整tree/parent/ref、22文本及10原生证据无损复原。现按实际看过的
历史图92/93与后来目录图，建立**不加载整车**的单侧Blender原生布局：一连通下框、
两分离踏面包络、三支承站位（含共用中间站）。未把未知吊挂造作钢索、刚杆、
压接头或螺栓；橙色虚线仅中心线、青色线框仅未定接口，线宽不是物理截面。

全部尺寸逐项注明继承模型数据或拟合，非厂家值。两踏区实测间隔170.0001mm，
含线宽的全部布局最高Z1.109299m，低于继承门槛基准1.120000m约10.7009mm；
这只是选定基准下的位置约束，不是接触真实安装面或车体净空证明。原生Cube/
Boolean/Bevel/Curve实现，保留可编辑构造工具；没有手编mesh面/顶点，未动原车任何件。
下框一闭合连通分量、两踏面各闭合；谓词负控仅拒单块板/四站/越基准/踏区重叠，
不冒充实际物理碰撞。只研究一侧，未断言左右完全对称。

斜/正两张1600×1000 Cycles CPU2/32sample原生图已直接审看。23.592/23.940秒、
各180秒外部截止、均exit0；图可见双踏区、三虚线站位与未知接口，标注清楚。
首斜图文字对比不足失败保留，修正仅注释材质/颜色；几何报告参数/包络/数量一致，
未做独立全mesh字节相等证明。新便携runner只语法/help检查，没有冒充记录运行的
原runner。图像SHA/实际进程/初失败见`work/cloud-step-layout-study-20261001/`。

原整车只读SHA校验、从未载入该研究。无新blend/GLB保存，两PNG仍仅本地产物待
授权阶段交付、未Git LFS上传。该布局尚不安装，不确定硬点、材料/柔性/接头/纹理/
制造/强度/1977批次，也不解决原6闭门接触。另一个原生轴控制独立候选正在收尾
保存/重开证据，不混入本布局结论；16项仍OPEN。

## 最新完成小项：可编辑原生共轴四门控制及真正保存后重开

44caed61的18文本/完整tree/parent/ref已实际读回，独立踏步斜/正两图已完成授权
渠道文件上传、线程和文件读取。本项真正修复原生打开原四门仍绕错轴的行为，
不只保留网页补偿：原四Quaternion模式EMPTY各加0–99°的open_angle_deg属性，
总16个明确Simple Expression驱动location X/Y及quaternion W/Z，使用实测p−R·p。
不改原点、不重挂层级、不改网格、不移车体；原四控制对象及原自属性保留。

只承认已检查的单位初始四元数/缩放/delta及静态identity父链，其他结构拒绝。
每驱动仅读同一对象未驱动标量属性，无transform/scene/frame/其他ID/namespace
变量，无Action/NLA/关键帧/FCurve修饰器。非法值/类型/default/range、坏轴元数据、
非identity基态、mute/错表达式/transform回馈目标均拒绝。原始Python直接赋值可
绕过UI范围，会使表达式无效并被验证器拒绝；**不是自动机械fail-closed控制**。

- 构建与全新进程重开均禁用autoexec。各44状态×44真实部件，含独立、混合及三次
  重复全开/全关；每轮528实际铰链中心检查及1320闭门部件比较
- 最大中心漂移0.382438µm、逐点运动公式误差0.382997µm，原20µm门未放宽
- 99°实际±98.999999292°、门端实际位移1.314–1.421m，排除“没动所以不漂”；
  最大角误差9.65935e-6°。它们是有限姿态证据，不是全连续净空证明
- 44闭门评估坐标/索引/世界矩阵用np.array_equal数值精确相等，不单独声称
  signed-zero/字节级评估数组比较。原10434对象身份/库存及所列状态字段保留；
  原7470mesh显式存储字段逐字节签名相同，含全部attribute/UV/权重/shape keys，
  不含运行缓存/计算法线。16驱动和8新增属性本就是有意变更，未声称全部RNA不变
- 原生build175.456秒/CPU1/exit0，唯一候选保存后另启verify187.631秒/CPU1/exit0，
  各240秒截止；不是隔离性能基准。fresh验证先走全部正向状态，未改写任何已存
  driver表达式/目标，因此不是先修好内存再冒充存档有效

候选位于云外部工作目录`../maz-native-axis-controls-20261001/`，文件名、大小、
SHA见顶部，原母版SHA前后不变，fresh验证也没改候选字节。**新blend未LFS上传**，
无指针/编码替代物/生产或网页替换。本提交只交付精确4390d156…重放脚本和证据。
若环境丢失，只能从已发布原源和脚本重新构建再重新核SHA/验证，不称已找回这个
本地文件的原字节。先恢复官方新LFS实体通路，避免继续累积多份未上传大候选。

证据`work/cloud-native-axis-controls-20261001/`：build/fresh报告、真实进程/日志、
执行脚本冻结副本、终态Hash审计。四份相同1664080B mesh签名原件以10列式JSON
分片+schema/index无损表示（最大98648B），各自恢复原77f22c…SHA及原字节，
不编码模型资产；主审再实际恢复四份并核源/候选/脚本/报告引用。首次路径读回多
拼testcar的轻量错误留证，未打开/改模型。早期原弹簧shape key签名不支持而停的
失败保留，后补完整签名而非删键。build日志四次Math Domain Error是故意100°
负控并恢复；fresh日志无ERROR。原六闭门接触保持，未合并140头部/踏步研究，
没有物理、动画、制造、原厂批次、连续净空、渲染或浏览器验收，16项仍OPEN。


## 最新完成小项：保存候选四门关/开真实原生同机位图

e86dbff0的45文本、完整tree/parent/ref与本地对齐已实际核验。现从唯一保存候选
3b230c12…重新各启一次Blender，autoexec关闭且未导入重建器，仅写四个已有角度
标量，不改driver表达式/目标或直接赋location/quaternion。原始材质保持，13图片
与3字体预查全可用，无丢失的非packed引用、无替换/重映射。

两图为同机位1600×1100、Cycles CPU2/32sample/AgX，原生FONT标明独立舱范围、
本地LFS缺口和未整车验收。保留整个cab层级598后代加24个外部前舱命名物体，
范围内556几何、原本可渲染472件及所有旧几何/原隐藏标记保持。仅暂藏9467个范围
外原可渲染对象，完整名单随证据保留，未保存模型。本图不能当整车画面。

主审也直接看过两个最终PNG：关门外形完整、开门近侧两个洞口和门板清楚，对侧
两门板可见但部分被舱体遮挡，未声称能看到所有铰链或接触。四个独立实际端点
角度均±98.999999292°，门端位移1.314–1.421m，与关门0°/零位移对照；不新增
连续净空/碰撞证明。同相机/灯光/曝光参数逐值对比相同，候选和原源SHA不变。

资源预查10.989秒，关门65.490秒、全开65.284秒，各240秒外部截止/exit0，没有
失败渲染重试；这些是实际耗时，不是隔离性能基准。精确执行渲染脚本a15467d5…
前后冻结SHA相同，脚本/日志/进程/图像SHA、像素审看见
`work/cloud-native-axis-render-20261001/`。原报告终态注明待像素审看，后续审看另
文件记录，不重写原报告来破坏进程SHA。

两完整渲染报告各约1.15MB及650547B资源报告，以18个普通JSON数组分片/index
无损表示，最大116531B；主审再次还原三原件逐字节相同，并核45个原产物SHA。
无模型/纹理编码，也没有另存blend/GLB。PNG未Git LFS上传，待授权渠道文件交付；
67.9MB候选仍LOCAL_ONLY_LFS_BLOCKED。门控制候选未合并140头部修复或踏步布局，
原6接触与16整车OPEN继续保留。下一步继续真实装配和来源缺口，不把两端渲染
当机械/连续运动/制造/批次或浏览器验收。


## 最新完成小项：真实车体内的下踏步安装失败与实体缺陷定位

fd650c14的43文本/完整tree/parent/ref已实际读回；同机位关闭与99°两原生PNG已
授权渠道完成上传并分别文件/线程回读。本轮在保存候选3b230c12…的原0°状态临时
重建原样布局，没有修改/隐藏/移走旧件。结果是**布局安装FAIL，下框实体有效性
UNKNOWN**，不是把正常exit0当合格。

第二踏面仍X[-3.95,-3.00]、Y[1.46,1.58]、Z约[.9235,.9325]m，8个不同原轮胎/
轮辋/轮毂对象的真实三角表面点落在这个简单八角点盒内。主审另外fresh-open原生
模型，直接读取这8个三角，独立重算重心坐标与盒内边界，全部通过；最小盒面轴向
内余量0.132469mm，最大4.5mm，不是总侵入深度或整车最短净空。原轮胎/车体不动。

完整10353几何条目含9344原对象+1009实际evaluated实例；每实例读自己的评估对象
及世界矩阵，持久ID/父级保留。此状态1009实例恰与各自source placement精确重复，
保留完整名单而每源摆放只计一次。69去重宽阶段配对内64个BVH表面候选不等于64
碰撞；32踏面盒内表面证据分为8轮部件、20旧下阶重复布置、4原Boolean工具。
旧件/工具各自保留，不把工具或实例重复计数当实物问题。原上层cab_0062/0063与
本次三个物理包络无AABB重叠，但未因此判其自身安装或旧门接触合格。

原下框1092顶点/1114面/2188三角，raw索引连通且边2-incidence的历史结果成立，
但现有366额外重合顶点（177位置组）、478零长三角边、845严格零面积三角；1461
三角的crossnorm<1e-14m²包含上述845个。分析性exact weld后418边incidence不为2。
因此不能把旧“闭合下框”外推为非退化实体，frame winding仅数值候选，不给体积
碰撞/连续净空结论。本项不Weld或修网格；修复原生构造另项处理。

发现此前用上层旧platform X[-5.15,-2.95]当下层框跨度，没有真实安装依据。原
lowerCurve范围约[-4.823,-3.528]，再次实际看iwm07/12原照片，下阶在第一轮前结束，
没有贯穿整个两门长度；这是错误基准转用的线索，不是可由照片直接标定的厂家尺寸。
三站6条有限上射线/最近点检查也表明门槛最低Z不是硬点：后站先碰轮胎，不能当
车体安装面；支承材料/柔性/截面、真实硬点、接头、批次和载荷包络均待确定。

最终native attempt05为72.384秒CPU1/exit0/240秒截止，完整10353评估几何读回不变，
原身份/所列矩阵/父数据引用/可见选中/集合及实例记录保持；候选和原源文件SHA不变。
另主审8个三角复核18.028秒CPU1/exit0/90秒截止，同样不保存。均非隔离性能基准，
只一个闭门状态，无新连续/物理/浏览器通过。16项与原6接触仍OPEN。

证据`work/cloud-step-installation-fit-20261001/`。41份原生/历史文本11265505B由
普通JSON字段表/数组分片无损保存107文本7314497B（最大144991B），主审再次恢复
全部41原字节/SHA完全一致。完整10353范围、所有正分离界、实例映射与三角候选
未丢弃；无模型/纹理/照片或LFS替代编码。早期attempt01漏实例拒绝、02算术路径
比较拒绝、03真实拓扑拒绝，以及04重复统计/过强实体解释都保留，04明确superseded。
attempt03后来复制的runner明确命名retrospective，01–03无当时runner SHA声明；
04/05才在launch时冻结runner。当前便携runner仅语法/help检查，未冒充历史执行。


## 最新完成小项：被拒绝踏步布局的真实原生侧图

16d0bac8的完整root tree/parent/nonforce ref及117文本已逐个实际读回，本地对齐。
中断的对象发布先逐SHA只读核19已存在、43明确缺失，仅补缺失者并逐个留收据，
没有盲重传不确定写入或重算模型。三段小tree最终仍严格匹配本地完整root tree。

本轮补存此前唯一一次实际失败布局侧图的记录。图为+Y侧局部，原全场景保留、
相机自然裁切，只在内存加入研究框/两踏面及摄影灯光/相机/标签。原材质、原件
与旧上平台都保留，没有为显干涉改变原模型。直接看过PNG：过长的第二踏面横到
前轮区域，标签明确FITTED REJECTED LAYOUT及INVALID下框。投影中部分框/踏面
边界重叠、原母版轮胎偏浅，不能把图当深度证明、精确纹理或整车渲染验收。

实际4.5.13 / Cycles CPU2 /24sample/1200×840/AgX，exit0，120.763秒，180秒截止，
不是性能基准；未追加渲染。执行脚本b9f6e053…前后SHA相同。原9344几何对象签名
精确保持，原可见/姿态/材质等所列状态保持，摄影用camera/world/engine/selection
恢复后再对比。原源8e962d6与唯一已保存门候选3b230c12的字节不变，没有保存/导出。

PNG 1315375B、SHA c3be1592a5bb0ea467ff33ea30bdb01f2883cb16176a4b2b985ea5340b3458c7
已授权渠道交付并实际读取文件与线程；未Git LFS上传。本提交只外存
`work/cloud-step-installation-render-20261001/`和重放脚本。12完整原始记录1979424B
通过普通UTF-8日志分片与JSON字段分片保留为27文本1984695B，主审再次实际恢复
12原件逐字节/SHA相同；不是模型或图片编码。初次包装不能容纳大日志的未完整目录
不作为交付，以final包与index为准。原生进程/图像/报告没改写。

此前布局仍安装FAIL，下框修复另有完成证据待外存，不混称已经装车。保存门候选
仍LOCAL_ONLY_LFS_BLOCKED，原六闭门接触与16项整车OPEN保持。


## 最新完成小项：原生下框退化的构造修正及便携重放

47d5b2c6已核完整tree/parent/ref和32文本逐字读回；真实失败侧图已授权渠道交付。
本项在官方4.5.13 factory-empty场景精确重现旧366重复点/845零面积/1461极小三角/
418分析weld非二面边。原生Union阶段已有细小碎面，原ANGLE30°/2mm/3段倒角在
clamp overlap下扩大退化且体积几乎未变；关闭clamp只作诊断，不拿它掩盖构造问题。
预Weld仍有2极小面，后Weld/溶解又造成3个索引连通分量，失败版本都保留。

最终改为**一个外Cube原生Difference减四个贯穿窗口，再原2mm Bevel**。两端窗口
超外框端10mm，工具穿出上下各10mm，保留两纵轨的开放端，不增加封端横档。原
站位/14mm轨档宽/47mm高/120mm总宽/2.2m跨度与全部拟合来源保持；“集合等价”仅
指名义实数未倒角矩形集合，不是Float32网格逐字相同。名义体积0.003076808m³。

修正后480顶点/486面/964三角：0 exact重复点、0重复三角坐标集、0未用点、0
crossnorm<1e-14m²面，最小crossnorm4.1931192e-7m²。一个连通分量，边incidence2、
定向平衡、BMesh顶点manifold；7个普通截面在固定2µm比较量内保名义截面。非共享
顶点三角BVH相交候选0仅补充诊断，略过相邻面且非完备自交证明，**不称实体认证**。

2mm倒角现在实际生效，顶部退让1.999974–2.000000mm。相对旧退化体测得体积减少
0.62076294%，有限表面样点最大位移1.5092mm，这是有意外形变化，不称没改几何。
原/新未倒角有限双向样点最大差0.0934µm，bounds最大差0.1192093µm；均非Hausdorff
全表面界。原BVH nearest对照曾误差达377µm而失败，已保留；改为Float64逐三角平面/
边投影的距离审计，几何没为测试换掉。414个解析/变换/瘦三角/反向控制及全退化
拒绝控制通过，2µm只用于拟合尺寸比较，绝未放宽0重复/极小三角要求。

历史final/fresh空场景CPU1各3.226/3.023秒、exit0、120秒界，报告同16a16158…SHA。
它们没有传disable-autoexec且未加载任何车辆，历史原件照实保留不追补安全状态。
推荐新入口`repair-native-step-frame.py`配`run-native-step-frame-repair.py`接受明确
repo/original-script/original-layout-report/out/blender路径，可直接用Git中原study
脚本与报告，不依赖私有scratch目录名。新入口带disable-autoexec且入口、执行原
空场景prefix后、结束前3次实查关闭，不改永久偏好。一次2.973秒有界重放exit0，
几何签名/参数/来源/数值/检查与原7/8完全相同，仅明确列出的scriptSHA/输入路径/
autoexec元数据不同，不称全报告同字节。历史48文件逐字保持，主审再核完整清单
与前后报告除上述元数据外全部字段相同。

证据`work/cloud-step-frame-topology-repair-20261002/`和精确13223b82…推荐脚本。
原source模型只核SHA，从未载入；无新blend/GLB保存、无图片或模型编码、无渲染。
这只修原生构造，原2.2m布局仍踩轮安装FAIL，未知支承/安装点/制造/材料/批次不
补猜。下步先从真实下阶与邻轮位置重新确认基准，保留原件，不挪删轮胎求通过。
所有16项整车与原6门接触保持OPEN；唯一门控制候选仍LOCAL_ONLY_LFS_BLOCKED。


## 最新完成小项：拒绝把原短下阶当合格安装基准

cdfcadc0的完整tree/parent/nonforce ref及75文本已逐个远端读回、本地对齐；下框
修正阶段报告已授权渠道发送并实际回读。为避免把原短下阶当成新布局的无证据
基准，本轮只核原+Y的BL_Cab_-1_step及20个BL_Step_-1_*原横条，车辆仍保存的
frame0/四门0°，没有选新尺寸或修改模型。

已发布10353库存原SHA7929cddd…复用于宽阶段。轮集合按记录的直接父级
wheels_pivot_002选出186个source、89实例，名称均属BL_Tyre/Rim/Hub/Wheel_0组，
不称原厂完整轮总成。21×186=3906对中10对AABB重叠，进入窄阶段。本次新评估
33 source和6相关实例、共39条，位置/三角索引SHA、计数和bounds逐项与原库存
完全相同；其余库存明确复用，不冒充新查全场。89轮实例的历史重复映射被引用，
只有5个相关轮实例加1个step实例重新评估，另84个轮实例没新评估。

原curve对轮胎profile及3个vent命名细节件，末横条19对profile及0.635 mould ring，6组物体
均有严格非共面三角交叉，共188浮点判据正配对。留每组一份实际两三角坐标/
顶点索引/几何SHA、共享线段、交段中点、barycentric/plane residual/边距。最强
curve/profile交段22.589869mm，中点到两组三角边的最小距离5.804031mm；bar19/
profile分别10.784259mm与5.205114mm。**边距只指中点，不是整段边距或侵入深度**。
其它4对无严格正证据，不是clearance pass；共面/仅边触/近退化/包容不在该判据内。

另一份独立有理算术脚本直接把记录的binary64坐标作为精确分数，重新构造两组
截平面线段，验证两套端点严格相同、间隔为正、中点barycentric严格为正及平面/
重构残差精确0。6份均通过；主审再执行该轻量证据检查，输出与原证书逐字/SHA
相同。它证明记录三角相交，不自己重新读取Blender、证明轮体实体或连续物理。
原生身份另由上述39条匹配保证。

原curve是未封端5点POLY、23mm bevel；后上点(-3.55,1.48,1.13)m与20横条最末
X-3.6795m只是继承的authoring坐标。其与轮边界纵向包围重叠数字不当penetration；
真正拒绝基准依赖三角正证据。原短下阶与先前2.2m布局都仍FAIL，不能机械沿用
任一版本的长度/高度/末点或spacing来“通过”新安装，需来源和实际邻轮共同确定。

一次官方4.5.13/background/factory-startup/disable-autoexec、CPU1、120秒界，
exit0/28.611秒；非性能基准，无失败或渲染重试。10434原对象所列身份/父数据/
矩阵/可见选择/集合/modifier状态保持；33选定几何结束又比一次。没有全场mesh
重验声明。源8e962d6、候选3b230c12、库存及执行脚本SHA不变，没隐藏删除移动
任何原件、没保存/导出或渲染。

证据`work/cloud-existing-step-datum-20261002/`，原生脚本1118b30b…及独立精确
算术783e7e49…，显式路径runner可从已发布package恢复原库存。16原证据仅187032B，
不再复制9.7MB库存或任何模型资产，主审核全部16文件SHA。原六门接触与16整车
验收继续OPEN，唯一保存门候选仍LOCAL_ONLY_LFS_BLOCKED。


## 最新完成小项：精确恢复既有1977手册来源，正文仍待读取

11b41978的完整tree/parent/nonforce ref及22文本已逐个实际读回，本地干净；阶段
报告已授权渠道发送并回读。此次找到已登记public Drive原书并完成只读获取，
11405399B、SHA cf8ebb65dcbfca6dd3b6c55a3174cfe9d628a206cb8c846eceee0041a2bb1bde，
与既有`maz543a-nominal-1977.json`完全一致。书名/版次/1977年沿用原记录，此轮
没有新解码封面或重新验证印刷页12/13，不能以下载成功冒充新读到安装内容。

本地IFF只读结构检查由主审再次复算：1 DJVM、240 DJVU scan units、29 DJVI；
240 TXTz、240 Sjbz、40 BG44、10 FG44及29 Djbz，无长度越界。没有TXTa明文字层
或BGjp/FGjp JPEG页，所有相关层均需解码。240个scan units不等于240印刷页，
跨页扫描对应关系此轮未核。现环境无现成DjVu解码器，未下载安装新软件，也未
把原书交给在线转换站；成功下载后尝试网页预览遇验证码，已停，不作为正文证据。

只外存1982B净化来源记录`reference/1977-handbook-recovery-20261002.json`，保留
public URLs、byte/SHA、格式计数与明确边界；无raw book、页像、连接器响应或
私人传输数据。原书研究副本留在云工作区。此结果只解决源文件可得性，仍需实际
解码/审看cab章和图，再判断它是否包含下阶安装点/支承结构/尺寸及目标批次。
**未读不能表述为书中没有答案**。既有照片的一维轮轴投影也不能替代完整相机
标定或制造尺寸，不能凭它们直接把两版失败下阶改短来称精确还原。

没有模型/几何/姿态/资料像素发布或新的安装结论。两版下阶仍FAIL，原六门接触
与16整车OPEN保持。门GLB14bit位置量化的既有54.479µm>20µm问题另行只改导出
策略/小范围验证，当前旧GLB未变、未宣称该误差已经解决；不新增大资产积压。


## 最新完成小项：读到1977原书A型下阶照片与驾驶室图，安装尺寸仍未知

前一902049b恢复记录仅记当时未解码状态，现由本项明确取代该限制，历史记录保留。
同一11405399B原书SHA cf8ebb65…解码前后不变；已直接看标题/前言、p6图2、
pp170–173驾驶室正文和pp174–177图101/102及图注。标题确认第三版莫斯科1977，
前言说以543为基本型，说明A/V/M差异，技术资料截至1977-01-01；驾驶室正文将
543和543A并列为两座、两门的左右驾驶室，不能由此认定每张通用图的具体批次。

p6图2明确标MAZ-543A，照片可见下阶在承载车门的固定门槛下、靠近前侧首轮之前。
斜视网点照片不能给出精确坐标/隐藏连接或三维净空。图101左舱与图102右舱上图
均显示连通下框、两处踏面和三支承位置，下阶并不沿整个驾驶室底周或后部延伸。
图102的17号трос引线位于翻舱机构小图，不能拿它证明踏步支承是绳索。
主审独立看上述关键图像和标题/前言/p170，对应逐页SHA与scan-unit/印刷页映射
记录在`reference/1977-lower-step-source-20261002.json`，不把OCR匹配当像素证据。

所读页像中没有确定下阶毫米尺寸、三安装坐标、支承材质/柔性、截面、关节或首轮
净空。OCR全书词干поднож无命中仅是检索结果，**不是整本书没有答案**；其它未读
页/图仍未知。本项提供A型原书照片这一较强车型依据，不选择新长度/高度/offset，
也不把二维前后关系升为实际安装通过。原短下阶与2.2m拟合布局仍各自FAIL。

已授权的官方DjVuLibre3.5.28解码工具、Debian包来源/版本/SHA、页像SHA/范围与
边界均记入9567B来源JSON；没有上传原书、页像或OCR，没有在线转换或模型写入。
下一步仍需可适用装配详图/有记录实测，结合原轮胎和门槛实际几何形成明确拟合
假设后验证。新原生门候选保持LOCAL_ONLY_LFS_BLOCKED，整车16项继续OPEN。


## 最新完成小项：阻止门压缩旧流被静默保留，真实源内存精度对照通过

a2f73cb的完整tree/parent/nonforce ref与2文本均逐字读回，本地对齐干净，1977
手册实际来源结果的阶段报告已发且线程实读。当前只修一处打包策略和相关小验证，
不创建第二份大模型或新GLB，不改变生产入口或原源/材质/UV/拓扑。

根因：既有`export-va180-cab-candidate.py`已经要求POSITION18bit，但
`prepare-va180-cab-pack.mjs`只批准2个旧mesh换流，因此通用packer又保留了20条
14bit门流。现在`preserve-unmodified-body-streams.mjs`在任何JSON打包修改或文件
写入前，读取实际会保留/替换的Draco流元数据，拒绝超预算门流。不能靠候选
导出设置、尚未编码的accessor bounds或把旧流标changed/new冒充修复。

新policy将本地POSITION完整grid step限制10µm，是既有20µm比较的一半；所需
bit按range/(2^bits-1)确定，不是完整世界/Float32传播误差证明。范围明确限静态
4已知pivot/20精确子mesh；同时查baseline/candidate防止改名全部pivot绕过。
scale非1、matrix式变换、skin、weights/morph、translation非3项或链上动画拒绝，
未知/lossless路径需单独审查，不默认放行。实际fde04 GLB20流中12条被拒，
8个较小handle/lock满足grid先决条件；当前完整资产仍FAIL。

这次重新恢复的是**已发布既有**Textured LFS实体，99960163B、SHA6e406eca…，
作为原export真正merged/baked输入；不是用独立Master或原生门控制候选替代UV
和几何来源。其只读恢复没有修复CLI写认证或新增LFS上传。官方4.5.13LTS/build
daeeeca98fb0、background/factory-startup/disable-autoexec、CPU1、120秒界执行，
仅20真实门primitive在内存各编码14bit、按范围12/13/17bit及18bit，共60次。
实际gather/compressor/native decoder与独立WASM读grid均有SHA，临时PNG编码、
最终buffer/image/GLB写出入口被拦截；输入和冻结脚本前后SHA不变。

有限双向所选真实顶点距离/全mesh跨度/12个真实连通铰链barrel跨度比较：14bit
12/20失败，最大顶点距离64.416381µm，barrel跨度误差54.478645µm，重现已知
问题。按range策略最大8.123744µm/3.933907µm，固定18bit最大4.129531µm/
2.145767µm，均低于未放宽的20µm。KD只选对应候选，距离用Float64重算，
它是到所选真实顶点的有限上界，不是逐角点对应、连续曲面或Hausdorff证明。
attribute名称/类型及index数量已查，UV/normal值和完整三角对应尚未认证。

成功原生exit0/20.735秒/RUSAGE_CHILDREN峰1762468KiB，非并发总内存或隔离
性能基准。首轮0.466秒exit1因把版本字符串误写4.5.13（实际带LTS）在开源前
拒绝，其真实原脚本/日志保留，最终改精确tuple和build hash。原生后最终policy
只补静态资格与注释，执行时dc7cdb…字节保留，三个grid/decoder函数及policy值
与最终40b31a…完全相同，不能把后加资格检查说成本次原生执行过。

最终12类负控/路由检查通过，实际packer在写入前exit1，原字节/描述符未改；
主审对落地代码独立再跑，guard和20流报告逐字相同，又逐SHA核全部交付文件、
8项执行源码映射，并从60次原生记录独立重算14/18/policy摘要完全相同。
最终repo-config lint4文件/208规则0diagnostics；初始外目录缺tsgolint、早期空
输出lint及初次隔离packer找不到three的失败保留，不当最终覆盖。仅连接既有
依赖，没有安装新包。两个Python脚本AST通过，未运行无关整app构建/浏览器。

证据`work/cloud-door-position-precision-20261002/`，原始30文本273532B加主审
复核小记录，原生report SHA27e25aaf…；一处packer变更和5个新增脚本可重放。
下一步真正修复资产仍需以原Textured重编码门流、核逐角点/UV/normal/拓扑和
其它流保留，再完成新LFS实体上传/实际回取。当前未产出/上传新GLB，旧GLB仍
FAIL，唯一保存门blend仍LOCAL_ONLY_LFS_BLOCKED，原接触和16整车OPEN保持。


## 最新完成小项：下阶安装来源有限补查与可追溯馆藏线索

门打包修复b4ed2d2的完整tree/parent/nonforce ref、39文件逐字读回，本地对齐
干净，阶段报告已授权发送并线程实读。当前check-runs和commit statuses各0，
empty aggregate为pending，不是正在执行CI或CI pass。

沿1977原书目录/OCR选择新scan units185–187与235–236，实际解码/看图pp366–371
保养表及pp468–471目录，没有重复此前cab图。第50–63项驾驶室/底盘保养未给
下阶硬点或尺寸；主审另直接看p370第62项，确为专用车身支座，不能把列出的
24/27mm扳手当踏步紧固件依据。这里只记这些页的有限负面结果，非全书缺失证明。

新增官方VHÚ–VHM Piešťany页面和5张具名照片，原URL、尺寸/SHA及适用边界记
`reference/step-mount-source-followup-20261002.json`。官方记录说明1974年制车、
2023年从VÚ4405 Nitra转入馆藏，并引用AT278运行记录与编目卡。它只确认MAZ543
馆藏身份，没有A型、底盘序号、下阶原装/修订证据，不能用年份代替目标车型。
主审独立读官网及34089/34091两照：左下框三支承和靠首轮前缘的投影可见，后门
下部覆盖首轮上前方投影；不支持按两门总长铺低踏板，也不足以确定胎外侧向
位置或后门登车路径。右侧未见同样完整下框，可能缺损仅为解释，不能用缺件或
不对称倒推原厂。支承上端紧固件/截面未分辨，弯曲外观不能证明绳索或柔性。

只外存11183B净化JSON，不上传书/照片/OCR，不联系馆方，不采纳其网页泛用
技术参数。可用下一来源路径是可适用旧543-8400008装配详图/修订图，或先核
可追溯实车识别和改装记录再实测；若以后联系第三方需另有通信授权。当前没有
选择新下阶长度、高度、侧移或硬点，两版下阶仍FAIL。不再重复同一组斜图来
换算毫米；原书已确认的1°轮外倾可独立继续原生机械改正，先审真实装配轴与
接头闭合，不能单独倾轮破坏其它机构。整车16项继续OPEN。


## 最新完成小项：真实前4轮接口与固定硬点外倾可达性，未选择新姿态

5af36b5的完整tree/parent/nonforce ref及2来源文本已读回，本地干净。下阶没有
足够新安装依据，继续另一个已知问题：转向轮原几何0°与1977名义1°的差异。
此次先读真实接口，不能只倾斜轮胎，也不把未核载荷/胎压与原文magnitude当完整
原厂静态设定。前4轮之外不沿用该1°要求。

当前8e962d6母版frame0，官方4.5.13LTS/builddaeeeca98fb0、factory-startup/
disable-autoexec、taskset1核/threads1/BLAS1、120秒界，exit0/17.164秒、
RUSAGE_CHILDREN峰1891488KiB，完成marker和完整JSON均存在，原源SHA前后不变。
此实际runner漏--python-exit-code，原argv/源码/终态原样保存；不以exit0单独
判成功，下一runner必须加明确python-exit-code1，不重写既有记录。

读104几何接口、1424对象scope；72条直接SHRINKWRAP字模→同胎目标均在scope
内，scope外直接目标0。这里只是直接object-pointer/driver目标观察，未形成完整
依赖许可；NODES/SUBSURF、collection/data/嵌套引用和动画状态须在候选前严格
审查，不能按名或类型白名单。中性wheel/carrier、upright、brake、shaft分别烘焙
动画的原父链是真实读出，尚未修改任何对象/动作/modifier或父子关系。

以轮面上缘向外为正，c=-asin(outward轴z)，把实测内轴/外销投影为原模型平面
四杆、保持臂长和轮架销距，+1°下两可达圆内部错开2.4437733–2.4437736mm，
没有闭合解；不是少量q采样没找到。主审独立从恢复的104接口质心数值重算该
圆交判据，与记录吻合；这是浮点解析检查，不冒充区间算术或原厂硬点证明。
−1°近分支虽闭合，却需轮心下移约71.593mm、上臂约−14.645°，不能拿它当
‘修成1°’。旧spec的上臂**精确**水平近分支只给camber+0.2477269°/轮心升
27.2565mm；未给‘近水平’杜撰容差，未修改内轴/臂长来强行凑数。

主审新看1977原书pp154–157、164/165图98，并重新核pp320/321。图98确标
下臂两头中心竖差136+5mm，p320用于装/换扭杆且支承bolt顶住上臂；满载时
上臂接近水平是另一个条件，不是把136–141mm当静态轮跳/路面高度。p157说明
鼓定位于hub内侧并螺栓连接；p154/155明确双十字叉外半轴Cardan与knuckle内部
CV及support两球轴承是不同部分。因此读到原外Cardan法兰与轮毂轴约6.207°
差异，不能直接断言这个法兰必须就是hub输入轴或强行设同轴。缺失接口仍未知。

4个鼓候选brakes_0003/7/11/15包络径670mm、轴宽130mm、148原顶点，顶点均值
z偏约9.054mm是采样分布；不能把均值当圆心。实际圆截面/原生成源码的身份
核对、鼓随spin和鞋静止的最小关系修复留给下一项。半轴广泛联动草稿未执行，
也不收入本已完成检查点；既有母版和唯一门候选均保持。

证据`work/cloud-wheel-interface-readout-20261002/`：原interfaces2410990B以4份
可读普通JSON表共379766B存储，5474条唯一值/引用，未存任何blend/GLB/PNG或
二进制压缩字符串。独立进程逐片验证并恢复原2410990字节，SHAfea41bf0…与
真实原生输出逐字相同。连同原探针/runner/终态、解析输入/结果、原书来源v2及
主审记录共20文本453495B；没有复制全车9.7MB库存。原生几何不变，没有新
LFS、渲染或生产晋级。名义外倾、CV/轴承内部、载荷、全转向/碰撞、16整车
验收都未关闭。下一项只验证0°中性几何保留的父链及鼓旋转，再保存与报告。


## 最新完成小项：保存两次未通过的轮组父链/鼓旋转候选，撤回空动测PASS

7f1ce0f的完整tree/parent/nonforce ref与21文件已逐字读回，本地对齐；阶段报告
已发且线程实读。当前只在内存尝试将4个完整carrier与静止制动机构跟随原
upright/kingpin中性joint frame、将原鼓proxy挂到spin。没有修改硬点、选择
外倾/转向角、挪半轴或保存blend/GLB。原作者cylinder(.335,.13)与实际圆截面
拟合对应简化鼓proxy，不冒充真实鼓壁/中心孔/定位台肩/轴承接触已重建。

01官方单核/120秒界/--python-exit-code1，exit0/64.521秒。776件中性逐顶点
最大7.045966e−8m（0.07046µm），低于既定2µm，三角索引相同；817结构资格、
72精确SHRINKWRAP profile及9626外scope矩阵比较完成。但执行方和主审都
从原QUATERNION rotation_mode与8项全零发现，脚本写rotation_euler并没转动。
原report的PASS和8个动测零误差**全部撤回**；原字节保留，以单独VALIDITY
文件为权威判定，中性结果不能升级为旋转/机械验收。

02改matrix_basis，并在源码加入实际world角度、鼓/胎非零位移、每顶点2r·
sin(θ/2)轨迹及刚体预期、旧Euler路径无运动负控、最终恢复检查；事前固定
原生成lib/maz543.ts SHA d1fdc631…（同01来源记录），避免来源变更后仍假称
对应。实际CPU1/120秒界，28.497秒exit1：到首站0/0.731rad时，最大刚体顶点
误差210.655025µm、半径轨迹误差101.554275µm，超过既定20µm；静止制动
几何误差0。断言在逐对象诊断和最终报告前发生，责任对象仍UNKNOWN，不能先
归罪字模或把72字模排除。后7个实际角度样本和最终恢复/外矩阵检查均未到达，
不得冒充已覆盖。01、02真实脚本/runner/argv/终态/日志及独立VALIDITY全保存。

另有实际导出不兼容：现VA180 exporter明确排除S543_SUSPENSION祖先，而
此候选把前轮/制动挂到该分支的upright下。未经适配直接复用旧exporter会遗漏
这些选择；本轮没有改exporter、生成GLB或称可推广。零偏置四杆+1°无解结论
只针对继承的固定拟合硬点/臂长和wheel-axis相对upright的既有零安装偏置，
不证明原厂不可能或需要改短某臂；knuckle/spindle/trunnion/CV关系仍待资料。

原source8e962d6已独立再次SHA核回不变；唯一已保存门候选未改、没有新大资产
积压。证据`work/cloud-wheel-neutral-failures-20261002/`共16文本161334B，
01report SHA811cd191…原PASS字面留作错误历史，顶部README/SUMMARY与
VALIDITY明确FAIL。下一项只做首站同0.731rad的原父链与修后186/187件全保留
对照，先落每件最坏顶点/误差再断言，区分既有modifier问题与新增回归；不放宽
20µm/2µm门，不删字模，不把未跑诊断记为结果。名义外倾与16整车仍OPEN。


## 最新完成小项：定位同两字模的继承回归，并量到原鼓随spin的真实收益

9d17f50的完整tree/parent/nonforce ref、17文件及阶段报告均已实际读回，本地
干净。此次只首站0、同0.731rad，在同一官方原生进程两次fresh-open同8e962d6
母版，比较原父链和冻结candidate02的中性父链。直接复用已执行SHA1001ef7d…
的helpers及mutation loop，不另写替代装配，也不冒充重做完整依赖资格。

CPU1/120秒界、--python-exit-code1，99.973秒exit1、峰2116344KiB，原源SHA
前后不变。两case和comparison完整落JSON后，最后原20µm门仍拒绝候选；exit1
不是缺记录。每case全187对象：原186个spin几何加原鼓（原父链鼓静止、修后
鼓进spin），另3固定制动件；未排除字模，没有全mesh顶点数组，只留逐件统计
和最坏点before/after/expected/轨迹等证据。请求0.731rad，实测0.730999589rad。

两case只有`BL_Tyre_0_emboss_10`/`_19`超20µm，分别125.370154/210.655025µm。
主审独立从还原记录比对，共用186件的**完整逐件观察字典**一一精确相等，
不止最大数相同。原母版父链已存在相同失败；本轮锁定对象及其Shrinkwrap/
Solidify栈，尚未隔离哪个modifier的具体数值机制，不预先把它解释成缩放、
BVH或某内核bug。其他所有字模仍在原检查中（下一大值8.621µm），整个候选
仍FAIL，不因为是继承缺陷就改口为全轮通过。

原鼓在原父链最大位移0，修后最大顶点实际走239.468959mm；其刚体误差
0.176062µm、半径轨迹误差0.00970µm。胎最远实际位移521.113177mm，3个固定
制动件顶点位移0，证明这次不是Quaternion对象被写无效Euler的空测试。此为
保留简化圆柱鼓proxy的挂接收益，不是厂家鼓壁/孔/台肩/轴承或力学刹车认证。
两case各190个观察/固定几何恢复的顶点数值和三角均相同、最大误差0，spin
原矩阵/action恢复，10247外scope world矩阵未变，控制失败列表为空。

三原JSON共668207B以共享明文JSON表3片266737B保存，复用7f1ce0f已发布的
codec（SHA2334d073…）；独立进程恢复三文件逐字/SHA相同，并重新核186条
一致观察、两失败名字和190项恢复。没有压缩二进制字符串或模型/图像资产。
完整证据`work/cloud-wheel-spin-diagnostic-20261002/`共15文本301221B，含实际
执行脚本/runner/argv/过程/原日志、摘要、原始字节恢复与主审记录。

下一候选准备以原生Modifier Apply在中性位固定4轮72个同资格字模的已有贴合
结果，保留字模对象和后续Solidify，不按这两个名字特判，也不单纯关modifier/
隐藏删除字模。先查中性顶点/三角、UV、材质与数据共享，再做4×2实际spin、
非零位移与恢复，门限保持20µm/2µm。尚未执行，原8e母版不保存，不增加
blend/GLB积压。名义1°、缺失CV/支承安装和旧exporter父分支排除仍未解，
16整车继续OPEN。

## 2026-10-02 05:27 UTC：原生字模贴合修复，120秒终止证据

证据：`testcar/work/cloud-wheel-native-fit-timeout-20261002/`。原母版8e962d6、官方
4.5.13，CPU1/120秒硬界、Python退出码1。实际脚本SHA
`ab0125e6da25b0509ccc2d4f94e7b47d74a5488f61d578e787075e01a895b64e`，
120.069614秒超时，wrapper124/native exit null，峰RSS1917388KiB。原脚本、runner、
原始日志、launch/process和独立VALIDITY全部保存。没有最终report.json，不能称PASS。

- 对同一合格类别全部72个前轮字模执行原生Shrinkwrap Modifier Apply，不仅处理
  已知两件。各自Solidify参数、可见性和72个原SOURCE FONT检查均保留；原数据
  users均1，不需要单用户复制。没有手工顶点/面构造，也没有blend/GLB保存。
- 已写776件中性几何检查：最大位置差0.07046µm，既定2µm门不变；三角索引、
  评估UV/材料签名一致。全部字模继续参与。
- 已写4轮×0.731/π共8个实际旋转样本：最大刚体误差0.36165µm、
  半径轨迹误差0.19788µm，静止制动件0。20µm门未放宽。4次还原记录均顶点/
  矩阵误差0并还原原action及latent Euler。
- 最后9626个原外部对象矩阵核对、最终源检查和汇总没有完成报告，不推定通过。
  Euler负控虽在样本前执行，其汇总只留内存未输出，也不当作已交付负控表。
  进程后独立SHA确认原8e源不变。14个原JSON共742610B存为5个可读明文
  值/引用表分片；父级独立逐字恢复并核各SHA，codec沿用已发布7f1ce0f版本。
- 下一次只建立前后完整data-user索引，并保留原Object引用，在全部还原后对每个
  实际matrix_world读取一次、仍比较16系数。原全集、8姿态、所有保护、2/20µm
  门和120秒硬界不变；原超时证据不覆盖。

本项只证明上述已落盘前缀。名义1°外倾、转向/CV、真实鼓/轴承结构、旧exporter
排除S543_SUSPENSION导致新父链漏导风险、网页及原生全时间线均未解决，16项OPEN。
新LFS实体发布缺口仍在。

## 2026-10-02 05:44 UTC：中性支承/随轮鼓/胎字原生修复完整终验

证据：`testcar/work/cloud-wheel-native-repair-pass-20261002/`，仍用原8e962d6母版
和官方4.5.13，CPU1/120秒硬界。实际脚本SHA
`5940176455cbb19373f96d0b2150dd636006e67eb73d404e44bf77b9313d49e8`。
05:34:44–05:36:26 UTC，101.482280秒exit0、峰RSS1919432KiB；最终完整report和
独立分项已落盘。这是SCOPED PASS，不是全车或网页验收；原超时证据保留不覆盖。

- 实际4个原主销轴下新增中性joint frame，轮carrier和固定制动组共用原upright
  支承，原简化鼓代理改随spin转动，制动蹄/执行器保持静止。8个旧carrier/brake
  action数据块保留，但候选中脱离驱动；joint未做转向，原全时间线尚未认证。
- 所有72前轮字模统一原生Apply其已精确资格限定的Shrinkwrap，保留Solidify、
  可见性及原SOURCE FONT。各原mesh均单用户；实际外部共享同行数0，不夸大为
  非空共享网格验证。776件中性最大位置差0.07046µm，既定2µm门不变，三角
  索引及同一进程中前后评估UV/材料绑定签名一致。
- 4站×0.731/π共8真实matrix旋转，每站187件均参与，最大刚体误差0.36165µm、
  半径轨迹误差0.19788µm；20µm门不变，鼓和轮胎真实非零位移、固定制动件0。
  4个Euler写入QUATERNION不产生运动的负控明确拒绝；4次还原的顶点/矩阵均0、
  原action和latent Euler还原。
- 全部9626原外部矩阵最终核对不变；转动/还原后再次验证72源FONT记录字段和
  72字模可见性，无失败。10434对象的有界反向依赖扫描无命中，仅覆盖脚本列明
  路径，不称完整Blender依赖或材质位移证明。最终源SHA仍8e962d6。
- 17个原JSON共1254989B含完整report和每个独立分项，作为6个明文值/引用表片
  保存；父级在独立目录恢复逐字/SHA通过。原脚本/runner/日志/启动/终态另存。
  父级对照发现两轮8spin+4restore语义全同，中性776位置/拓扑字段相同；但301个
  UV/材料组合hash跨fresh-open不同，各轮内部before=after仍成立。原记录只有
  组合hash，具体组件与原因UNKNOWN。`parent-record-comparison.json`保留完整
  差异，不宣称跨进程外观一致。下一项只读少量代表对象定位组件，不猜原因。

没有新blend/GLB保存或生产替换。原鼓仍为封端简化代理，未重建真实内孔/鼓壁、
轮毂定位台和轴承座。保留中性0°，名义1°外倾、载荷/胎压/符号、转向/CV/半轴、
接触和连续净空均未认证。旧exporter会漏重父链轮组，网页还会清空suspension
子层级并按旧局部坐标覆写轮/制动姿态，不能仅放开导出白名单。需明确候选装配
与绑定，现生产规则不改。新LFS上传缺口仍在，16整车门仍OPEN。

## 2026-10-02 06:06 UTC：四个代表件的跨进程差异定位到评估UV

证据：`testcar/work/cloud-wheel-appearance-components-20261002/`。只读同一8e母版、
官方4.5.13，CPU1/30秒硬界。第一轮原计划两次fresh-open，30.054秒超时，wrapper124、
native exit未知；第一份6件组件JSON完整落盘，第二次没有完整记录。保留原script、
runner、argv、log和失败终态，不把部分样本当两次成功。随后只补一次单fresh-open，
16.513029秒exit0、峰RSS1917160KiB，未重复第一有效样本。两进程初始化顺序和
同6件读取函数相同；明确这是跨两个独立进程的两个完整样本。

- 4个原组合hash变化代表：BL_Hub_0_cover、BL_Wheel_0_nut_0.26_1、
  BL_Wheel_0_washer_0.343_12、BL_Tyre_0_curved_tread_blocks。本轮仅
  evaluated SurfaceUV 的float32字节摘要不同；两处重复/派生组合hash一起变，
  不是3个独立故障。
- 原始网格UV及外观记录、评估材质列表/slot绑定/面材质索引、局部顶点/loop/
  triangle顺序摘要、UV形状/字节数/active标志/数值范围/非有限数/负零数均相同。
  范围相同不代表UV值相同或有误差上界。两个无修饰器对照
  BL_Tyre_0_VI203_profile、BL_Rim_0_bead_lock的全部记录字段相同。
- 原UV数组未保存，尚无逐loop差值、ULP或最大UV误差，也未定位具体modifier因果。
  6件固定读取顺序不同于早先776件完整遍历，不能追溯证明历史301件都同因，
  不把4件结论外推全部。材质绑定记录不代表完整shader或真实渲染。
- 父级独立解析两份JSON得到同4变2稳，包内compare-components.py再次复核通过。
  全部原记录按字节保留，源SHA仍8e962d6；没有模型变换、Apply、渲染、blend/GLB
  保存或生产替换。16门OPEN，原生限定修复的同进程保护边界保持不变。

下一项准备同机位原生轮组中性/实际转动双图，保留原材质、附近门体和已知下踏步
干涉，不移隐藏原件；之后推进候选导出/网页装配兼容。新LFS实体上传缺口不变。

## 2026-10-02 07:00 UTC：原生前轮中性/转动两张实图已完成并交付

证据：`testcar/work/cloud-wheel-native-render-20261002/`。同一原8e母版、官方4.5.13，
明确是66085四站方法的**站0局部原生演示**：各独立进程只实际Apply18个合格字模、
重挂一站支承/鼓，另三站保留原源状态。原4站/72字模资格及全对象依赖审查保留；
只改变原方法4个精确校验过的AST节点，不删原车体、轮胎、遮挡物或已知干涉。
两张图不等于完整四站渲染候选，更不是全车/网页验收。

- 中性图112.018秒exit0，渲染57.092秒；转动图110.494秒exit0，渲染55.843秒。
  原计划每图CPU2/240秒界，实际均完整终态。脚本
  `40c4dd55a4ae210ca560f5f40fbeabd460b956f39b32ac64339c7ed8e118299c`；
  runner `fb5ed3f650118e822baba1970fd551270297e86100df3bd541f3a1f0fd107c38`；
  actual HEAD为bc5eced9，方法资格仍归属66085，不把新HEAD冒称曾通过旧全项测试。
- 同一实际相机矩阵、2.60m正交尺度、灯光参数、1100×1000/12sample原生Cycles
  CPU去噪均实读一致。原材料/世界/可见性/对象身份分别在各进程前后保持；
  含指针的材质指纹不跨进程比较。没有blend/GLB保存或生产资产替换。
- 实际转角0.730999589rad（请求0.731，约41.9°）；20个轮胎/简化鼓/字模见证
  均有非零实际位移，最大刚体误差约0.350µm。10246个固定原矩阵误差0；
  最终18FONT、18Solidify和字模可见性保护通过，20见证顶点还原0、原spin
  action/basis/quaternion/latent Euler精确还原；源SHA前后仍8e962d6。
- 已亲看两图：轮毂管线、螺栓和轮胎细节的转动清楚；近门车体与原下踏步同位，
  已知踏步干涉保留。胎字仍不可清晰读出，不能用此图声称字样外观通过；
  内鼓被遮挡，随转结论依据数值见证而不是图中看见其内构。
- 两PNG原始共2356751B已完成授权渠道上传、文件/线程及实际文件回读。
  回取PNG编码各少511B，但1100×1000解码RGBA像素逐字相同；原始SHA不能冒充
  回取编码SHA。这里不含私人渠道/签名URL/交付收据。PNG实体不在Git/LFS，
  只保存原文件尺寸/SHA清单；不伪造新LFS指针，不用文本包塞图像字节。

保留两次先前失败：全4站首轮117.239秒到自设界限，0PNG，内存还原未确认；
第二轮放宽到足够420秒预算，但150.068秒收到非计划SIGKILL（native-9、
runner247、timed_out=false），中性9/12sample、0PNG，原因UNKNOWN。可得资料
不足以断定OOM或平台150秒限制，不改系统限额；另两次成功子进程的实际CPU/RSS/
AS限制显示unlimited，不能反推早先进程。原终态和所有raw日志逐字保留。

67原文本6643853B与来源清单由普通JSON值/引用表和5份直接可读脚本保存，31明文
表片，总出版包3522791B；父级独立恢复67原件及额外来源清单、逐字/SHA比较通过，
原3份历史失败清单也逐项核验。没有二进制资产编码。

16门仍OPEN，原下踏步安装、名义1°外倾、CV/轴承实体、候选导出和运行装配兼容
继续未验收。下一项按源码与已有FONT矩阵定位胎字为何不可读，先核实际形状/
可见性/表面与相机首命中，不把40条独立vent短痕误当字，不凭截图猜缩放或法线。

## 2026-10-02 07:38 UTC：胎字实际可见性/投影/表面有限读数

证据：`testcar/work/cloud-tyre-letter-visibility-20261002/`。同一8e母版、frame0、
官方4.5.13，CPU1/60秒界，单次18.854556秒exit0，峰RSS1850564KiB。
实际script SHA `4cd9269489d5d2c696cee613fbda3e3cdb2ba096d6ae5e52498e95e6f2c21a58`，
runner `292c2a52a5c19b719fe495b15893fc197f3cfc129d018981f3023e5a8dc2c5c5`。
没有Apply、转轮、渲染、模型保存或重跑。

- 37可见性对象=18实际MESH字模+18原SOURCE FONT+胎体；实际字模的hide_render、
  hide_viewport、hide_get均false，visible_get/visible_camera均true，原集合/
  layer路径未隐藏、排除、holdout或indirect-only。源FONT按预期隐藏，不能与
  实际字模混同。18Solidify在viewport和render均开启，厚0.850000mm、offset1。
- 36个对象分别持久化raw/evaluated两种几何读数。实际evaluated字模共2592顶点、
  5140三角面心，最近胎面normal本来全部朝+Y，没有为此翻转原绕序normal。
  顶点有符号距离范围−0.050204至+0.813057mm；面心−0.050206至+0.807023mm，
  包含故意嵌入的底/背面，不能用总范围代替所有正面的连续暴露证明。
- 实际单字框宽4.0567–11.7486px、高2.93594–12.69610px（现1100×1000近图）；
  40mm FONT size是em参数，并非实测字高。实际胎体投影框与保存的原生相机
  NDC换算框最大差0.000154484px，在0.001px算式一致性门内；不是可见性证明。
- 对_1、_10、_19各最多3个实际外侧三角面心，共9条平行正交VIEWPORT射线，
  8条先命中字模。_19三角126的一处先命中cab_0062，提前45.317778mm；该件
  hide_render=false、visible_camera=true。仅证明这个点的几何遮挡，不能
  说整字/全部文字被车体挡住，亦不替代Cycles透明材质/位移/像素可读性。
- 10434原对象矩阵逐个实读最大差0、身份集合不变，所选flags/modifier字段无
  变化，源8e与原相机记录SHA不变。全部原读数、实际argv、终态和静态18原点
  投影来源均保留。65原文本1094662B及源清单已由父级独立进程逐字恢复核SHA，
  以5个普通JSON值/引用表片和直接可读脚本/日志保存，出版包632641B，无资产编码。

这排除了“所有字模被关掉”及所测暴露点“全埋入/全被挡”的解释，但两张图的
实际不可读渲染原因仍未隔离。40条径向短痕是独立vent rods，不是18字的legend；
源码当前文案/字号/字形和历史装车适用性仍是重建值。下一步先用原材质、原几何
做更近观察/照明对照，不能凭低可读性擅自改尺寸或挪原件。16门OPEN，PNG/LFS
与模型资产状态维持前项。
