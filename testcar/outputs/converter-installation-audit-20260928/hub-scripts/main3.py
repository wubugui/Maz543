"""Read-only: describe legacy 'drive' children near the converter site."""
import bpy, json, math, os
from pathlib import Path
from mathutils import Vector
OUT = Path(os.environ['HUB_OUTPUT_DIR']); OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path.cwd() / 'MAZ543A_Master.blend'))
tx = bpy.data.objects['S543_TRANSMISSION']; inv = tx.matrix_world.inverted(); drive = bpy.data.objects['drive']
rows = []
for ob in [o for o in drive.children] + [bpy.data.objects.get('BL_Final_drive_1_cast_housing')]:
    if ob is None: continue
    obs = [ob] + list(ob.children_recursive); ms = [o for o in obs if o.type == 'MESH']
    pts = [inv @ (o.matrix_world @ v.co) for o in ms for v in o.data.vertices]
    row = {'name': ob.name, 'type': ob.type, 'meshes': len(ms), 'vertices': len(pts), 'props': {k: str(ob[k])[:160] for k in ob.keys() if not k.startswith('_')},
           'materials': sorted({s.material.name for o in ms for s in o.material_slots if s.material})[:6]}
    if pts:
        row['txFrameMin'] = [min(p[i] for p in pts) for i in range(3)]; row['txFrameMax'] = [max(p[i] for p in pts) for i in range(3)]
        row['rMaxAboutGearboxAxis'] = max(math.hypot(p.y, p.z) for p in pts)
    rows.append(row)
(OUT / 'drive-holder-inventory.json').write_text(json.dumps(rows, indent=2))
print('[inv]', len(rows), flush=True)
