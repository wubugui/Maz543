"""Replay continuous solver poses against saved race and roller meshes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_Freewheels.blend'))
data=json.loads((ROOT/'outputs/converter-freewheel-contact-diagnostic.json').read_text());fit=data['fit']
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(ob):
    m=ob.data;m.calc_loop_triangles()
    return BVHTree.FromPolygons([ob.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
for ob in bpy.data.objects:ob.animation_data_clear()
checks=[];maximumGapError=0;nominalInnerContacts=0;maximumInnerRoundoff=0;nominalWedgeContacts=0;maximumWedgeRoundoff=0
for sample in data['rows']:
    y,z,spin,angle=sample['q'];co=math.cos(angle);si=math.sin(angle)
    localY=co*y+si*z;localZ=-si*y+co*z
    for row,x in zip(['front','rear'],fit['rowX']):
        outer=bpy.data.objects['CV_'+row+'_outer'];outer.rotation_euler.x=(angle+math.pi)%math.tau-math.pi
        roller=bpy.data.objects[f'CV_{row}_roller_0'];roller.location=C((x,localY,localZ));roller.rotation_euler.x=(spin-angle+math.pi)%math.tau-math.pi
        bpy.context.view_layer.update();roll=tree(roller);race=tree(bpy.data.objects['CV_'+row+'_wedged_outer_race'])
        inner=tree(bpy.data.objects['CV_shared_fixed_inner_race']);centre=roller.matrix_world.translation
        assert (centre-C((x,y,z))).length<2e-8,(row,sample['time'],(centre-C((x,y,z))).length)
        if roll.overlap(race):
            local=[outer.matrix_world.inverted()@roller.matrix_world@v.co for v in roller.data.vertices]
            angles=[math.atan2(-p.y,p.z)*180/math.pi for p in local]
            assert min(angles)>-13 and max(angles)<8,(row,sample['time'],'roller reaches a pocket side wall')
            d=fit['rollerRadius']+(fit['innerRadius']+fit['rollerRadius'])*math.cos(fit['wedgeAngle'])
            depth=max(0,max(math.cos(fit['wedgeAngle'])*p.z-math.sin(fit['wedgeAngle'])*p.y-d for p in local))
            assert depth<5e-8,(row,sample['time'],'actual wedge penetration exceeds float-transform bound',depth)
            nominalWedgeContacts+=1;maximumWedgeRoundoff=max(maximumWedgeRoundoff,depth)
        # Analytic circular radius is outside the inscribed mesh; a tiny mesh
        # tolerance accounts for float transforms at the physical tangent.
        if roll.overlap(inner):
            # BVH reports the intended tangent as an overlap under float32
            # world transforms. Bound actual inward depth from every mesh edge
            # against the circumscribed inner cylinder; no blanket exemption.
            verts=[roller.matrix_world@v.co for v in roller.data.vertices];minimum=float('inf')
            for edge in roller.data.edges:
                a,b=[verts[i] for i in edge.vertices];dy,dz=b.y-a.y,b.z-a.z
                u=max(0,min(1,-(a.y*dy+a.z*dz)/max(1e-30,dy*dy+dz*dz)))
                minimum=min(minimum,math.hypot(a.y+u*dy,a.z+u*dz))
            depth=max(0,fit['innerRadius']-minimum)
            assert depth<5e-8,(row,sample['time'],'inner penetration exceeds float-transform contact bound',depth)
            nominalInnerContacts+=1;maximumInnerRoundoff=max(maximumInnerRoundoff,depth)
        direction=C((0,math.cos(angle+fit['wedgeAngle']),math.sin(angle+fit['wedgeAngle'])))
        _,_,_,distance=race.ray_cast(centre,direction,.030)
        _,_,_,rollerDistance=roll.ray_cast(centre,direction,.030)
        assert distance is not None and rollerDistance is not None
        gap=distance-rollerDistance;error=abs(gap-sample['gaps'][1]);maximumGapError=max(maximumGapError,error)
        assert error<3e-6,(row,sample['time'],gap,sample['gaps'][1])
        checks.append({'t':sample['time'],'row':row,'actualWedgeGapM':gap,'solverWedgeGapM':sample['gaps'][1]})
report={'poseChecks':len(checks),'maxWedgeGapErrorM':maximumGapError,'nominalInnerContacts':nominalInnerContacts,
 'maximumNominalInnerDepthM':maximumInnerRoundoff,'checks':checks,
 'nominalWedgeContacts':nominalWedgeContacts,'maximumNominalWedgeDepthM':maximumWedgeRoundoff,
 'limits':'Two row representatives; other rollers are periodic copies. Actual saved cylinder/ramp/inner-race meshes replayed at 100 Hz. Springs are NOT continuously rebuilt by this reader. No full native animation, spring force/geometry parity, blade flow or full 3D assembly acceptance.'}
(ROOT/'outputs/converter-freewheel-contact-native.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
