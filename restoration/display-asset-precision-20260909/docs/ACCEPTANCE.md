# MAZ-543A product demonstration acceptance

**最新：[显示资产精度与切线追踪](DISPLAY_ASSET_PRECISION_20260909.md) 已核实旧 Draco 量化造成细面/切线损失；实际整车导出保护性修正 616 个切线，82 个真实表面问题仍未通过。两件原生对象的零量化压缩保持全部三角形角点属性逐位相同，尚未替换运行时资产。整车仍约 0.5 FPS；完整 goal ACTIVE，16 项 OPEN，继续保精度显示优化和机械实现。**

此前阶段：

**最新：[完整显示工作线程与无损封装](RENDER_WORKER_20260909.md) 已在开发入口装配完整模型并直连 240 Hz 机械计算，界面不再依赖绘制线程返回仪表；350 MB 整车 Blob 导出的全部二进制载荷与原封装一致。整车仍约 0.3–0.7 FPS，完整校验发现 698 个切线错误尚待追踪，独立显示未默认启用。完整 goal ACTIVE，16 项 OPEN，继续保精度优化。**

此前阶段：

**最新：[独立机械调度](SIMULATION_DISPLAY_SCHEDULING_20260909.md) 已把原求解器放入固定 240 Hz Worker，保留内部悬架 480 Hz 与所有几何，显示迟滞不再丢弃机械时间；延迟一致性、真实 Worker 阻塞试验和网页启动/停机观察通过有限检查。GPU 绘制仍慢，整车性能与物理精度未验收。完整 goal ACTIVE，16 项 OPEN，继续保精度优化。**

此前阶段：

**最新：[CAD 显示优化](PERFORMANCE_CAD_DISPLAY_20260908.md) 已启用每帧单次阴影、严格显示缓存、按时间相机缓动及原生资源释放。静态机构检查恢复响应；整车仍由 Basic Render Driver 软件渲染，性能未解决。合批仅保留开发实验，因画面差异/内存和热身收益不足未默认启用。完整 goal ACTIVE，16 项 OPEN，优先继续保精度性能工作。**

此前阶段：

**最新：[四工作轮变矩器总成](CONVERTER_FOUR_WHEEL_ASSEMBLY_20260908.md) 已保存并导出 180 个实体的泵轮、涡轮、双导轮总成，应用新增 /converter，装配拆看与导出核对通过。叶型/尺寸仍为拟合，液力和闭锁动力学未完成。整车现场报告 Basic Render Driver、约 2698 万三角形及 0 FPS，必须继续核查性能。完整 goal active，16 项 OPEN。**

此前阶段：

**最新：[全表面接触与积分误差](CONVERTER_STRIP_SURFACE_CONTACT_20260908.md) 已新增全带面/滚柱接触，38 个静态形态原生保存及实体读回检查通过；最大计算应力约 9.36 GPa，真实弹性范围未通过。10 N·m 连续诊断到 1.187 秒后失败，时间积分能量误差待解决。完整 goal active，16 项 OPEN。**

此前阶段：

**最新：[弯带与外圈接触及连续受力](CONVERTER_STRIP_POCKET_CONTACT_20260908.md) 已修复扩大压缩范围中约 16.4 μm 的带材穿透，补足楔面反力与根部载荷；39 点原生检查及 352 段接触求解通过有限验证。连续外载试验已开始，10 N·m 场景进入未核查范围后中止，尚未发布动态结果。完整 goal active，16 项 OPEN。**

此前阶段：

**最新：[图件纠错与弯带弹簧研究](CONVERTER_STRIP_SOURCE_CORRECTION_20260908.md) 撤回旧圆线螺旋弹簧的原车结构假设。新弯带已有 26 个独立平衡、原生实体读回与网页逐点比对；应用新增 `/strip-spring` 可查看变形。固定座、材料、强度、连续受力与整车联动仍未通过，完整 goal active，16 项 OPEN。**

此前记录（旧圆线台架仅保留内部一致性证据，不能作为原车弹簧验收）：

**最新：[单向离合器连续台架](CONVERTER_CONTINUOUS_BENCH_20260908.md) 已保存 201 组联动姿态，弹簧实体与受力一致性、600 个帧间检查和网页顶点比对通过；应用新增可操作回放入口。双导轮流体与整车联动未完成，完整 goal active，16 项 OPEN。**


