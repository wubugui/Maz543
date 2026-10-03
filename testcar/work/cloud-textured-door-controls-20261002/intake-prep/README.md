# 当前 Textured 门控：一次窄范围只读采集准备

阶段：MAZ_TEXT_TEXTURED_DOOR_INTAKE_4514。状态：PREPARED_NOT_EXECUTED；
实际纯检查结果以本次恢复后重新生成的preparation-checks.json为准。本目录仅准备源码、固定输入清单和纯测试；
尚未打开 Blender、采集当前原生字段、识别轴、安装控制或生成模型。
必须先审查、完整插件发布并独立核回本准备，再由负责者启动一次读取。

固定源：100052636 B，SHA256
`48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea`。
本阶段官方 Blender 4.5.14 LTS/build62c1db4208e8 的路径/163613240 B/SHA、bundled Python 3.11.15、
NumPy 1.26.4、24项实际输入全在 `inputs/intake.json`。CLOUD_CONTINUATION
不作为固定计算输入，避免正常发布进度后使准备失效。固定父目录三个文件不改。

## 读取与保护

- 四原 EMPTY pivot（002/003/006/007）及 cab/root：保存 authored变换全部
  location/rotation_mode/latent Euler/quaternion/axis-angle/scale/delta分量、
  basis/local/parent-inverse/world矩阵、custom/UI、AnimData及action slot、NLA
  strips、drivers/变量/目标/keyframe/sample/modifier、constraints、链接/override。
  当前20 MESH保持原父边/共享data/材料/合并表示，完整记录其相同对象字段。
- 几何只读20门原mesh。复用固定 native-door-axis-controls.py 的
  mesh_signature 定义：坐标/拓扑/选择隐藏seam/sharp/smooth标记、所有该定义
  支持的原生attribute payload、UV层/UV值、材料、deform weights、shape keys。
  记录实际字段清单；未枚举RNA和运行时缓存不受此声明保护。未知属性读取
  不给白名单：保存不完整状态并使完整保护资格失败，但仍尝试保留原拓扑。
- 20份 `.raw.json` 保存float32原坐标、int32 edge端点、loop vertex/edge、
  polygon start/size/material，以及原world矩阵和签名。采用已固定pack/unpack
  数值JSON，逐缓冲保存LE字节数/SHA并实际读回，保留负零。没有三角化、
  depsgraph/evaluated_get/to_mesh、frame_set、原生mesh/operator修改。
- 四绿色原拓扑先写raw、读回，再由纯函数按edge索引分连通组件；坐标相同
  不焊接。保全原vertex/edge/loop/polygon索引和正反映射、计数、local/world
  bounds/顶点质心、三条PCA基轴的投影/径向范围、精确投影极值重复数。
  Fraction只判表示数值的精确仿射rank，不加几何epsilon；近简并保持未知。
  PCA方向/符号、192v/380组合fan计数均仅描述，绝不据此宣布barrel身份。
  组件错误会独立记录，已保存raw仍可离线重做；没有自动唯一匹配或轴选择。
- 保存8522对象名/父边/四矩阵原值。552原action完整读取已枚举属性、曲线、
  keyframe/handle/easing、samples、modifier、groups/slots/layers/channelbags、
  pose markers后，保存每action精确摘要、计数、共享字段清单及fake-user；
  全对象AnimData绑定按实际读取值签名，并明确其action/slot。原.blend已完整
  可恢复，不在JSON复制全场每个key数值两遍。旧action_record和graph snapshot
  的固定算法在原始门数据落盘后，另对4.5.13原552 action摘要、8522名字/父边/
  world精确基线。任何差异保存expected/observed，明确挡轴/后续安装；现有历史
  记录只有hash的字段不伪造原数值，也不逆算hash定位具体坐标。
- 前四轮joint/carrier/brake/spin/drum及upright/kingpin对象与祖先字段实读，
  精确核原身份/父边/XYZ spin/slot绑定；不读其几何、不求值、不旋转。历史
  4.5.13的132 raw/128 evaluated/7 material证据只pin历史来源，不转给新版通过，
  保留原UV门与timeline门。本次前后不变保护与跨旧版本对应是两个结果。
  六控制与20门及其data的直接ID users另列；这不是完整外部依赖白名单。
- 前后完整快照使用相同序列化，无阶段标签。如果逐字相同，Git可复用一个
  blob。所有固定输入、准备源码/说明/清单均由runner前后SHA核对。不会修改
  源、原输入、action、custom/UI、selection、visibility、UV、normal或材料。

