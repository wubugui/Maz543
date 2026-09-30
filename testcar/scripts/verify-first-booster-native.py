"""Check the actual first-gear booster solids, seal travel and open feed path.
This is a geometric test, not a hydraulic leakage or pressure validation.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
D=json.loads((ROOT/'work/transmission/poses.json').read_text());p=D['clutches']['first'];c=D['contact']
P0=p['start']+.005;travel=c['pistonGap']+(p['count']-1)*c['plateGap'];feed=(p['inner']+p['outer'])/2
piston=bpy.data.objects['TX_first_annular_piston'];moving=bpy.data.objects['TX_first_piston_seal_29_moving'];fixed=bpy.data.objects['TX_first_piston_seal_31_fixed']
assert moving.parent.name=='TX_piston_first';assert fixed.parent.name=='TX_first_booster_cover32'
solids=[piston,moving,fixed]+[bpy.data.objects['TX_first_booster_'+s] for s in ['back_wall','outer_bore','inner_guide','inlet_tube','inlet_boss']]
for ob in solids:
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges),ob.name
    assert bm.calc_volume()>0,ob.name
    bm.free()
def xrange(ob):
    x=[(ob.matrix_world@v.co).x for v in ob.data.vertices];return min(x),max(x)
fixed_reference=None;seals=[];paths=[]
for frame in [0,120,240,360,480]:
    bpy.context.scene.frame_set(frame);stroke=travel if frame==120 else 0
    fx=xrange(fixed);mx=xrange(moving)
    if fixed_reference is None:fixed_reference=fx
    assert max(abs(a-b) for a,b in zip(fx,fixed_reference))<1e-8
    assert abs(sum(mx)/2-(P0+.012-stroke))<1e-7
    assert P0+.003<mx[0] and mx[1]<P0+.018
    # The fixed inner seal remains inside the moving skirt over full travel.
    assert P0+.002-stroke<fx[0] and fx[1]<P0+.0135-stroke
    seals.append(dict(frame=frame,strokeMM=stroke*1000,fixedSealXMM=sum(fx)*500,movingSealXMM=sum(mx)*500))
    if frame not in [0,120]:continue
    dg=bpy.context.evaluated_depsgraph_get();trees=[]
    for ob in bpy.data.objects['S543_TRANSMISSION'].children_recursive:
        if ob.type!='MESH':continue
        ev=ob.evaluated_get(dg);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
        trees.append((ob.name,tree));ev.to_mesh_clear()
    for dy,dz in [(0,0),(.001,0),(-.001,0),(0,.001),(0,-.001)]:
        origin=Vector((.270,dy,feed+dz));hits=[]
        for name,tree in trees:
            hit=tree.ray_cast(origin,Vector((-1,0,0)),.09)
            if hit[0] is not None:hits.append((hit[3],name,hit[0].x))
        distance,name,x=min(hits)
        assert name==piston.name,(frame,dy,dz,name,x)
        assert abs(x-(P0+.0135-stroke))<1e-7
        paths.append(dict(frame=frame,offsetMM=[dy*1000,dz*1000],firstHit=name,hitXMM=x*1000))
result=dict(manifoldPressureParts=len(solids),sealStates=seals,feedRayChecks=paths,
            limits='Nominal surfaces and five discrete states. No elastic seal compression, leakage, pressure, fluid network or full booster manufacturing acceptance.')
(ROOT/'outputs/first-booster-native-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
