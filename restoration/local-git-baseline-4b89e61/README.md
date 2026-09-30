# MAZ-543A · Blender 机械解构

本项目提供 Blender 建模资产和可在浏览器操作的三维工作台。外观统一参考量产 MAZ-543A 双驾驶室照片；轮胎采用有产品规格资料的 VI-203 形态，不代表某辆早期车辆的原装轮胎。

## 可使用的文件

- `outputs/MAZ543A_Master.blend`：原始 Blender 外观网格、倒角、细分与厚度修改器、参考图对象、Cycles 灯光。
- `outputs/MAZ543A_Textured.blend`：烘焙 PBR 材质、可编辑网格、命名总成与已烘焙的机构动画。
- `public/models/maz543a-blender.glb`：浏览器实际加载的 Blender 导出资产。
- `outputs/maz543a-textured-preview.png`：Blender Cycles 渲染。
- `docs/REFERENCE_NOTES.md`：图片出处、型号差异、参考尺寸及准确性限制。

## 浏览器操作

拖动旋转、滚轮缩放、点击选择部件。右侧可以启动发动机、调整油门/挡位/制动、操纵前两轴转向、展示悬架台架运动、打开车门和分离总成。提供透视、纵剖、标签、单独查看与当前姿态 GLB 导出。浏览器的 GLB 导出包含当前模型和贴图，不携带网页控制程序。

## Blender 动画

打开 `MAZ543A_Textured.blend`，按空格播放时间线：

- 1–120 帧：发动机慢动作。
- 121–240 帧：车轮、转向与悬架演示。
- 241–301 帧：驾驶室车门检查。

动画由同一套运动计算烘焙而来。需要观察内构时，可在 Blender 中隐藏车壳总成或使用透视显示。

## 精度范围

此模型没有经过原厂尺寸、公差或实车扫描认证，不是包含所有零件的工程数字样机。外形参考照片重建；部分紧固件、管路、齿形、配气相位、安装尺寸和内部机构仍然简化。发动机内构采用可计算的曲柄连杆关系，转向按共同瞬时中心求角，制动/车速为简化响应，悬架用位移输入演示。没有轮胎接地、流体、热力、电气、材料应力或经过标定的多体动力学求解。

## 本地运行与验证

需要 Node.js 22.13+。运行 `npm install` 后执行 `npm run dev`。生产构建使用 `npm run build`。

`node scripts/verify-model.mjs` 检查轴距、活塞行程、连杆定长、转向中心、内外轮转速、制动保持、有限变换、导出的关节名称与 glTF 文件。该检查不等价于浏览器视觉检查。

## 资产重建

1. `node scripts/prepare-blender.mjs` 导出简化机械机构底稿。
2. Blender 4.5 LTS 后台运行 `scripts/blender-model.py` 创建原生外观网格和母版。
3. 运行 `scripts/blender-export.py` 展 UV、烘焙基础色/粗糙度/法线/AO/金属度，并导出压缩 GLB。
4. `node scripts/bake-animation.mjs` 生成机构动画采样。
5. Blender 运行 `scripts/blender-animate.py` 校正门轴、保存动画工程并导出中立姿态模型。

参考图在建模脚本中默认读取 `D:/maz543-references`；移动项目时请更新该路径。参考照片不嵌入网页模型贴图。Blender 二进制与工作缓存位于被忽略的 `work` 目录。
