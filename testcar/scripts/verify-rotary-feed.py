"""Check reconstructed support50/body46 geometry and the complete fluid route.
Tests actual native meshes; fixed and rotating segments meet through an annular
band. This is geometric continuity, not a hydraulic or leakage simulation.
"""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if '--geometry-only' in sys.argv else 'outputs/MAZ543A_Transmission.blend')))
root=bpy.data.objects['S543_TRANSMISSION'];report={'solids':[],'routes':[],'sealStates':[],'stepJointChecks':[],'failures':[]}
D=json.loads((ROOT/'work/transmission/poses.json').read_text())['directBooster'];face=D['pressureFace'];wall_x=D['backWallCentre']
names=['TX_direct_'+n for n in ['body46_sleeve','annular_piston','booster_back_wall','booster_inner_guide',
       'piston_seal_outer_moving','piston_seal_inner_fixed','support50_journal','support50_inlet',
       'feed_seal_0','feed_seal_1','feed_bearing_inner','feed_bearing_outer']]
names+=['TX_case47_front_web','TX_end_cover_-0.25']
names += [f'TX_feed_ball_{j}_surface' for j in range(14)]
names += [f'TX_feed_cage_rail_{s}' for s in [-1,1]]+[f'TX_feed_cage_bridge_{j}' for j in range(14)]
for name in names:
    ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data)
    bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume()
    report['solids'].append(dict(name=name,badEdges=bad,volumeM3=volume))
    if bad or volume<=0:report['failures'].append(dict(kind='solid',name=name,badEdges=bad,volume=volume))
    bm.free()
assert bpy.data.objects['TX_rotating_body46'].parent.name=='TX_ring18'
assert bpy.data.objects['TX_fixed_support50'].parent.name=='TX_intermediate_case47'
assert bpy.data.objects['TX_feed_bearing_cage'].parent==root

def coord(x,r,a):return Vector((x,-r*math.sin(a),r*math.cos(a)))
for j,centre in enumerate([-.233,-.226]):
    ob=bpy.data.objects[f'TX_direct_feed_seal_{j}'];me=ob.data;me.calc_loop_triangles()
    tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)
    for dx,angle,open_gap in [(-.0004,math.pi-.01,True),(-.0004,math.pi+.01,False),
                              (0,math.pi,True),(.0004,math.pi+.01,True),(.0004,math.pi-.01,False)]:
        origin=coord(centre+dx,.099,angle);direction=coord(0,1,angle)
        hit=tree.ray_cast(origin,direction,.004)[0]
        assert (hit is None)==open_gap,(j,dx,angle,'stepped ring joint topology')
        report['stepJointChecks'].append(dict(ring=j,axialOffsetMM=dx*1000,angle=angle,open=open_gap))
def segment(trees,a,b,label):
    d=b-a;length=d.length;d.normalize();hits=[]
    for name,tree in trees:
        h=tree.ray_cast(a,d,length)
        if h[0] is not None and h[3]<length-1e-7:hits.append(dict(name=name,distance=h[3],point=list(h[0])))
    if hits:report['failures'].append(dict(kind='blocked',segment=label,hits=hits))
    return len(hits)

# Continuous revolution of the rotary interface, in addition to both endpoint
# piston states. Other components keep their native neutral reference pose.
for step in range(24):
    bpy.context.scene.frame_set(0)
    bodyAngle=step*math.tau/24;body=bpy.data.objects['TX_ring18'];body.rotation_euler.x=bodyAngle
    stroke=.0045 if step%2 else 0;bpy.data.objects['TX_piston_direct'].location.x=stroke
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();trees=[]
    for ob in root.children_recursive:
        if ob.type!='MESH':continue
        ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
        trees.append((ob.name,BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)));ev.to_mesh_clear()
    fixed=D['feedAngle'];rot=bodyAngle
    points=[coord(-.270,.096,fixed),coord(-.2295,.096,fixed),coord(-.2295,.1013,fixed)]
    delta=(rot-fixed+math.pi)%math.tau-math.pi;n=max(1,math.ceil(abs(delta)/(.05)))
    points += [coord(-.2295,.1013,fixed+delta*j/n) for j in range(1,n+1)]
    points += [coord(-.2295,.1035,rot),coord(wall_x,.1035,rot),coord(wall_x,.099,rot),coord(face+stroke-.0001,.099,rot)]
    blocked=sum(segment(trees,a,b,f'{step}:{i}') for i,(a,b) in enumerate(zip(points,points[1:])))
    # Last leg must end on the real moving pressure face, not a casing plug.
    origin=points[-1];hits=[]
    for name,tree in trees:
        h=tree.ray_cast(origin,Vector((1,0,0)),.02)
        if h[0] is not None:hits.append((h[3],name,h[0].x))
    hit=min(hits)
    if hit[1]!='TX_direct_annular_piston' or abs(hit[2]-(face+stroke))>1e-7:
        report['failures'].append(dict(kind='pressureFace',step=step,hit=hit))
    report['routes'].append(dict(angleDegrees=step*15,travelMM=stroke*1000,segments=len(points)-1,blocked=blocked,pressureFace=hit[1]))
for frame in [0,120,240,360,480]:
    bpy.context.scene.frame_set(frame);stroke=.0045 if frame==360 else 0
    if '--geometry-only' in sys.argv:
        bpy.data.objects['TX_piston_direct'].location.x=stroke;bpy.context.view_layer.update()
    moving=bpy.data.objects['TX_direct_piston_seal_outer_moving'];fixed=bpy.data.objects['TX_direct_piston_seal_inner_fixed']
    assert moving.parent.name=='TX_piston_direct' and fixed.parent.name=='TX_rotating_body46'
    bounds=lambda ob: sorted((ob.matrix_world@v.co).x for v in ob.data.vertices)
    a,b=bounds(moving),bounds(fixed)
    assert abs((a[0]+a[-1])/2-(D['outerSealX']+stroke))<1e-7
    assert abs((b[0]+b[-1])/2-D['innerSealX'])<1e-7
    assert wall_x+.001<a[0]<a[-1]<-.1785
    assert face+stroke<b[0]<b[-1]<D['innerSkirtFront']+stroke
    report['sealStates'].append(dict(frame=frame,travelMM=stroke*1000))
report['limits']='Reconstructed dimensions/routes. 24 angular samples and 5 seal states; no flow, pressure, leakage, elastic ring squeeze, bearing loads or factory dimensional acceptance.'
report_path=ROOT/('work/transmission/rotary-geometry-checks.json' if '--geometry-only' in sys.argv else 'outputs/rotary-feed-checks.json')
report_path.write_text(json.dumps(report,indent=2))
print(json.dumps({'solids':len(report['solids']),'routes':len(report['routes']),'failures':report['failures'][:20]},indent=2),flush=True)
assert not report['failures'],'See outputs/rotary-feed-checks.json'
