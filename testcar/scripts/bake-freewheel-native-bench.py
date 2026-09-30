"""Bake actual contact trace, roller spin and shared continuous spring shape."""
import bpy,bmesh,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_continuous_spring import geometry
D=json.loads((ROOT/'work/freewheel-contact/native-bench.json').read_text());F=D['fit']
source=ROOT/'outputs/MAZ543A_Converter_Freewheels.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceBlendSha256']
bpy.ops.wm.open_mainfile(filepath=str(source))
for ob in bpy.data.objects:
    ob.animation_data_clear()
    if ob.type=='MESH' and ob.data.shape_keys:ob.data.shape_keys.animation_data_clear()
def C(p):return Vector((p[0],-p[2],p[1]))
def rotation(ob,angle,frame):
    ob.rotation_mode='QUATERNION';ob.rotation_quaternion=(math.cos(angle/2),math.sin(angle/2),0,0)
    ob.keyframe_insert('rotation_quaternion',frame=frame)
root=bpy.data.objects['S543_CONVERTER_FREEWHEELS']
if 'CV_READ_ME' in bpy.data.texts:
    old=bpy.data.texts['CV_READ_ME'];old.name='SOURCE_ENDPOINT_README'
    content=old.as_string();old.clear();old.write('Historical source-component notes. Animation statements below describe the source endpoint asset, not this continuous bench. See CONTINUOUS_FREEWHEEL_BENCH.\n\n'+content)
template=bpy.data.objects['CV_front_engagement_spring_0'];material=template.data.materials[0]
s0=D['samples'][0];points,faces=geometry(F,s0['q'][0],s0['q'][1],s0['springLength'])
mesh=bpy.data.meshes.new('CV_continuous_shared_coil');mesh.from_pydata([C(p) for p in points],[],faces);mesh.materials.append(material);mesh.update()
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for face in mesh.polygons:face.use_smooth=True
template.data=mesh;template.shape_key_add(name='Basis');mesh.shape_keys.use_relative=False
for row,x in zip(['front','rear'],F['rowX']):
    for j in range(F['rollerCount']):
        spring=bpy.data.objects[f'CV_{row}_engagement_spring_{j}'];spring.data=mesh;spring.location=C((x,0,0))
        spring['springGeometry']='Solver coil length, fixed wire radius and inextensible ideal helix centreline; full constitutive elasticity not solved.'
for sample in D['samples']:
    frame=sample['frame'];y,z,spin,angle=sample['q'];co=math.cos(angle);si=math.sin(angle)
    localY=co*y+si*z;localZ=-si*y+co*z
    if frame:
        points,_=geometry(F,localY,localZ,sample['springLength']);block=template.shape_key_add(name=f'T_{frame:04d}')
        for vertex,p in zip(block.data,points):vertex.co=C(p)
    else:block=mesh.shape_keys.key_blocks[0]
    block.interpolation='KEY_LINEAR';mesh.shape_keys.eval_time=block.frame;mesh.shape_keys.keyframe_insert('eval_time',frame=frame)
    for row,x in zip(['front','rear'],F['rowX']):
        outer=bpy.data.objects['CV_'+row+'_outer'];rotation(outer,angle,frame)
        for j in range(F['rollerCount']):
            roller=bpy.data.objects[f'CV_{row}_roller_{j}'];roller.location=C((x,localY,localZ));roller.keyframe_insert('location',frame=frame)
            rotation(roller,spin-angle,frame)
    for name,value in [('simulation_time_s',sample['time']),('applied_torque_Nm_per_row',sample['torque']),
        ('spring_length_m',sample['springLength']),('spring_axial_force_N',sample['springAxialForce']),
        ('spring_contact_force_N',sample['springForce']),('inner_normal_force_N',sample['normalForce'][0]),
        ('outer_normal_force_N',sample['normalForce'][1]),('inner_friction_force_N',sample['frictionForce'][0]),
        ('outer_friction_force_N',sample['frictionForce'][1]),('kinetic_energy_J_per_row',sample['kinetic'])]:
        root[name]=float(value);root.keyframe_insert(data_path='["'+name+'"]',frame=frame)
# Linear quaternion channels otherwise distort time within large angular steps.
# Subdivide the same recorded angular trajectory; this is not added physics data.
rotationSubkeys=0
for a,b in zip(D['samples'],D['samples'][1:]):
    count=max(1,math.ceil(abs(b['q'][3]-a['q'][3])/.1))
    for k in range(1,count):
        t=k/count;angle=a['q'][3]*(1-t)+b['q'][3]*t
        for row in ['front','rear']:rotation(bpy.data.objects['CV_'+row+'_outer'],angle,a['frame']+t)
        rotationSubkeys+=1
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for curve in ob.animation_data.action.fcurves:
            for key in curve.keyframe_points:key.interpolation='LINEAR'
for curve in mesh.shape_keys.animation_data.action.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
scene=bpy.context.scene;scene.render.fps=D['fps'];scene.frame_start=0;scene.frame_end=D['samples'][-1]['frame'];scene.frame_set(0)
root['motionStatus']='Continuous contact bench: two rows replay the same prescribed external-torque case. Not converter-fluid or whole-vehicle animation.'
root['outerRotationSubkeysPerRow']=rotationSubkeys
text=bpy.data.texts.new('CONTINUOUS_FREEWHEEL_BENCH');text.write(D['limits']+'\n100 Hz saved keys over 2 physical seconds. Initial/0.4s -2 Nm; then +2 Nm until 1.2s; then -2 Nm. Coils share one absolute shape-key mesh. Intermediate interpolation is a sampled approximation; saved-frame geometry and force parity require separate readback.\n')
root['solverSha256']=D['solverSha256'];root['diagnosticSha256']=D['diagnosticSha256'];root['sourceBlendSha256']=D['sourceBlendSha256']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_Freewheel_ContactBench.blend'),compress=True)
print('SAVED FREEWHEEL CONTACT BENCH',len(D['samples']),'states',flush=True)
