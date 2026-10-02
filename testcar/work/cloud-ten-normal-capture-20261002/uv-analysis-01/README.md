# 十件已保存 raw 的 UV 对应差异：只读数值定位

2026-10-02；基于 HEAD `4b896eb0e249c136cd4bbb757542fee8345b75f3`。

结论：本次 fresh evaluated UV 与 run03 的 evaluated UV 存在真实的微小
float32 数值差，不能靠负零解释。没有查到采集/重放的 UV 读取、翻转实现错误，
也没有在所读官方路径发现原 mesh UV 的写回。具体是哪一步评估产生差异尚未证实。
这里不修改 UV、阈值、旧报告或门条件，不声称修复运输/整车验收。

## 已证事实

- 十件原 GLB 的 `TEXCOORD_0` 有向三角签名逐件精确等于 run03 reference；
  现存 fresh raw 逐件重放则精确复现 run-01 的失配结果。两组记录没有混用。
- 每材料桶按原始 glTF 坐标 `POSITION` float32 字节建立有向三角对应，只允许
  循环旋转，不允许反向。50,680 个三角位置键唯一。
- 八个波纹套各有96个双重位置组，共1,536个三角；仅用对应位置上的转换后
  `NORMAL` 精确数值相等进一步区分。每组候选关系都是唯一双射，UV不参与
  配对。因此52,216个三角、156,648个角点全部覆盖，未剩歧义。
  此处数值相等按 IEEE 比较接受 ±0；未改任何属性数组，也未运行正式 +0 门。
  在这1,536个细分三角中，NORMAL相等由候选配对条件保证，不是独立的法线
  验证；另外50,680个仅靠POSITION唯一配对的三角，NORMAL相等才是独立
  检查结果。前述唯一双射仍证明这些材料桶中POSITION字节与NORMAL数值的
  联合三角多重集可一一对应，不证明包含UV的完整联合属性已通过。
- 共34,490/313,296个 UV 组件有非零差值，涉及32,406个角点、25,662个三角。
  所有差异为1–5 ULP，最大绝对差 `4.76837158203125e-7`。UV中没有负零，
  因而 UV byte 差与 numeric 差计数完全相同。
- U和V都有正负两向差值，不是单一常数偏移；再翻转V或交换U/V均不能精确
  对上。脚本只计算这两种反事实诊断，未应用变换或修改数据。
- 全部对应角点转换后的 NORMAL 数值差为0；23,828个字节不同组件仅是
  fresh 的 -0 对 GLB 的 +0。这是本次明确配对上的观察，不代表完整联合属性
  已匹配，更不代表新 raw 是遗漏的历史 raw。

| 对象 | UV非零差组件 | 最大绝对差 | 最大ULP |
|---|---:|---:|---:|
| BL_Front_mirror_face_-1 | 632 | 1.7881393432617188e-7 | 3 |
| BL_Front_mirror_face_1 | 594 | 1.7881393432617188e-7 | 3 |
| S543_0_halfshaft_bellows | 3714 | 4.76837158203125e-7 | 4 |
| S543_1_halfshaft_bellows | 4476 | 4.76837158203125e-7 | 4 |
| S543_2_halfshaft_bellows | 4554 | 4.76837158203125e-7 | 5 |
| S543_3_halfshaft_bellows | 3540 | 4.76837158203125e-7 | 4 |
| S543_4_halfshaft_bellows | 3132 | 3.5762786865234375e-7 | 4 |
| S543_5_halfshaft_bellows | 4422 | 4.76837158203125e-7 | 4 |
| S543_6_halfshaft_bellows | 5250 | 4.76837158203125e-7 | 4 |
| S543_7_halfshaft_bellows | 4176 | 4.76837158203125e-7 | 5 |

精确例子：`BL_Front_mirror_face_-1`，材料`Worn_steel`，fresh三角2的loop6
对原GLB三角2的vertex25，U从fresh的`0.7807318568229675`对到GLB的
`0.7807319164276123`，差`-5.960464477539063e-8`（1 ULP）。V均为
`0.5165693759918213`。完整位置、float32位模式及各件最大差例子在JSON中。

## 实现核查与尚未证明的原因

