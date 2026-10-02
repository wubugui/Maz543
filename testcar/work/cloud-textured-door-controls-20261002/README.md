# 将门轴控制整合到当前 Textured 前轮候选

当前阶段只读现存已发布记录，尚未打开 Blender 或修改源。目标是基于当前
100052636B、SHA48dbc498 的 Textured 前轮源形成一个整合候选，保留已有轮链
和材质合并。旧67.9MB Master门控候选作为历史证据，不能直接改其脚本SHA套用。

`static-findings.json` 由 `summarize_saved_doors.py` 从固定原文件直接生成：
四个 pivot 沿 cab → MAZ543_REFERENCE_CHASSIS，均 EMPTY/QUATERNION；其
保存 basis 与旧 Master 门scope精确相等。但当前每门只有5个直接MESH，共20件：
handle、lock、window、合并绿色网格、合并橡胶网格。旧44名称仅12名仍存在，
其余为已合并表示，不是丢失零件，不得拆回或重造44对象迎合旧检查器。

同源 native 库存中的 action_slot_handle、action_blend_type、action_influence
四门均为null。固定 inspect_native_graph.py:81,96–100 只有在
obj.animation_data不存在时才写这些null，因此当时没有四门旧方案所需16个
原生driver。这不是从GLB不能保存driver推断，也不代替下一次属性/constraint
现场读取；旧custom/UI内容仍未从库存逐字段保存。

blender-export.py:35–65 的原生convert/join流程及当前detail_meshes、计数支持：
每门绿色合并原fasteners+三barrel+pressed_shell；橡胶合并gap+recess+seal。
前门绿色2688顶点/4804三角，后门2712/4842；橡胶1472/2940，均等于对应
旧组件计数之和。完整名表、矩阵和输入SHA在JSON；计数相符不证明组件几何身份。

下一项准备一次只读fresh intake：

1. 实读四pivot与cab/root的原authored变换、custom/UI、AnimData/action/NLA/
   drivers、constraint与链接状态，确认无现有控制或属性冲突
2. 原样记录当前20门mesh身份、共享data、材质/属性与闭门几何；只读四绿色
   mesh的连通组件，唯一识别三barrel并测实际轴，不预设旧70.342mm偏差
3. 保护8522原对象名字/父边/矩阵、552原action及当前前轮父链；不推进时间线，
   不调用建模/Separate/保存/导出，不默认允许未知依赖

旧barrel在该合并表示前已烘焙为192顶点/380三角；旧控制脚本的原始48顶点、
双24环前置条件不能直接沿用。任何组件歧义先保留，不凭旧轴加控。以后若证据
支持修复，可复用 original_basis @ T(p−Rz(θ)p) @ Rz(θ) 形式并使用当前实测p，
保0°闭门与现有20件几何/材质/轮链；最终需原生保存、fresh-open及实际闭开门图。

静态摘要在官方bundled Python3.11.15、CPU2、30秒界内实际0.715298秒exit0；
12项输入前后SHA完全一致。只解析保存JSON和GLB JSON chunk，没有新几何实验。
六处历史闭门接触仍OPEN，模型拟合轴不是OEM机构；16项整车门仍OPEN。
