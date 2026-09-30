"""Check evaluated native flange topology and actual open/solid axial ray paths."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
bpy.context.scene.frame_set(0)
reports=[]
for kind in ['lower','upper']:
    for i in range(2):
        name=f'COOL_lower_cardan_flange_{i}' if kind=='lower' else f'COOL_upper_input_flange_{i}'
        o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        bm=bmesh.new();bm.from_mesh(mesh)
        nonmanifold=sum(not e.is_manifold for e in bm.edges)
        tree=BVHTree.FromBMesh(bm)
        x0=min(v.co.x for v in bm.verts);x1=max(v.co.x for v in bm.verts)
        def hit(y,z):return tree.ray_cast(Vector((x0-.01,-z,y)),Vector((1,0,0)),x1-x0+.02)[0] is not None
        clear=0;solid=0
        # Nine rays per hole distinguish a through bore from a blind recess.
        for j in range(4):
            a=math.pi/4+j*math.pi/2;cy=.037*math.cos(a);cz=.037*math.sin(a)
            for k in range(9):
                r=0 if k==8 else .0035;b=k*math.pi/4
                assert not hit(cy+r*math.cos(b),cz+r*math.sin(b)),(name,j,k,'blocked bolt passage')
                clear+=1
            for k in range(8):
                b=k*math.pi/4
                assert hit(cy+.0055*math.cos(b),cz+.0055*math.sin(b)),(name,j,k,'missing material around bolt hole')
                solid+=1
        assert not hit(0,0),(name,'blocked shaft passage')
        for j in range(16):
            a=j*math.pi/8
            assert hit(.023*math.cos(a),.023*math.sin(a)),(name,'broken central annulus')
        assert nonmanifold==0,(name,nonmanifold)
        reports.append({'name':name,'throughHoleRays':clear,'surroundingSolidRays':solid,'centralBoreOpen':True,'nonManifoldEdges':nonmanifold,'thicknessMM':round((x1-x0)*1000,5)})
        bm.free();ev.to_mesh_clear()
report={'flanges':reports,'limits':'Four-hole topology from catalog; hole centres, OD, axial dimensions and year compatibility remain reconstructed. No installed Cardan clearance acceptance.'}
(ROOT/'outputs/cooling-interface-verification.json').write_text(json.dumps(report,indent=2))
print('INTERFACE_NATIVE',json.dumps(report),flush=True)
