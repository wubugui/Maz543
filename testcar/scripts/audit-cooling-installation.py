"""Read-only actual mesh clearance audit of the current installed cooling pack."""
import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
study='--study' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/('MAZ543A_CabFit_Study.blend' if study else 'MAZ543A_Master.blend')))
bpy.context.scene.frame_set(0)
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
result=[]
for side in [-1,1]:
    wall=bpy.data.objects[f'BL_Cab_{side}_inner_wall'];t=tree(wall)
    for i in range(2):
        name=f'COOL_shroud_{i}';hits=t.overlap(tree(bpy.data.objects[name]))
        if hits:result.append({'cabSide':side,'coolingPart':name,'intersectingTrianglePairs':len(hits)})
report={'status':'OPEN' if result else 'Not accepted; only one pose sampled','cabShroudIntersections':result,
  'limits':'Actual installed mesh surfaces at frame zero only. No replacement fan position, diameter or cabin wall dimension is inferred by this check.'}
(ROOT/'outputs'/('cooling-cab-study-clearances.json' if study else 'cooling-installation-clearances.json')).write_text(json.dumps(report,indent=2));print('COOLING_PACK_CLEARANCE',json.dumps(report),flush=True)
