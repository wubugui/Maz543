# 十件保存法线的只读分类

`classification.json` 是 **DIAGNOSIS_ONLY_NOT_ACCEPTANCE**，不是新验收门。
实现基线为 `5c3bf6c4b13f8846fa7b93bb3779b3de6fd92f93`；已冻结的
`design.md` 与所有历史文件未改。只读取原保存数组和原 GLB，没有启动
Blender、求值、重采样、渲染、重导出、修改模型/UV/法线或另存 GLB。

## 实测结果

- 范围仅两镜面和八波纹套：104256 原 loops、52216 三角、156648 展开
  corner、469944 法线组件次数和 313296 UV 组件次数。展开次数可能重复同一 loop。
- 材料及精确有向 POSITION 唯一配对：50680 三角、152040 corner、456120
  法线组件；原转换向量 `s` 对实际 GLB `g` 的数值差为 0，21284 组件仅零符号不同。
- 重复 POSITION 经精确数值 NORMAL 唯一细分：1536 三角、4608 corner、13824
  法线组件；数值差为 0，2544 组件仅零符号不同。这组相等是选配条件，不能当作
  独立 NORMAL 验证。两组均实测，不从旧合计23828臆分；未决组 0，UV 未用于配对。
- 两组运输方向角/弦长为 0，均无方向排除项。没有先 normalize 再比较向量，
  也没有新增角度容差、角度 PASS 或总体 normal PASS。
- fresh 镜面最坏向量差角点的原长度 0.259321004152298，raw→复现转换误差
  0.740678995847702，方向角 0；波纹套对应原长度约 0.706304904、向量误差
  0.2936951594677212、方向角约 0.0052513°。报告保存各自 r/q/c、loop/vertex
  及真实三角引用；平方差分解只用同一个角点，不混合不同最大值。
- 原 GLB 的十件 UV 签名仍与 run03 精确相同；fresh 有34490组件真实差：
  1/2/3/4/5 ULP 分别为26208/7170/1052/48/12，最大绝对差
  4.76837158203125e-7，零符号差0。位置/法线结果不能推出全属性保真。
- 原 `FAIL_STATIC_NATIVE_TRANSPORT`、2299 issues、2e-4 raw-vector 门、
  `FRESH_NOT_CORRESPONDING_RUN03`、正式 +0
  `NOT_RUN_OLD_REFERENCE_MISMATCH`、browser QA `NOT_RUN` 及16项 OPEN 全保留。
  fresh raw 不补成缺失的历史 raw；幅值资格、native方向正确性、UV根因、切线/
  着色等效及其余整车范围仍未确定。

## 实现与验证

`classify_normals.py` 复用固定 `replay_capture.py` 的精确数值读取、原float32
转换和旧记录重建，以及 `analyze_uv.py` 的有向POSITION分组、取值和逐组件比较。
新增的最小配对段仅暴露原配对依据；实际全部桶的计数、未决项、法线/UV比较及
签名逐项对回原 `uv-analysis-01/analysis.json`，再分组统计。

原输入读取器拒绝非有限保存数组；方向函数对合成 zero、rounded-zero/fallback、
nonfinite 明确给 null/原因，并通过严格JSON序列化检查。统计分清 count、
finite_count、nonfinite_count 以及方向 valid/excluded；旧nonzero最大值仍用
转换后的原 `~zero` 掩码，未换成方向 eligible 掩码。

固定官方 Python 3.11.15 / NumPy 1.26.4，CPU affinity `[0,1]`。
`run_bounded.py` 每次27秒上界，超时杀死自有子进程组并记录真实退出码；本轮无超时。

- 一次真实分类：2026-10-02 22:52:56 UTC 开始，6.882184秒，exit0
- 五组小测试：22:53:09 UTC 开始，0.565985秒，exit0；`tests.log` 完整记录5/5
- 测试覆盖固定角点/旧判定、方向有效域/幅值、零符号与1ULP、方向/材料/多重性/
  条件配对、真实范围/UV/旧门/输入保护；不是全车验收
- `classification.json` 保存40项输入的前后字节数和SHA256，全部一致；测试后
  再核相同输入。包含原源、原134267928B GLB、原比较器/旧报告、设计、旧证据和
  本次代码。`verification.json` 记录最终核验；`MANIFEST.json` 列出本次新文件

使用 capture.json 内的绝对 bundled_python 路径执行 `-B run_bounded.py diagnosis`
及 `-B run_bounded.py tests`。固定输出使用独占创建，本轮已冻结，不能覆盖后重跑。
这是只读旁路工具，不由历史比较器调用，不影响历史退出状态。本包未自行commit/
push或发送外部进度报告；完整发布由父任务处理。
