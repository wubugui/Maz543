"""Reopen the saved moving freewheel bench and measure evaluated geometry."""
import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'work/freewheel-contact/native-bench.json').read_text());F=D['fit']
path=ROOT/'outputs/MAZ543A_Converter_Freewheel_ContactBench.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
root=bpy.data.objects['S543_CONVERTER_FREEWHEELS'];assert root['diagnosticSha256']==D['diagnosticSha256']
def C(p):return Vector((p[0],-p[2],p[1]))
def evaluated(ob):
    deps=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles()
    local=[v.co.copy() for v in m.vertices];triangles=[tuple(t.vertices) for t in m.loop_triangles]
    world=[ob.matrix_world@p for p in local];tree=BVHTree.FromPolygons(world,triangles,all_triangles=True)
    e.to_mesh_clear();return local,world,triangles,tree
springs=[o for o in bpy.data.objects if '_engagement_spring_' in o.name]
assert len(springs)==24 and len({o.data.as_pointer() for o in springs})==1
assert len(springs[0].data.shape_keys.key_blocks)==len(D['samples'])
poseChecks=0;springStates=0;collisionPairs=0;nominalWireContacts=0;maxWireDepth=0;maxLengthError=0;maxWireError=0;maxHelixLengthError=0;maxForceError=0;maxAngleError=0;maxPositionError=0
segments=160;sides=12;rho=F['innerRadius']+F['rollerRadius'];refLength=-F['springBaseZ']-F['rollerRadius']-F['springWireRadius'];expectedWireLength=math.hypot(refLength,math.tau*F['springTurns']*F['springRadius'])
summaryRows=[]
for sample in D['samples']:
    bpy.context.scene.frame_set(sample['frame']);bpy.context.view_layer.update()
    y,z,spin,angle=sample['q'];co=math.cos(angle);si=math.sin(angle);ly=co*y+si*z;lz=-si*y+co*z
    for row,x in zip(['front','rear'],F['rowX']):
        outer=bpy.data.objects['CV_'+row+'_outer'];expected=Quaternion((1,0,0),angle)
        err=outer.rotation_quaternion.rotation_difference(expected).angle;err=min(err,abs(math.tau-err));maxAngleError=max(maxAngleError,err);assert err<2e-6
        for j in range(F['rollerCount']):
            ob=bpy.data.objects[f'CV_{row}_roller_{j}'];expectedPos=C((x,ly,lz));err=(ob.location-expectedPos).length;maxPositionError=max(maxPositionError,err);assert err<2e-8
            expected=Quaternion((1,0,0),spin-angle);err=ob.rotation_quaternion.rotation_difference(expected).angle;err=min(err,abs(math.tau-err));maxAngleError=max(maxAngleError,err);assert err<2e-6
            poseChecks+=1
    local,_,triangles,_=evaluated(springs[0]);assert len(local)==(segments+1)*sides
    centres=[sum(local[i*sides:(i+1)*sides],Vector())/sides for i in range(segments+1)]
    length=(centres[-1]-centres[0]).length;err=abs(length-sample['springLength']);maxLengthError=max(maxLengthError,err);assert err<2e-8
    base=C((0,rho,F['springBaseZ']));axis=(centres[-1]-centres[0]).normalized()
    radii=[]
    for i,centre in enumerate(centres):
        displacement=centre-base;radial=displacement-axis*displacement.dot(axis);radii.append(radial.length)
        for p in local[i*sides:(i+1)*sides]:
            err=abs((p-centre).length-F['springWireRadius']);maxWireError=max(maxWireError,err);assert err<2e-8
    radius=sum(radii)/len(radii);wireLength=math.hypot(length,math.tau*F['springTurns']*radius)
    err=abs(wireLength-expectedWireLength);maxHelixLengthError=max(maxHelixLengthError,err);assert err<1e-7
    # Reference rate and saved measured length independently recover the coil
    # elastic force; the record includes damping, so account for length rate.
    stateDistance=math.hypot(ly-rho,lz-F['springBaseZ']);sine=length/expectedWireLength;cosine=math.sqrt(1-sine*sine);radial=math.sqrt(F['rollerRadius']**2-(F['springWireRadius']*sine)**2)
    derivative=1/(1-F['springWireRadius']**2*length/(expectedWireLength**2*radial)-F['springWireRadius']*length/(expectedWireLength**2*cosine))
    by=rho*co-F['springBaseZ']*si;bz=rho*si+F['springBaseZ']*co
    speed=((y-by)*(sample['v'][0]+sample['v'][3]*bz)+(z-bz)*(sample['v'][1]-sample['v'][3]*by))/stateDistance
    k=F['shearModulus']*(2*F['springWireRadius'])**4/(8*(2*F['springRadius'])**3*F['springTurns'])
    force=max(0,k*max(0,F['springFreeLength']-length)-F['springDamping']*speed*derivative)
    err=abs(force-root['spring_axial_force_N']);maxForceError=max(maxForceError,err);assert err<.0001
    assert abs(root['spring_contact_force_N']-sample['springForce'])<1e-6
    bm=bmesh.new();bm.from_mesh(springs[0].evaluated_get(bpy.context.evaluated_depsgraph_get()).data);assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0;bm.free()
    springStates+=24
    for row in ['front','rear']:
        ob=bpy.data.objects[f'CV_{row}_engagement_spring_0'];_,world,tris,coil=evaluated(ob)
        for name in ['CV_shared_fixed_inner_race','CV_'+row+'_wedged_outer_race','CV_'+row+'_roller_0']:
            target=bpy.data.objects[name];_,_,_,other=evaluated(target);collisionPairs+=1
            if not coil.overlap(other):continue
            assert '_roller_' in name,(row,sample['frame'],name,'spring crosses a race or cell wall')
            centre=target.matrix_world.translation;minimum=float('inf')
            for tri in tris:
                for ia,ib in zip(tri,tri[1:]+tri[:1]):
                    a=world[ia]-centre;b=world[ib]-centre;dy,dz=b.y-a.y,b.z-a.z;u=max(0,min(1,-(a.y*dy+a.z*dz)/max(1e-30,dy*dy+dz*dz)))
                    minimum=min(minimum,math.hypot(a.y+u*dy,a.z+u*dz))
            depth=max(0,F['rollerRadius']-minimum);assert depth<5e-8,(row,sample['frame'],'wire penetrates roller',depth)
            nominalWireContacts+=1;maxWireDepth=max(maxWireDepth,depth)
    summaryRows.append({'frame':sample['frame'],'lengthM':length,'wireRadiusM':sum((p-centres[i//sides]).length for i,p in enumerate(local))/len(local),'coilRadiusM':radius,'axialForceN':force})
report={'poseChecks':poseChecks,'springInstanceStates':springStates,'sampleFrames':len(D['samples']),
 'collisionPairs':collisionPairs,'nominalWireContacts':nominalWireContacts,'maximumNominalWireDepthM':maxWireDepth,
 'maxPositionErrorM':maxPositionError,'maxAngleErrorRad':maxAngleError,'maxCoilLengthErrorM':maxLengthError,
 'maxWireRadiusErrorM':maxWireError,'maxIdealHelixLengthErrorM':maxHelixLengthError,'maxAxialForceErrorN':maxForceError,
 'blendBytes':path.stat().st_size,'blendSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':summaryRows,
 'limits':'Saved 100-Hz sample frames, periodic symmetric instances and fitted linear spring force. Between-frame mesh/quaternion interpolation is approximate. Material strength, fluid torque, full pocket envelope and vehicle installation remain unaccepted.'}
(ROOT/'outputs/freewheel-native-bench-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)