**最新：[单向离合器连续接触](CONVERTER_CONTACT_20260908.md) 已实现滚柱/内圈/楔面与弹簧受力的独立求解，负扭矩自然保持、正向越程；三种步频与 400 个实际网格姿态回放检查通过。连续弹簧网格、保存的动态原生文件、双导轮流体及网页整合尚待完成。完整 goal active，16 项 OPEN。**


**最新：[变矩器双单向离合器](CONVERTER_FREEWHEELS_20260908.md) 已建独立 Blender 组件，共用内圈、两套楔形外圈、滚柱和弹簧；68 个封闭实体、72 个端点检查及渲染已完成。当前仅离散几何检查，未安装到整车/网页，连续滚动、楔紧受力及双导轮流体驱动仍待实现。完整 goal active，16 项 OPEN。**


**最新：[带载起步诊断](TRANSMISSION_LOADED_LAUNCH_20260908.md) 已运行 12 组质量/分动挡/挡位场景及 240/480/960 Hz 步长检查。40.6 t 倒挡起步约 3.04–3.62 秒，接合加速度尖峰在细步长仍存在；固定转速台架不代表原车通过。当前运行质量仍 20.55 t，543A 型号质量、变矩器、惯量与阀体须联合核对。完整 goal active，16 项 OPEN。**


**最新：[接合计时定义](TRANSMISSION_TIMING_DEFINITION_20260908.md) 已对照 1973/1977 原文核实。带载起步 ≤3 秒与压力完全建立 2–3 秒是不同指标；当前一挡/倒挡第 3 秒仅达主路的 16.7%，95% 诊断约 4.17 秒，仍 OPEN。保留原参数，继续核对弹簧及阀体尺寸。完整 goal active，16 项 OPEN。**


Latest: [return springs and pusher hardware](TRANSMISSION_SPRING_COUNTS_20260908.md) now use 30/16/16/30 springs. The 1,755-node module, two native masters, browser and dynamic bench are synchronized. Fitted geometry/clearance and browser engagement/release checks pass. Spring material/dimensions/preload, high calculated wire stress, pressure timing, factory converter/control systems and whole-vehicle fidelity remain unaccepted. All 16 vehicle gates remain OPEN; full goal active.

此前记录（冲突时以最新记录为准）：

Latest: [friction-face grooves](TRANSMISSION_GROOVES_20260908.md) now exist on both faces of 23 discs. Saved-mesh depth, contact-land radius and closed-pack outlet centreline checks pass; native assets, runtime and bench are synchronized. The current eight springs per pack remain incorrect: catalogue quantities indicate 30/16/16/30. Hardware, spring stiffness/preload and supply-route correction are next. Browser shading and whole-vehicle performance are not accepted. All 16 vehicle gates remain OPEN; full goal active.

此前记录（冲突时以最新记录为准）：

Latest: [shared clutch parts](TRANSMISSION_COMMON_PARTS_20260908.md) now use common native/browser geometry across 68 instances in 6 catalogue groups. Shared hydraulic response and saved bench checks pass. Oil-drain grooves, factory dimensions, pressure timing, full converter/control mechanisms and all 16 vehicle gates remain OPEN.

此前记录（冲突时以最新记录为准）：

Latest: [direct-piston pressure-area reconstruction](TRANSMISSION_DIRECT_AREA_20260908.md) resolves sustained third-gear slip in the documented fitted load case. Native/browser geometry, force balance and saved bench checks pass. Factory dimensions, shared-part fidelity, converter/control mechanisms and complete vehicle performance remain OPEN. All 16 vehicle gates remain OPEN.

此前记录（状态冲突时以最新记录为准）：

Latest: [hydraulic and coupled transmission dynamics](TRANSMISSION_HYDRAULICS_20260908.md) now drive the browser and an additional native bench. Numerical and saved-file checks pass; third-gear sustained slip remains a failed model case. Factory geometry, calibration, converter/reactors/lockup, valve and pump internals and complete vehicle verification remain OPEN. All 16 vehicle gates remain OPEN.

Earlier stage record (superseded where noted):

Latest: [direct-clutch rotary feed and support bearing](TRANSMISSION_ROTARY_FEED_20260908.md) are reconstructed and checked. All four booster geometries are present, with fitted dimensions and kinematic strokes. Pressure, valve control, leakage, friction torque, converter dynamics and factory dimensional accuracy remain OPEN. All 16 vehicle gates remain OPEN.

