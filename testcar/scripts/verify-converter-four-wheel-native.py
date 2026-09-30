"""Read saved assembly topology, closed solids and cross-rotor intersections."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_FourWheelAssembly.blend'))
keys=['pump','turbine','front_reactor','rear_reactor','fixed_support'];groups={k:bpy.data.objects['CA_'+k] for k in keys}
parts=[];members={k:[] for k in keys}
def owner(ob):
    p=ob
    while p:
        for k,root in groups.items():
            if p==root:return k
        p=p.parent
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data);closed=all(e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free()
    assert closed and volume>0,(ob.name,closed,volume)
    key=owner(ob);assert key,ob.name;members[key].append(ob)
    parts.append({'name':ob.name,'group':key,'closed':closed,'volumeM3':volume,'vertices':len(ob.data.vertices),'blade':bool(ob.get('blade'))})
def tree(objects):
    points=[];faces=[];names=[]
    for ob in objects:
        ob.data.calc_loop_triangles();start=len(points);points.extend(ob.matrix_world@v.co for v in ob.data.vertices)
        for f in ob.data.loop_triangles:faces.append(tuple(start+i for i in f.vertices));names.append(ob.name)
    return BVHTree.FromPolygons(points,faces,all_triangles=True),names
states=[]
for pump,turbine in [(0.,0.),(.31,-.22)]:
    groups['pump'].rotation_euler.x=pump;groups['turbine'].rotation_euler.x=turbine;bpy.context.view_layer.update()
    trees={k:tree(v) for k,v in members.items()};collisions={}
    for i,k in enumerate(keys):
        for other in keys[i+1:]:
            a,names=trees[k];b,names2=trees[other]
            for ia,ib in a.overlap(b):
                pair=names[ia]+' | '+names2[ib];collisions[pair]=collisions.get(pair,0)+1
    unexpected=[k for k in collisions if not ('_roller_' in k and ' | CA_13_shared_inner_race' in k)]
    assert not unexpected,unexpected
    states.append({'pumpAngle':pump,'turbineAngle':turbine,'intersections':collisions,'unexpectedIntersections':unexpected})
roller_checks=[]
for key in ['front_reactor','rear_reactor']:
    for j in range(12):
        ob=bpy.data.objects[f'CA_{key}_roller_{j:02d}'];a=j*math.pi/6;centre=(.06225*math.cos(a),.06225*math.sin(a))
        vertices=[ob.matrix_world@v.co for v in ob.data.vertices]
        errors=[];minimum=1.
        for p in vertices:
            radius=math.hypot(p.z-centre[0],-p.y-centre[1]);errors.append(min(radius,abs(radius-.00625)))
            minimum=min(minimum,math.hypot(p.z,p.y)-.056)
        bound=max(errors)
        assert minimum>=-bound-1e-9,(ob.name,minimum,bound)
        roller_checks.append({'name':ob.name,'minimumVertexInnerRaceGapM':minimum,'maximumCylinderVertexDeviationM':bound})
report={'meshCount':len(parts),'parts':parts,'states':states,'rollerChecks':roller_checks,'limits':'Surface intersection screen only. Same-rotor cast/spline mates and contained solids require additional fit verification. Roller/inner-race contact is expected and reported, not silently suppressed. Roller check covers vertices and circular surface storage deviation, not continuous rolling dynamics.'}
(ROOT/'outputs/converter-four-wheel-native.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'meshCount':len(parts),'bladeCounts':{k:sum(p['blade'] for p in parts if p['group']==k) for k in keys},'states':states},indent=2),flush=True)
