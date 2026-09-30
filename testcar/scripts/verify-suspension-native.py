import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];data=json.loads((ROOT/'work/suspension-poses.json').read_text());P=data['spec']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Suspension_Master.blend'))
def C(p):return Vector((p[0],-p[2],p[1]))
maxgap=0;clearance=1e9
for f in data['frames'][::3]:
    bpy.context.scene.frame_set(f['frame']);bpy.context.view_layer.update()
    for i in range(8):
        s=1 if i%2 else -1;n=f'S543_{i}';lower=bpy.data.objects[n+'_lower'];upper=bpy.data.objects[n+'_upper'];upright=bpy.data.objects[n+'_upright']
        a=lower.matrix_world@C((0,P['lowerEnd'][0]-P['lower'][0],s*(P['lowerEnd'][1]-P['lower'][1])))
        b=upright.matrix_world.translation;maxgap=max(maxgap,(a-b).length)
        a=upper.matrix_world@C((0,P['upperEnd'][0]-P['upper'][0],s*(P['upperEnd'][1]-P['upper'][1])))
        b=upright.matrix_world@C((0,P['upperEnd'][0]-P['lowerEnd'][0],s*(P['upperEnd'][1]-P['lowerEnd'][1])));maxgap=max(maxgap,(a-b).length)
        body=bpy.data.objects[n+'_damper_body'];rod=bpy.data.objects[n+'_damper_rod']
        clevis=lower.matrix_world@C((-.15,0,s*(P['lowerEnd'][1]-P['lower'][1])*P['damperFraction']));maxgap=max(maxgap,(clevis-body.matrix_world.translation).length)
        pistonMesh=bpy.data.objects[n+'_damper_piston'];guideMesh=bpy.data.objects[n+'_damper_rod_guide'];baseMesh=bpy.data.objects[n+'_damper_base_valve']
        pistonVertices=[(body.matrix_world.inverted()@pistonMesh.matrix_world@v.co).z for v in pistonMesh.data.vertices]
        guideBottom=min(v.co.z for v in guideMesh.data.vertices);baseTop=max(v.co.z for v in baseMesh.data.vertices)
        clearance=min(clearance,min(pistonVertices)-baseTop,guideBottom-max(pistonVertices))
assert maxgap<2e-6,maxgap
assert clearance>0,clearance
torsions=[o for o in bpy.data.objects if o.get('s543Role')=='torsion'];assert len(torsions)==16
for ob in torsions:
    assert len(ob.data.shape_keys.key_blocks)==3
    for key in list(ob.data.shape_keys.key_blocks)[1:]:
        for a,b in zip(ob.data.shape_keys.key_blocks[0].data[:32],key.data[:32]):assert (a.co-b.co).length<1e-6,'fixed torsion anchor must not rotate'
report={'sampledFrames':41,'maxNativeJointGapMetres':maxgap,'minimumSampledDamperInternalClearanceMetres':clearance,'torsionShafts':len(torsions),'scope':'Native articulation envelope, not factory dimensional verification or full fluid simulation'}
(ROOT/'outputs/suspension-native-verification.json').write_text(json.dumps(report,indent=2));print(report)
