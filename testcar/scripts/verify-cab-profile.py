"""Check the corrected native facade, aperture and local shroud clearance."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_CabFit_Study.blend'))
bpy.context.scene.frame_set(0);results=[]
for s in [-1,1]:
    o=bpy.data.objects[f'BL_Cab_{s}_front_shell']
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh)
    bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True)
    assert bad==0 and volume>0,(o.name,bad,volume)
    mesh.calc_loop_triangles();tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[tuple(f.vertices) for f in mesh.loop_triangles],all_triangles=True)
    rays=[]
    for h,lateral,expect in [(2.3,.95,False),(2.4,1.12,False),(1.5,1.05,True),(1.5,.65,False)]:
        hit=tree.ray_cast(Vector((-10,-s*lateral,h)),Vector((1,0,0)),10)[0] is not None
        assert hit==expect,(s,h,lateral,hit,expect)
        rays.append({'height':h,'lateral':lateral,'hitFacade':hit})
    results.append({'side':s,'nonManifoldEdges':bad,'positiveVolumeM3':volume,'rays':rays})
    bm.free();ev.to_mesh_clear()
(ROOT/'outputs/cab-profile-verification.json').write_text(json.dumps({'status':'local geometry checks passed; dimensions still fitted','facades':results},indent=2))
print('CAB_PROFILE_VERIFIED',json.dumps(results),flush=True)