Earlier stage records (chronological progress, superseded where noted):

Latest: [case 47 and second/reverse booster geometry](TRANSMISSION_CASE47_20260908.md)
are integrated and checked. The direct clutch rotating feed, factory geometry,
pressure and torque dynamics remain OPEN. No vehicle acceptance gate closes.

Latest: [first-gear booster geometry](TRANSMISSION_FIRST_BOOSTER_20260908.md)
has a skirted piston, fixed/moving seals and an open inlet. The other boosters,
factory oil routing and hydraulic/load dynamics remain OPEN. No vehicle gate closes.

Latest: [sliding clutch splines](TRANSMISSION_SPLINES_20260908.md) now have mating
native geometry and scoped clearance checks. Hydraulic chambers, correct moving/
stationary seal placement and load dynamics remain OPEN. No vehicle gate closes.

Latest increment: [clutch axial contact geometry](TRANSMISSION_CONTACT_20260908.md)
and round-wire spring morphs pass scoped checks in native and browser assets.
Hydraulic chambers, plate splines, forces and complete vehicle acceptance remain
OPEN. All 16 gates below remain OPEN; older stage notes follow chronologically.

Latest: the [two-row planetary core](PLANETARY_CORE_20260908.md) replaces the old
three generic rows in the browser and native vehicle masters. Rigid gearing is
checked; converter, clutch contact, hydraulic shifting, complete installed drive
and full assembly clearance remain OPEN. No vehicle gate is closed.

2026-09-08 transmission increment: published ratios, transfer-range controls and
straight-running speed inspection passed scoped checks; see
[transmission notes](TRANSMISSION_REFERENCE_NOTES.md). The old generic planetary
geometry, converter dynamics and full driveline remain OPEN. No gate is closed.

2026-09-08 continuation: circular-wire spring deformation and its full-coil browser
inspection passed the scoped checks in [the continuation record](CONTINUATION_20260908.md).
The original complete goal is active; no full-vehicle gate is closed by this increment.

The complete user objective remains open. A passing build or one working animation
does not close this checklist. Fixed hardware follows its mounting assembly; moving
hardware must follow its actual joint and load/actuator relationships.

2026-09-08 restoration increment: final cooling contact checks, native pose checks,
web export and local browser checks now pass for the existing fitted mechanism.
All 16 full-vehicle gates remain OPEN. Current evidence and next work are in
RESTORE_20260908.md; older counts, export versions and unrun-check notes below
are historical snapshots.

2026-09-06 cab-photo correction: the actual front photograph exposed an overly
narrow lower central opening. A fitted lower-inner relief and wider front grille
have been promoted to the native master after closed-facade and aperture checks.
The two current shroud/wall surfaces no longer cross at frame zero. Hidden wall
depth, exact dimensions and installed Cardan closure remain unverified; this
does not close any full-vehicle gate. See CAB_PHOTO_FIT_NOTES.md.

2026-09-06 cooling update: lower and upper local gearbox meshes, nominal bearing
envelopes and their shared animation have been rebuilt and checked. The module
now has 254 pose bindings. Source comparison exposed an unresolved Cardan flange
pattern / variant issue; installed transmission closure, original ratios,
loaded contact, full oil/water passages and complete-vehicle clearances are still
unaccepted. All 16 full-vehicle gates remain OPEN.

## Evidence sources

- S1: MAZ-543 and modifications, Technical Description, 3rd edition, 1977.
  https://djvu.online/file/zjMdLY3MFjmTL — manufacturer-era vehicle documentation,
  cached text available; local direct HTML does not contain the book. Do not treat it
  as a downloaded complete manual.
- S2: D12 engine operation manual: https://neva-diesel.com/f/rukovodstvo_d12.pdf
  Downloaded to work/reference-docs/D12-manual.pdf, 235 scanned pages. Fig.14 on
  printed p.33 explicitly shows main and articulated rods; fig.17 p.37 shows paired
  intake/exhaust camshafts. This is a D12 family manual: verify transport-variant
  differences before claiming D12A-525A-specific dimensions.
- S3: docs/REFERENCE_NOTES.md: coherent MAZ-543A exterior photo set and tire sheet.

## Gates and evidence required

