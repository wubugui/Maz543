"""Check Blender geometry and native animated joints, not just JS telemetry."""
import bpy,json,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'work/d12-poses.json').read_text());spec=data['spec']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
scene=bpy.context.scene
def C(p):return Vector((p[0],-p[2],p[1]))
max_joint_error=0.;max_contact_gap=0.;min_contact_gap=1.
for f in range(1,242,4):
    scene.frame_set(f);bpy.context.view_layer.update()
    for i in range(1,7):
        master=bpy.data.objects[f'D12_master_rod_{i}'];slave=bpy.data.objects[f'D12_slave_rod_{i}']
        pL=bpy.data.objects[f'D12_piston_L{i}'];pR=bpy.data.objects[f'D12_piston_R{i}']
        errors=[((master.matrix_world@C((0,spec['mainRod'],0)))-pL.matrix_world.translation).length,
          ((master.matrix_world@C((0,spec['earAlong'],spec['earAcross'])))-slave.matrix_world.translation).length,
          ((slave.matrix_world@C((0,spec['slaveRod'],0)))-pR.matrix_world.translation).length]
        max_joint_error=max(max_joint_error,*errors)
        for bank,s in [('L',-1),('R',1)]:
            axis=C((0,math.cos(math.pi/6),s*math.sin(math.pi/6)))
            for kind in ['intake','exhaust']:
                for j in [1,2]:
                    lobe=bpy.data.objects[f'D12_cam_lobe_{bank}{i}_{kind}_{j-1}']
                    tappet=bpy.data.objects[f'D12_tappet_{bank}{i}_{kind}_{j}']
                    # Raw authored profile; bevel rounding is limited to edges.
                    cam_lower=min((lobe.matrix_world@v.co).dot(axis) for v in lobe.data.vertices)
                    flat_top=max((tappet.matrix_world@v.co).dot(axis) for v in tappet.data.vertices)
                    gap=cam_lower-flat_top;max_contact_gap=max(max_contact_gap,gap);min_contact_gap=min(min_contact_gap,gap)
assert max_joint_error<1e-6,f'Native articulated rod detached: {max_joint_error}'
assert min_contact_gap>-.000003,f'Cam penetrates actual tappet mesh: {min_contact_gap}'
assert max_contact_gap<.000025,f'Cam loses contact with actual tappet mesh: {max_contact_gap}'
for prefix,count in [('D12_piston_body_',12),('D12_gudgeon_pin_',12),('D12_valve_head_stem_',48),('D12_coil_',96),('D12_camshaft_',4),('D12_main_bearing_',7)]:
    assert len([o for o in bpy.data.objects if o.name.startswith(prefix)])==count,prefix
report={'nativeJointErrorMetres':max_joint_error,'nativeCamGapMetres':[min_contact_gap,max_contact_gap],'framesChecked':61,'nativeObjectCount':len(bpy.data.collections['D12_ENGINE'].objects),'scope':'Geometric agreement of actual native geometry; unmeasured parts remain unvalidated'}
(ROOT/'outputs/d12-native-verification.json').write_text(json.dumps(report,indent=2))
print('D12_NATIVE_VERIFIED',report,flush=True)
