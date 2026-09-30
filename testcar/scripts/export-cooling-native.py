"""Export the saved cooling master without rebuilding or re-baking surfaces."""
import bpy,bmesh,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
root=bpy.data.objects['S543_COOLING']
for o in engine_descendants(root):
    if o.type=='MESH' and (o.get('lowerDrive') or o.get('upperGearbox')):
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(o.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'),compress=True)
report=json.loads((ROOT/'outputs/cooling-parts-register.json').read_text())
source=(ROOT/'scripts/blender-cooling.py').read_text();exec(compile(source[source.index('# Batch only'):],str(ROOT/'scripts/blender-cooling.py'),'exec'))
