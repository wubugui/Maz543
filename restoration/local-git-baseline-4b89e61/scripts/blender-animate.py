import bpy,json,math
from mathutils import Vector,Quaternion
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/'MAZ543A_Textured.blend'))
data=json.loads((ROOT/'work'/'animation-keyframes.json').read_text())
# Align the existing door pivots with the authored hinge lines without moving skin.
for name,x in [('cab_pivot_002',-4.91),('cab_pivot_003',-3.96),('cab_pivot_006',-4.91),('cab_pivot_007',-3.96)]:
    obj=bpy.data.objects[name];world={child:child.matrix_world.copy() for child in obj.children};obj.location.x=x;bpy.context.view_layer.update()
    for child,matrix in world.items():child.matrix_world=matrix
count=0
for node in data['nodes']:
    obj=bpy.data.objects.get(node['name'])
    if obj is None:continue
    obj.animation_data_clear();obj.rotation_mode='QUATERNION'
    for f in node['frames']:
        x,y,z=f['p'];obj.location=(x,-z,y)
        x,y,z,w=f['q'];obj.rotation_quaternion=(w,x,-z,y)
        x,y,z=f['s'];obj.scale=(x,z,y)
        for channel in ['location','rotation_quaternion','scale']:obj.keyframe_insert(data_path=channel,frame=f['frame'],group='Mechanical demonstration')
    count+=1
scene=bpy.context.scene;scene.render.fps=30;scene.frame_start=1;scene.frame_end=301
for name,frame in [('V12_SLOW_CYCLE',1),('STEERING_AND_SUSPENSION',121),('DOOR_INSPECTION',241)]:
    scene.timeline_markers.new(name,frame=frame)
scene.frame_set(1)
root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
bpy.ops.object.select_all(action='DESELECT')
def select_tree(o):
    o.select_set(True)
    for c in o.children:select_tree(c)
select_tree(root);bpy.context.view_layer.objects.active=root
for obj in bpy.context.selected_objects:
    if obj.type=='MESH' and any(len(p.vertices)>4 for p in obj.data.polygons):
        if not obj.modifiers.get('Export tangent triangulation'):
            mod=obj.modifiers.new('Export tangent triangulation','TRIANGULATE');mod.keep_custom_normals=True
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public'/'models'/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
text=bpy.data.texts.get('READ_ME__MODEL_SCOPE');text.write('\nNative timeline: frames1-120 engine,121-240 steering/suspension,241-301 door opening. Keyframes are baked from the browser kinematics. They are educational motion, not validated physical multibody simulation. Cycles GPU studio is included. Browser GLB exports the neutral pose; web code supplies live control.')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs'/'MAZ543A_Textured.blend'),compress=True)
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.filepath=str(ROOT/'outputs'/'maz543a-textured-preview.png');scene.cycles.samples=64;bpy.ops.render.render(write_still=True)
print('ANIMATED_NODES',count,flush=True)