固定源码位置均来自 `../capture.json`，全部原输入SHA在本结果中再次实读确认：

- `export_native.py:36–39,458–463`、`capture_native.py:70–73`、
  `replay_capture.py:94–101` 和官方 `primitive_extract.py:1413–1426`
  均用 float32 `foreach_get('vector', ...)`，随后 `V *= -1; V += 1`。
  U不变。因此已实测的U差不可能由这些一致的V翻转语句造成。
- fresh `capture_native.py:148–155` 与官方 `nodes.py:309–311` 都调用
  `evaluated_get(depsgraph)` → `to_mesh(preserve_all_data_layers=True,
  depsgraph=depsgraph)`，不是这两个API参数不同。
- 官方 `mesh.py:54–77` 在primitive采集之后调用`gather_mesh_hook`，
  `nodes.py:362–371` 在其返回后才清理同一个临时mesh。UV翻转和UDIM处理
  都操作独立NumPy缓冲；`gltf2_blender_utils.py:32–37`的零符号规范也只
  操作结构化NumPy数组。所读路径没有把这些结果写回原mesh UV。
- 上下文并非完全相同：官方 `nodes.py:284` 在评估前调用原mesh的`validate()`，
  fresh capture未调用；run03有更广的preflight和导出遍历，而fresh仅评估十件。
  官方最初的UV提取在三角计算前，旧hook和fresh捕获均在各自三角计算后取UV。
  这些是候选差异点，不是已证根因。
- run03 `native-report.json` 明确 `cross_evaluation_uv_determinism=NOT_CLAIMED`，
  `source_memory_preserved=true`且`changed_authored_sections=[]`。
  文件/原始数据保护不保证不同评估上下文生成完全相同的modifier UV位模式。
  BEVEL插值、validate引起的重算、依赖图缓存/顺序/浮点计算顺序均仍是假设。

目前没有充分证据支持唯一的模型或UV修复，不应为了过门改UV、归零、重排或调
epsilon。唯一建议的后续证据流程修正是：在下一次本来就需要进行的官方导出中，
从同一次 `gather_mesh_hook` 的同一个 evaluated mesh 同时持久化 raw数值、
对应数组与reference，避免再以另一次fresh评估倒推旧raw。本项未准备或执行
该导出，亦不建议仅为本差异盲目重导134MB资产；当前历史缺口不能追溯补成旧证据。

## 固定输入与重放

`analysis.json`包含13个原固定输入的路径/长度/SHA256、十份raw、原run-01
replay、run03报告、采集/重放代码、额外官方`mesh.py`及本脚本的SHA256。
执行前后全部相同，原raw的所有buffer SHA在解包时也逐一确认。

- 源blend SHA256：`48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea`
- 原GLB：134267928B，SHA256 `e99d275080737a520293c548d947401c6910cda3bc86d101dc57396bee9c587d`
- run03 reference SHA256：`32901de5c6e092bada794ff49e5f469f61e3fbe1955d7f3f921025016b288b53`
- 原helper SHA256：`f67acdccdf722752ab7f876fd23de6130570b0d36e0f33e2bff550a1d8086860`
- 官方primitive_extract SHA256：`884ba7f2691f1c69874c148a3058791b0621740dc5c7123799f6785fc3c87fa7`

在仓库根目录执行，输出必须为本目录下尚不存在的新文件：

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/4.5/python/bin/python3.11 \
testcar/work/cloud-ten-normal-capture-20261002/uv-analysis-01/analyze_uv.py \
--output testcar/work/cloud-ten-normal-capture-20261002/uv-analysis-01/analysis-replay.json
```

本次使用官方bundled Python3.11.15/NumPy1.26.4，核对runtime完整身份，
CPU affinity限制2核，实际终态exit0、墙钟5.27秒。没有启动Blender、采集、
导出、重新审计整车或改写输入。本目录三项产物与权威进度一起通过GitHub插件完整外存。

`FRESH_NOT_CORRESPONDING_RUN03`及正式+0比较`NOT_RUN_OLD_REFERENCE_MISMATCH`
保持；`FAIL_STATIC_NATIVE_TRANSPORT`、2299issues、raw-vector的2e-4门限、
全部16 OPEN和browser QA NOT_RUN均未更改。
