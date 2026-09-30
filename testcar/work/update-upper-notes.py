from pathlib import Path
p=Path('components/vehicle-viewer.tsx');s=p.read_text(encoding='utf-8').replace('cooling.glb?v=lower-2','cooling.glb?v=upper-1').replace('上齿轮箱、万向轴及完整管路仍待细化。','上下齿轮箱已有独立内构；万向轴、安装闭合及完整管路仍待完成。');p.write_text(s,encoding='utf-8')
p=Path('scripts/verify-model.mjs');s=p.read_text().replace('upper gears, Cardans and complete passages remain incomplete','upper local gears/bearings rebuilt; Cardan interfaces, installed drive and complete passages remain incomplete');p.write_text(s)
p=Path('docs/COOLING_REFERENCE_NOTES.md');s=p.read_text(encoding='utf-8').replace('973 authored mesh/curve objects','1237 authored mesh/curve objects').replace('178 semantic pose bindings','254 semantic pose bindings').replace('vehicle masters: 354 joints','vehicle masters: 430 joints').replace('was below 0.00006 radians','was below 0.00007 radians');s += '''
## Upper native geometry increment

Both upper gearboxes now have separate conical input/output gears, eight total
ball-bearing assemblies, stepped shafts, input seals/shims, hollow cast cases,
removable bearing cups, drilled fitted flanges, pedestals and spring-loaded end
brushes. The front support bolts are outside their flange; the inlet touches the
case and the brush meets the shaft end without penetrating it. The **20:32
upper gear pair is fitted**. The fan/armature rotation sign follows the authored
upper output axis, toward the fan (-X); factory rotation and complete Cardan
velocity transmission have not been accepted. Thermal and clutch calculations
continue to use positive speed magnitudes and the fitted net ratio of 1.

Upper casting normals and roughness are baked into separate 2048 px maps.
This alloy finish has no accepted individual upper-gearbox photo and remains a
material approximation. `prepare-cooling-upper.py` prepares the tooth caps;
`update-cooling-upper.py` rebuilds only these parts while preserving the lower
bakes. `verify-cooling-upper.py` checks both local gear pairs/cases over 49
samples, all eight nominal bearing envelopes, and the end-brush contact. It
renders external/internal inspection PNGs. None of these checks validates the
installed interface conflict or turns the whole drivetrain into an accepted
physical simulation.
''';p.write_text(s,encoding='utf-8')
p=Path('README.md');s=p.read_text(encoding='utf-8').replace('973 个网格/曲线对象和 178 个姿态绑定','1,237 个网格/曲线对象和 254 个姿态绑定');s += '\n上齿轮箱：先运行 `prepare-cooling-upper.py` 和 `prepare-starting.mjs`，再用 Blender 执行 `update-cooling-upper.py`、`verify-cooling-upper.py`、`install-cooling-assets.py` 和 `verify-cooling-install.py`。浏览器“冷却系统 → 检查左上齿轮箱”提供独立检查。上下齿轮箱的局部齿轮已重建，但万向轴法兰孔位、安装位置和完整传动闭合尚未通过核验。\n';p.write_text(s,encoding='utf-8')