Action按当前官方4.5.14 `is_action_layered`区分存储；layered只读channelbag groups，
不访问Action.groups legacy兼容集合。官方UI的分支用法已固定为第24项输入。
所有helper仅AST选取明确只读函数；不import旧建模脚本、其全局赋值或入口。
runner从已发布run_capture.py缩小改写，避免建立新进程框架。未知constraint、
modifier、AnimData、已有控制属性或library/override始终列阻断，采集不会删除、
覆盖、自动修复或默认批准它们。是否同效控制需审原值，不由无AnimData假设代替。

## 执行边界与命令

计划只运行一次、CPU2、120秒操作界，计时从前置hash开始；预留末尾10秒，
原生终态观察最迟在110秒。前置后不足60秒native余量就不启动。
10秒心跳附当前stage；Popen.poll/wait观察真实终态。超时只清理由这次
Popen创建的session进程组，TERM2秒/KILL3秒，失败/真实code留档，不猜PID。
最终输入hash用时也纳入120秒PASS门；清理阶段若导致越界如实失败。
此前4.5.13同源fresh-open约12.25秒、窄raw约12.02秒仅支持预算，不证明4.5.14
兼容性或本次性能。本阶段只读使用已核验现有4.5.14安装，不复制/修改其它项目
工具；4.5.13下载403后已停止，不改变或重标任何旧实验。

审查、发布、核回后，负责者应填真实并行窗口说明，再运行（本准备未执行）：

```sh
cd /workspace/scratch/a29d03198654/Maz543
/workspace/scratch/a29d03198654/tools-feiting/blender-4.5.14-linux-x64/4.5/python/bin/python3.11 -B testcar/work/cloud-textured-door-controls-20261002/intake-prep/run_intake.py --output /workspace/scratch/a29d03198654/Maz543/testcar/work/cloud-textured-door-controls-20261002/intake-prep/run-01 --window-note '填写实际并行任务状态'
```

runner使用当前允许CPU集的前两个核，并设置OMP/OpenBLAS/MKL线程2；Blender
参数固定 `--background --factory-startup --disable-autoexec --threads 2
--python-exit-code 1 --python collect_native.py -- --output ...`。只open保存frame0/
subframe0，绝不推进时间线。已有run目录拒绝覆盖，失败现场保留不原地重试。

预计33个输出文件：20 raw、4组件、2保护快照、native report、日志、心跳、
stage/stages、launch/process。JSON总量预计约10–25MB，主要为两份8522对象
矩阵快照；只是准备估计，实际byte/时间须运行后报告。前后相同快照可共blob。
不生成.blend、GLB、图像或新的大型候选。

## 状态解释与准备验证

`CAPTURE_COMPLETE_GUARDS_PASS`只表示原字段采集/明列保护完成。
`axis_identification`始终单列：跨版本差异/未知依赖/保护失败时BLOCKED，否则
仍为NOT_IDENTIFIED_REVIEW_SAVED_RAW；安装资格始终阻断，未识别轴不能安装。组件摘要
是否完成、依赖阻断、控制安装NOT_RUN分别报告。即使采集exit0也不代表轴
唯一识别、门控制可装、已安装或整车通过。六原闭门接触OPEN、16整车门OPEN、
全时间线NODES资格BLOCKED原样保留，70.342mm没有成为事实或准入假设。

准备检查仅：四执行/测试源码及输入重建配方语法编译（不写pyc）、两个Python --help（不import bpy）、
官方bundled Python下4组纯NumPy合成负控：同位不连接、多解不选择、非连续
索引双向映射、非法索引/loop关系/非有限坐标拒绝。另以纯伪action验证layered分支不会访问legacy groups；没有真正读取新native。
`preparation-checks.json`冻结各文件bytes/SHA以及实测检查结果；其自身SHA由
最终工程清单/发布核回固定。准备后停止，任何改动必须重新审查冻结发布。

恢复说明：未发准备源码由本任务可见工具文本与按序补丁恢复；旧preparation-checks
不可复用。RECOVERY.json保留恢复与新版本阶段事实，本次正式清单需重新冻结。

发布说明文案修订：已执行run-01的原准备以提交
`eaedd2af47019a582b527e8d017a18c5ecc751d3`中的版本及校验为准；
本次仅修订说明措辞，原准备检查和运行记录未改，不表示新测试或原生运行。
