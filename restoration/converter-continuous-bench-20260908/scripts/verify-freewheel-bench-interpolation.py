"""Bound geometric errors between saved contact samples, without resimulation."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'work/freewheel-contact/native-bench.json').read_text());F=D['fit']
path=ROOT/'outputs/MAZ543A_Converter_Freewheel_ContactBench.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
ob=bpy.data.objects['CV_front_engagement_spring_0'];roller=bpy.data.objects['CV_front_roller_0'];outer=bpy.data.objects['CV_front_outer']
wire=F['springWireRadius'];rho=F['innerRadius']+F['rollerRadius'];Lref=-F['springBaseZ']-F['rollerRadius']-wire
S=math.hypot(Lref,math.tau*F['springTurns']*F['springRadius'])
report={'fractionalFrames':0,'maxWireRadiusErrorM':0.,'maxHelixLengthErrorM':0.,'maximumRollerPenetrationM':0.,'maximumSpringSkinGapM':0.,'minimumSpringSkinGapM':1.,'maxOuterInterpolationAngleErrorRad':0.}
for a,b in zip(D['samples'],D['samples'][1:]):
    for t in [.25,.5,.75]:
        bpy.context.scene.frame_set(a['frame'],subframe=t);bpy.context.view_layer.update()
        e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();points=[v.co.copy() for v in mesh.vertices];e.to_mesh_clear()
        centres=[sum(points[i*12:(i+1)*12],Vector())/12 for i in range(161)]
        length=(centres[-1]-centres[0]).length;axis=(centres[-1]-centres[0]).normalized();base=Vector((0,-F['springBaseZ'],rho))
        radii=[]
        for i,c in enumerate(centres):
            d=c-base;radii.append((d-axis*d.dot(axis)).length)
            for p in points[i*12:(i+1)*12]:report['maxWireRadiusErrorM']=max(report['maxWireRadiusErrorM'],abs((p-c).length-wire))
        report['maxHelixLengthErrorM']=max(report['maxHelixLengthErrorM'],abs(math.hypot(length,math.tau*F['springTurns']*sum(radii)/161)-S))
        # Actual evaluated wire vertices against the analytic roller cylinder.
        cy,cz=roller.location.y,roller.location.z
        gap=min(math.hypot(p.y-cy,p.z-cz) for p in points)-F['rollerRadius']
        report['maximumSpringSkinGapM']=max(report['maximumSpringSkinGapM'],gap);report['minimumSpringSkinGapM']=min(report['minimumSpringSkinGapM'],gap)
        ly,lz=roller.location.z,-roller.location.y
        inner=math.hypot(ly,lz)-rho
        outerGap=F['rollerRadius']+rho*math.cos(F['wedgeAngle'])-(ly*math.cos(F['wedgeAngle'])+lz*math.sin(F['wedgeAngle']))-F['rollerRadius']
        report['maximumRollerPenetrationM']=max(report['maximumRollerPenetrationM'],-inner,-outerGap)
        angle=(1-t)*a['q'][3]+t*b['q'][3];q=outer.rotation_quaternion.normalized()
        difference=2*math.atan2(q.x,q.w)-angle;err=abs(math.atan2(math.sin(difference),math.cos(difference)))
        report['maxOuterInterpolationAngleErrorRad']=max(report['maxOuterInterpolationAngleErrorRad'],err)
        report['fractionalFrames']+=1
report['blendSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
report['limits']='Quarter, half and three-quarter frame samples only. Analytic roller/race gaps and evaluated coil vertices; not a new high-frequency physical trajectory or an all-time collision proof.'
assert report['maxWireRadiusErrorM']<3e-8,report
assert report['maxHelixLengthErrorM']<1e-6,report
assert report['maximumRollerPenetrationM']<5e-8,report
assert report['minimumSpringSkinGapM']>-5e-8 and report['maximumSpringSkinGapM']<5e-8,report
assert report['maxOuterInterpolationAngleErrorRad']<1e-5,report
(ROOT/'outputs/freewheel-bench-interpolation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)