| Requirement | Necessary proof | Current status |
|---|---|---|
| Accurate exterior | Variant-specific dimension table; front/side/top orthographic measurements; calibrated photo overlays; every mismatch resolved | OPEN; only axle spacing and tire envelope grounded |
| Hollow twin cabs | Four actual apertures, seats/instruments/controls; door/quarterlight seals and hinge axes; collision check through full opening | OPEN; actual apertures repaired and eight rays passed; interior detail and complete collision audit remain |
| Complete engine | D12A-525A crankcase, main/articulated rods, liners, pistons/rings/pins, 48 valves, four cams, timing drive, bearings, pump/accessory internals | OPEN; new Blender engine replaces generic seed; 48 valves/four cams/coupled rods verified; accessory internals and dimensional calibration remain |
| Engine starting and stopping | Electrical/air starting path, oil precharge, crank acceleration, firing/valve phase, governor and load, coast/stall; actual meshes follow states | OPEN; C5/MZN reduced current, pressure, inertia and governor model replaces RPM interpolation; manual/guided starts work; pneumatic start, measured motor maps, full oil galleries and thermodynamics remain |
| Fuel / air / exhaust | Tank selection, lift/injection pumps, 12 injectors, filters, intake cleaner, exhaust/ejector, measurable flow relationships | OPEN |
| Lubrication / cooling | Dry-sump supply/scavenge pumps, tank/filter/cooler/bypass; coolant pump, radiator, two fans and drive | OPEN; dual 12-blade fans, electromagnetic clutches, pump load and a conservative thermal network added; drive internals, complete passages and measured performance remain |
| Transmission | Converter pump/turbine/stator/freewheel, three-speed planetary train and brakes/clutches, two-speed transfer/differential; mesh and torque constraints | OPEN; arbitrary independent gear rotations are not valid |
| Eight driven wheel ends | Four central reducers/differentials, shafts/U-joints/CV joints, planetary hubs; gear ratios, differential constraints and steered wheel speeds | OPEN |
| Steering | Steering wheel/gear, hydraulic power assist, longitudinal and transverse rods, kingpins; measured linkage closure through full lock/travel | OPEN; wheel angles alone are insufficient |
| Physical suspension | Correct torsion rods/arms/knuckles, telescoping dampers, bump stops; spring/damper forces, wheel contact and chassis heave/pitch/roll | OPEN; source-guided Blender double-torsion module and force-based vertical solver added; hardpoints, axle-specific castings, installation and force parameters remain uncalibrated |
| Braking | Air compressor/receivers/regulator, pedal/valves/boosters/master cylinders, wheel cylinders/shoes/drums and parking mechanism | OPEN; current brake pose and scalar deceleration are insufficient |
| Electrical / cabin functions | Battery isolation, starter/generator charging, instruments, lamps/indicators/horn/wipers, heaters/ventilation; causal circuits and moving parts | OPEN |
| Other fitted chassis equipment | Variant-specific equipment inventory including tire pressure control, preheater and starting systems; no omitted fitted functions | OPEN; full inventory requires manual/catalog cross-check |
| Browser product operation | Clearly discoverable controls and each named action tested with observable 3D mechanism + state feedback, reset/stop/reverse behavior | OPEN; live partial checks cover doors, engine internals, suspension stand and electric start; full vehicle function coverage remains |
| Photoreal browser rendering | Verified actual browser closeups, front/rear/side/interior, material scale, shadows, glass, texture seams; GPU timing and responsive interaction | OPEN; reversed normals repaired and rebaked AO verified in normal browser rendering; final material/lighting/FPS review remains |
| Native editable deliverables | Updated Blender master, packed textures, mechanically named assemblies/joints; web asset parity | OPEN until full model/rig is complete |

## Current verified findings (2026-09-05)

- New suspension module has 1,716 source-indexed authored pieces, 16 torsion
  shafts and 80 semantic transforms. It is appended to both vehicle masters;
  the web downloads it independently from the body and engine.
- Four-bar closure, virtual-work torsion force, unilateral tire contact, static
  equilibrium and decay after removing road excitation passed numerical checks.
  The force coefficients and installation hardpoints remain uncalibrated.
- Native suspension sampled 41 frames with a maximum joint gap of 1.69e-7 m
  and positive piston/base-valve/guide clearances. This verifies the modeled
  articulation sequence, not a manufacturer's travel or tolerance specification.
- Tyre carrier and spin origins were recentered from 0.80 m to their native
  geometry's 0.75 m centre while preserving tyre vertices. Browser and native
  wheel/brake poses now follow the reconstructed four-bar carrier.
