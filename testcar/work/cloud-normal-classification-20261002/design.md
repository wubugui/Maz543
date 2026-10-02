# 法线分类旁路报告：最小设计，冻结待窄审

2026-10-02；基线 `befb797359a86732aba4ce6b05de6fb835e42a16`。只新增本文。
拟议报告只读已保存证据；不实现比较器、不改历史文件/epsilon，不采集、导出或运行Blender。
`validate_export.py`及`decoded-validation.json`逐字保留，旁路不参与其控制流或退出状态。

## 1. 证据及代码依据

路径缩写：`E=testcar/work/cloud-native-static-export-20261002`；
`C=testcar/work/cloud-ten-normal-capture-20261002`，均相对仓库根。

- **旧门**：`E/export_native.py`，`NativeReference.gather_mesh_hook:419`，448–455行计算raw到本地复现官方转换的欧氏差，499–500行存原两个最大值；它不是raw对GLB的方向误差。`E/validate_export.py:31–40`仍以原nonzero最大值与`normal_nonzero_vector_error=2e-4`比较。`E/run-03/native/decoded-validation.json`保持FAIL及2299issues。
- **fresh测量/资格**：`C/run-01/{replay-report.json,result-summary.json}`；`C/replay_capture.py`的`conversion:69–78`、`statistics:141–202`分别定义转换和长度/角度；`analyze:238–285`核完整旧记录后才运行正式+0门，目前仍`NOT_RUN_OLD_REFERENCE_MISMATCH`。
- **实际GLB诊断**：`C/uv-analysis-01/{README.md,analysis.json,analyze_uv.py}`；脚本`triangle_groups:28–37`与`compare_bucket:67–141`保持材料桶、精确有向POSITION及重复组多重性，仅NORMAL可细分，UV不参与挑配；`field_comparison:49–64`分字节/数值/零符号差。
- **解码及精确签名**：`C/capture.json.inputs.decoder`指向`E/validate_glb.py`，`_GLB.accessor:98–114`、`oriented_signature:26–58`；仅允许循环轮换，保留方向、联合角点属性和多重性。单属性hash不证明联合绑定。
- **官方实现**：绝对路径与SHA取`C/capture.json.inputs.official_primitive_extract/official_unique`。`PrimitiveCreator.__get_normals`在`primitive_extract.py:1428–1476`；`normalize_vecs:80–82`、`zup2yup:85–88`；同插件`io/com/constants.py:159`为round4。`gltf2_blender_utils.py.fast_structured_np_unique:8–37`规范结构化浮点零符号；NORMAL在1478–1482行写入该结构，POSITION按vertex_index另取。只确认实现行为，未据此证明native非单位幅值的规范语义或合格性。

## 2. 算法与最少字段

固定官方Python3.11.15/NumPy1.26.4；仅静态无skin/morph路径。
`r`为保存的float32 raw，`q=round(r,4)`，`c`为依原float32顺序归一化q并将exact-zero替换native+Z的结果；`s=yup(c)`，`g`为同一glTF局部坐标下明确配对的GLB NORMAL。原缓冲不变，度量用float64。

新增一个旁路`normal_diagnosis`对象，不建立新验收框架：

| 字段组 | 最少内容和定义 |
|---|---|
| `scope` | 十对象/mesh ID、证据路径/SHA/runtime，标`fresh_run01`；原loops与展开triangle-corner分别计数 |
| `preserved_qualification` | 原FAIL、2299、2e-4、16 OPEN、browser QA NOT_RUN；引用旧报告，不能覆盖它 |
| `native_raw` | `length=||r||`、`distance_from_unit=abs(||r||-1)`的count/min/max，zero/nonfinite计数，最坏corner；仅测幅值，不设新的单位容差或合格门 |
| `official_conversion` | `round4_vector_perturbation=||q-r||`、`converted_length=||c||`、`raw_to_reproduced_vector_error=||c-r||`、原nonzero掩码最大值、`direction_angle_degrees`及`direction_chord`、fallback数和方向排除原因 |
| `correspondence` | 原`legacy_record_status`；POSITION唯一/NORMAL细分/未决组各自计数与依据 |
| `converted_glb_transport` | 分`position_only_independent`与`normal_refined_conditioned`组：三角/corner/component分母、数值差/字节差/仅零符号差计数、`max_vector_error=||s-g||`、`max_direction_angle_degrees`、方向排除原因 |
| `attribute_binding` | 引用旧all/UV签名、UV真实差/ULP、正式+0门状态；位置或法线结果不推导全属性通过 |

