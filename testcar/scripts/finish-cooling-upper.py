"""Align the end brush contact after initial native assembly, then export."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
for i in range(2):
    o=bpy.data.objects[f'COOL_upper_end_brush_{i}'];offset=.103-min(v.co.x for v in o.data.vertices)
    for v in o.data.vertices:v.co.x+=offset
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'),compress=True)
exec(compile((ROOT/'scripts/export-cooling-native.py').read_text(),str(ROOT/'scripts/export-cooling-native.py'),'exec'))