- Eight wheel stations can be isolated; covers can be removed; suspension can
  be paused independently; stopping test-pad excitation leaves a decaying response.
  Complete steering/CV torque phases, visual stop-contact alignment, tire
  deformation and axle-specific casting/anchor calibration remain open.

- Existing browser service was stopped; restarted and actual GLB loaded in the App.
- With default rendering, left doors and inspection lid appeared black. Disabling
  GTAO or normal mapping did not resolve it; disabling baked AO did. Blender
  outward-normal repair found reversed faces on mirrored lids and shell pieces.
- Door slider at 100 rotated four door groups, but a solid panel remained behind
  the right-side door opening. Recompute solid winding before boolean subtraction.
- Engine demo displayed internal meshes; this proves visibility only. It does not
  prove correct D12 internals, starting physics, valve count or complete linkage.
- After winding repair, all four cab openings passed two ray heights each; solid
  wall samples outside the openings still hit. Single-door browser operation
  reached 99 degrees with the other three at zero; visible cabin aperture is clear.
- Current D12 Blender module has 1,900 registered engine pieces and 148 named joints.
  See docs/D12_REFERENCE_REGISTER.md and outputs/d12-parts-register.json for source
  and dimension status. Original factory photographs and KMZ 525A photos were
  inspected alongside D12 manual figs.11–18 and target MAZ figs.7–9. C5 is now
  a separate detailed starting module; complete/calibrated acceptance remains open.
- 2,881 geometric samples preserve both rod lengths and the shared articulation.
  Fitted strokes are 180 and 186.7 mm with equal top dead centres; this is not a
  measurement of actual rod dimensions. Cam flat-tappet envelope consistency is
  within 0.005 mm in the geometric check, not a claim of manufactured tolerance.
- New D12 GLB validation: zero errors and warnings. Browser loaded the new engine
  and its inspection panel; actual assembled/open-head/paused checks continue.
- Native Blender geometry passed 61 sampled frames: both rod joints remain closed
  and actual lobe/tappet surfaces agree with the authored law. Browser assembled,
  open-head, longitudinal section and pause/resume were inspected; see
  docs/BROWSER_QA.md for current measurements, fixes and remaining limits.

Goal completion is forbidden while any row is open or only supported by indirect
evidence. Add source-backed dimensions and runtime observations as each subsystem
is implemented; do not turn omissions into successful acceptance conditions.

## Electric starting pass (2026-09-05)

- Native C5/MZN module: 167 source-indexed authored pieces, seven moving
  transforms, eight packed reference images. The MN-1 stator detail uses an
  owner-identified dismantled specimen; early-production identity and dimensions
  remain unconfirmed. Armatures, brushes, commutators and winding connections are
  still incomplete. The C5-2S cutaway is identified as a later suffix reference.
- The separate browser asset replaces the previous simple starter and block-tooth
  ring. The original eleven-tooth pinion count is retained; ring count/module,
  spline lead, friction-stack count and installation pose are fitted parameters.
- Actual authored rest gap is 3.5001 mm; the original manuals specify a range.
  Native checks found no surface intersections across 20 meshed C5 frames and
  41 MZN gear frames. A 4,401-angle planar check also found no gear overlap.
  These checks establish clearance in reconstructed meshes, not factory tooth
  geometry, backlash certification or a contact-force solution.
- Fourteen native samples of all 138 D12 joints follow the same starting crank
  angle as the C5 ring. Maximum sampled rotation deviation is 1.28e-5 rad.
  The preoil pump follows the frame; the starter follows the engine mounting.
- Browser starts now depend on simulated battery current, preoil pressure, shaft
  inertia, starter drive engagement and fuel-enabled engine torque. Manual mode
  preserves independent buttons; guided mode follows the documented procedure.
  Releasing manual start no longer traps the pinion at partial engagement.
- The model uses uncalibrated aggregate electrical, hydraulic and combustion
  coefficients. No completion is claimed for the full starting, electrical,
  engine, photorealism or native-deliverable gates above.


## Target cam-bank pass (2026-09-05)

- Five original MAZ chapter scans were inspected and packed, alongside a D6/D12
  family shaft photo. Variant differences were resolved in favour of the MAZ
  text: compound gear on intake, and exhaust counterrotation.