方向算法：分别将两向量以float64长度归一化为u/v，角度为`degrees(atan2(||u×v||,u·v))`，弦长为`||u-v||`。raw-zero、rounded-zero/fallback、非有限值方向记null并计原因；运输阶段遇零/非有限向量同样不生成假0。运输的数值/字节差比较s/g本身，不能先归一化掩盖幅值差。

对同一有效角点，令a=||r||、b=||c||，有`D²=(a-b)²+a*b*||u-v||²`。幅值与方向项可共存；不把不同corner最大值代入，不把大D全称为方向丢失。

仅在新报告中，将原`raw_to_official_normal_max_nonzero_error`展示为“raw→复现转换的非zero最大向量差”，映射到`official_conversion.raw_to_reproduced_nonzero_max_vector_error`并保留`legacy_field_name`与原值/来源。历史JSON键、`~zero`掩码及2e-4比较均不改；`direction_acceptance_limit=null`，不生成角度PASS门。最坏corner附object、loop/vertex、triangle引用和r/q/c。

运输只用事实标签`NUMERIC_EQUAL_WITH_ZERO_SIGN_DIFFERENCES`、`NUMERIC_DIFFERENCE_OBSERVED`或`UNRESOLVED_CORRESPONDENCE`，必须附配对依据；NORMAL挑配组不算独立法线通过。三段结论不能合并为一个“normal PASS”。

## 3. 已支持的分类与限制

- fresh镜面最坏向量差corner：raw长度`0.259321004152298`，D=`0.740678995847702`，该corner方向0；镜面全loop最大方向角是另一corner的`0.0045584343718963844°`。波纹套对应长度`0.7063049039932805`、D=`0.2936951594677212`、方向约`0.005251303172427886°`，全loop最大`0.00525181837333352°`。这些最坏corner均被三角引用，支持大D有显著幅值贡献。
- 原采集104256loops；GLB配对展开为52216三角、156648corner。50680三角仅POSITION唯一，1536三角用精确NORMAL细分，无未决组。469944个NORMAL组件次数中数值差0，23828次仅零符号差；**组件次数可重复同一raw loop，不是独立loop/vertex数**。后1536三角的相等是配对条件，只证明条件下联合多重集相等。现存JSON只给NORMAL合计差数，按依据拆分的零符号/角度统计未单独输出，对应字段记null/unknown，不编造分组数字。
- 十件GLB UV签名精确等于run03；fresh有34490/313296个展开UV组件真实差，1–5 ULP、最大`4.76837158203125e-7`、零符号差0。完整旧对应仍`FRESH_NOT_CORRESPONDING_RUN03`，正式+0门仍NOT_RUN；不能用位置保真推导全属性保真。
- `testcar/work/cloud-normal-transport-diagnosis-20261002/analysis.json`对缺失历史raw幅值的结论仍为附假设推断。fresh测量不能补成旧raw。现证据未证明UV根因、原生方向正确性、幅值资格、切线/着色等效或其余全车；16门仍OPEN。没有必要为本报告重导134MB；同次hook保存raw/reference仅可在未来本来就需要的官方导出中另议。

## 4. 未来实现最小测试需求（本项未运行）

1. 固定镜面/波纹套corner复核别名等于旧值；镜面D仍超2e-4且方向0；分开幅值/方向，旧判定不变。
2. raw-zero、round4归零、非有限值均排除方向并记原因；反向约180度；同向不同幅值不能被0度掩盖。
3. ±0只产生字节差；非zero分量1 ULP变化必须报数值差。POSITION负零和通用签名仍字节敏感。
4. 循环轮换可接受；反向、材料混桶、多重性/唯一双射失败不得接受；NORMAL细分不可充当独立验证，UV不可挑配。
5. 保持十件/loops/三角分母、原UV真实差、+0 NOT_RUN及FAIL/2299/2e-4/16 OPEN；旧比较器与报告hash不变，未覆盖部分不得补通过。

冻结后仅交窄审；本文未触发任何实现或新原生任务。
