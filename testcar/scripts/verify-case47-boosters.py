"""Native geometry proof for the two fixed boosters supported by case 47."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
D=json.loads((ROOT/'work/transmission/poses.json').read_text());report={'solids':0,'seals':[],'inletRays':[]}
case=bpy.data.objects['TX_intermediate_case47'];assert case.parent.name=='S543_TRANSMISSION'
objects=[bpy.data.objects['TX_case47_'+n] for n in ['front_web','outer_bridge','reverse_web']]
for name in ['second','reverse']:
    booster=bpy.data.objects[f'TX_{name}_booster_case47'];assert booster.parent==case
    objects += [bpy.data.objects[f'TX_{name}_'+n] for n in ['annular_piston','piston_seal_outer_moving','piston_seal_inner_fixed','booster_back_wall','booster_inner_guide','booster_outer_bore']]
    objects.append(bpy.data.objects[f'TX_case47_{name}_oil_gallery'])
for ob in objects:
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges),ob.name
    assert bm.calc_volume()>0,ob.name
    bm.free();report['solids']+=1
def bounds(o):
    x=[(o.matrix_world@v.co).x for v in o.data.vertices];return min(x),max(x)
for frame in [0,120,240,360,480]:
    bpy.context.scene.frame_set(frame)
    for name,selected in [('second',240),('reverse',480)]:
        p=D['clutches'][name];P0=p['start']-.005;t=D['contact']['pistonGap']+(p['count']-1)*D['contact']['plateGap'];stroke=t if frame==selected else 0
        moving=bpy.data.objects[f'TX_{name}_piston_seal_outer_moving'];fixed=bpy.data.objects[f'TX_{name}_piston_seal_inner_fixed']
        assert moving.parent.name==f'TX_piston_{name}' and fixed.parent.name==f'TX_{name}_booster_case47'
        a,b=bounds(moving);c,d=bounds(fixed)
        assert abs((a+b)/2-(P0-.012+stroke))<1e-7
        assert abs((c+d)/2-(P0-.0045))<1e-7
        assert P0-.018<a<b<P0-.003
        assert P0-.0135+stroke<c<d<P0-.002+stroke
        report['seals'].append(dict(pack=name,frame=frame,travelMM=stroke*1000))
    if frame not in [0,240,480]:continue
    dg=bpy.context.evaluated_depsgraph_get();trees=[]
    for ob in bpy.data.objects['S543_TRANSMISSION'].children_recursive:
        if ob.type!='MESH':continue
        ev=ob.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles()
        trees.append((ob.name,BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)));ev.to_mesh_clear()
    for name,selected in [('second',240),('reverse',480)]:
        if frame not in [0,selected]:continue
        p=D['clutches'][name];P0=p['start']-.005;stroke=D['contact']['pistonGap']+(p['count']-1)*D['contact']['plateGap'] if frame==selected else 0
        for dy,dz in [(0,0),(.001,0),(-.001,0),(0,.001),(0,-.001)]:
            r=(p['inner']+p['outer'])/2;angle=math.pi/8 if name=='reverse' else 0
            origin=Vector((-.270,-r*math.sin(angle)+dy,r*math.cos(angle)+dz));hits=[]
            for obname,tree in trees:
                hit=tree.ray_cast(origin,Vector((1,0,0)),.2)
                if hit[0] is not None:hits.append((hit[3],obname,hit[0].x))
            distance,obname,x=min(hits)
            assert obname==f'TX_{name}_annular_piston',(frame,name,obname,x)
            assert abs(x-(P0-.0135+stroke))<1e-7
            report['inletRays'].append(dict(pack=name,frame=frame,offsetMM=[dy*1000,dz*1000],hit=obname))
report['limits']='Fitted gallery routes and five discrete states. No pressure, elastic sealing, leakage, continuous collision or casting accuracy acceptance.'
(ROOT/'outputs/case47-booster-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps({'solids':report['solids'],'sealStates':len(report['seals']),'inletRayChecks':len(report['inletRays']),'errors':0},indent=2))