- The rebuilt bank assembly contains 248 objects (244 geometry objects and four
  shaft groups). The complete engine has 1,827 registered pieces / 138 moving
  joints; this is a part-count report, not full mechanical acceptance.
- Nominal events follow the target 20/48 degree timing diagram. The 9 mm peak,
  quartic lift law, shaft spacing, tooth form and local dimensions remain fitted.
- Native checks: 121 spur-mesh frames without surface intersections, eight
  spline-interface checks, and 61 actual lobe/tappet frames with gaps from
  -0.000134 to 0.001535 mm. Mesh agreement is not a manufacturing tolerance.
- The 8,470,968-byte engine GLB has zero validation errors or warnings. Native
  whole-vehicle start sequences retain the corrected cam directions and events;
  fourteen integration samples agree with the source to 1.28e-5 rad.
- Browser isolation, bank selection, gear-end framing, slow motion and pause
  were inspected. The incoming bevel train, lash, valve loads and complete engine
  operation remain unaccepted. Every full-vehicle gate above remains OPEN.


### Timing gear train increment — 2026-09-05

25 gear identities, 15 mating pairs and ten new shaft pivots are authored in
Blender and present in the browser module. Each of six bevel and three accessory
spur profile types passed 721 sampled angular positions; the assembled native
gears passed 73 positions per pair with no surface intersections. Exported
shaft axes and pivots match within 1.6e-7 and 2.9e-8 respectively. The final engine
GLB is 9,330,608 bytes with 148 pose bindings and zero glTF errors/warnings.
The integrated textured vehicle checked all 148 D12 poses at 14 start/stop frames:
zero local position error and maximum angular error 2.23e-5 radians.

This is rigid kinematics with reconstructed tooth form and dimensions. It does
not accept legacy casing interference, water-pump/distributor installation,
load transmission, backlash, physical lubrication, pump/generator internals or
full vehicle accuracy. All 16 acceptance gates remain OPEN. The 308-series
supplier pages located during this increment are part-number leads; no new
usable individual part photos have been accepted from them.

### Circulating water pump increment — 2026-09-05

The actual MAZ-1973 figure 28 was downloaded and inspected. Its 17 numbered
component types are represented in the native pump, including six sheet blades,
two ball bearings, the oil seal, corrugated gland, spring and four-tab face seal.
The supplier photograph is only a low-resolution mixed-pump group image; individual
internal-part photo coverage is still missing. Dimensions, ball count, spline
count, blade curvature and casting scroll geometry remain fitted.

The assembly contains 153 authored objects, including display-section halves and
motion groups; this is not an original bill-of-material count. The engine now has
2,046 registered pieces and 169 motion bindings. The 9,996,500-byte engine GLB
passes validation with zero errors and warnings. Native rotor/casing checks cover
37 angular samples with no surface intersections. Export checks preserve all 17
figure labels, coaxial mounting and ideal bearing rolling velocities. The local
water-pump drive is coupled to the lower timing shaft at 1.5 times crank speed.
The textured whole-vehicle start/stop sequence checked all 169 D12 bindings at
14 frames: zero local position error, maximum angular error 4.47e-5 radians.

This does not accept the original front support casting, complete installed
clearances, pump head/flow/torque, actual bearing loads, seal wear, heat exchange,
pressure relief, or the complete coolant network. The original two fans and their
Cardan/gearbox drives are still pending. All 16 full-vehicle gates remain OPEN.

2026-09-06 interface correction: the four lower/upper gearbox flange meshes now
use the four-hole topology visible in the Cardan catalog. Local through-bore,
surrounding-solid and manifold checks passed, along with native pose parity and
the updated browser asset validation. Hole spacing and register dimensions remain
fitted, installed Cardan closure remains incomplete, and browser performance has
not passed acceptance. This increment closes no full-vehicle gate: all 16 remain
OPEN. See the latest entries in COOLING_REFERENCE_NOTES.md and BROWSER_QA.md.

The independent fan-drive Cardan module now includes native forks, two crosses,
eight cups, 176 needles, seals, circlips and male/female splines, with tested
joint orthogonality and ideal rolling kinematics. Its 213 meshes and 190 poses
are inspectable in the browser. This remains preparation for installation,
not completion of the vehicle transmission: actual installed fan shrouds still
intersect the cab inner walls (32 triangle pairs per side at frame zero), and
the shaft axes/length and load path are not accepted. All 16 gates stay OPEN.
