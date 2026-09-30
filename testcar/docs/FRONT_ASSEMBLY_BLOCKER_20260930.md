# 前部总成继续阶段：空间核查与 Hub 权限阻塞

项目完整目标 ACTIVE，16 项整体验收均 OPEN。本轮没有推广任何模型候选，正式资源保持上一轮探照灯修正版本。

## 已核实的进展

- 技术栈仍为 React / TypeScript / Three.js / vinext，原生母版由 Hub Blender 4.5.13 处理。
- 只读原生审计成功：任务 `b4a0a428-c7c6-4357-9d93-fc4e85651150`，结果 `work/front-assembly-20260930/front-assembly-audit.json`，SHA256 `87f6a31ed93e502bec48c66654d3f64e1b7bafba02368816e153921174c73dc7`。
- 目前中央顶板 BL_Radiator_top_hatch 长 0.43 m，范围 x=-5.565..-5.135，y=1.9595..2.0045，不能覆盖已安装发动机。
- 实际 D12A 安装外包络 x=-4.818..-3.315，最高 y=2.08009；冷却膨胀水箱盖最高 y=2.2595。中央盖必须兼顾水箱，不能仅把前面盖住。
- 旧镜背中心约 y=2.22、z=±1.68，照片中的低位圆镜和长弯臂仍未还原。
- 实际网页只读核查定位到 frame_0002 中的双圆拖环及支座。此对象还含其他车架件，不能整件删除。

## 候选代码，尚未在 Blender 验证通过

- `scripts/hub-front-assembly-model.py`：用原生 NURBS 控制网、Solidify、Bevel 建立中央薄壳盖；低位圆镜、Bezier 弯臂；按原件包围范围分离归档旧件；对 D12_/COOL_ 实体做世界坐标 BVH 表面相交检查。前缘低、后部抬升以避开水箱。均为照片拟合尺寸。
- `scripts/hub-front-bumper.py` 与其源片段 `hub-front-bumper-body.py`：厚箱梁、Boolean 中央凹口与端部收角、单拖钩、下护板；局部归档双圆拖环及支座，保留其余 frame_0002。尚未提交此依赖任务。
- 两个完整脚本通过本机 Python 语法编译，仅代表语法有效；不等于原生几何、安装、外形或功能通过。
- `scripts/hub-front-task.mjs` 保存提交体、上传文件和幂等键，修复操作必须先确认旧任务 failed，避免重复作业。

## 失败与真实阻塞

1. `e226a00a-c1e8-4584-9b3f-32ffeea35c11`：脚本第114行字典键拼写造成 SyntaxError。已修正，并在重新提交前完成语法检查。旧候选没有推广。
2. 修正任务 `6e95834d-f419-495b-9e5b-9e6b9b561d87`：Hub 返回 `runner_error`，`WinError 5`，原子替换 `state-*.new` → `state.json` 被拒绝，路径位于 `F:\InferenceHub\data\blender\6e95834d-f419-495b-9e5b-9e6b9b561d87\ab315ce4-29d2-4d0b-82b8-6efceb0688ba\`。
3. 后续只读回查确认 state=failed、result.files=[]、exit_code=null，stdout/stderr 均为空。没有候选可合法下载，也没有模型执行完成证据。
4. 同时 `/health` 返回 ok、服务 PID42948，`/health/blender` 返回 ready，4.5.13 可用；这些就绪状态不能证明写入故障已恢复。

最小恢复动作：请 Hub 运维检查该任务目录状态文件的锁占用与服务账号实际写入条件，恢复服务正常原子写入后告知。不能凭此故障擅改系统安全设置、停止其他任务或绕过 API 直接写 Hub 目录。故障确认恢复后再提交修复候选；不要将失败任务当作在途任务重复启动。

## 未测与下一步

原生曲面是否实际生成、机械与驾驶室干涉、曲面法向/UV/材质、正式 GLB 的无关字节保留、多视角照片匹配、四门全行程、浏览器导出均未测。保险杠候选未提交。风挡增高与轮廓仍待实施。完整机械动力学、厂家尺寸和完整质量 FPS 未验收。

恢复后先完成中央盖/镜臂候选的原生审查和多视角网页检查，再处理保险杠与风挡，继续动力罩长度、冷却安装、后部箱体与行走件。不得降低验收标准。探照灯尺寸标定、旧位置 AO 和灯具功能继续 OPEN。

本轮新的真实网页现状截图位于 `outputs/front-assembly-20260930/`，只显示未修改正式资源中的缺口，不标作修复后截图。Slack 原线程：PRIVATE_SLACK_DELIVERY_LINK 。
