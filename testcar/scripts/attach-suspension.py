import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
manifest=json.loads((ROOT/'work/mechanical-manifest.json').read_text())
def recenter(ob,world):
    children={c:c.matrix_world.copy() for c in ob.children};m=ob.matrix_world.copy();m.translation=world;ob.matrix_world=m;bpy.context.view_layer.update()
    for c,matrix in children.items():c.matrix_world=matrix
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/filename));holder=bpy.data.objects['suspension']
    for child in reversed(engine_descendants(holder)):bpy.data.objects.remove(child,do_unlink=True)
    old=bpy.data.collections.get('S543_SUSPENSION')
    if old:bpy.data.collections.remove(old)
    with bpy.data.libraries.load(str(ROOT/'outputs/MAZ543A_Suspension_Master.blend'),link=False) as (source,target):target.collections=['S543_SUSPENSION']
    collection=target.collections[0];bpy.context.scene.collection.children.link(collection)
    root=next(o for o in collection.objects if o.name=='S543_SUSPENSION');root.parent=holder;root.location=(0,0,0)
    bpy.context.scene.frame_start=0;bpy.context.scene.frame_set(0)
    rest=json.loads((ROOT/'work/suspension-poses.json').read_text())['rest']
    for name,pose in rest.items():
        ob=bpy.data.objects.get(name)
        if ob:ob.location=(pose['p'][0],-pose['p'][2],pose['p'][1]);ob.rotation_euler.x=pose['rx']
    # Recenter tyre spin at its actual .75 m centre, preserving every vertex.
    # Earlier carrier origin at .8 m introduced a 50 mm spin eccentricity.
    for w in manifest['wheels']:
        carrier=bpy.data.objects[w['carrier']];spin=bpy.data.objects[w['spin']]
        carrier.animation_data_clear();spin.animation_data_clear()
        carrier.location=(w['x'],-w['side']*2.375/2,.8 if not carrier.get('wheel_center_corrected') else .75)
        carrier.rotation_euler=(0,0,0);spin.rotation_euler=(0,0,0);bpy.context.view_layer.update()
        if not carrier.get('wheel_center_corrected'):
            world=Vector((w['x'],-w['side']*2.375/2,.75));recenter(carrier,world);bpy.context.view_layer.update();recenter(spin,world)
            carrier['wheel_center_corrected']=True
        bpy.data.objects[w['hub']].location.z=0
    poses=json.loads((ROOT/'work/suspension-poses.json').read_text())
    for i,w in enumerate(manifest['wheels']):
        carrier=bpy.data.objects[w['carrier']];spin=bpy.data.objects[w['spin']];brake=bpy.data.objects[w['brake']];brake.animation_data_clear()
        for f in poses['frames']:
            pose=f['pose'][f'S543_{i}_wheel'];p=pose['p'];rx=pose['rx'];carrier.location=(p[0],-p[2],p[1]);carrier.rotation_euler=(rx,0,0)
            carrier.keyframe_insert('location',frame=f['frame']);carrier.keyframe_insert('rotation_euler',frame=f['frame'])
            spin.rotation_euler.y=-(f['frame']-1)/240*math.pi*4;spin.keyframe_insert('rotation_euler',frame=f['frame'])
            brake.location=(p[0],-p[2]+w['side']*.29*math.cos(rx),p[1]+w['side']*.29*math.sin(rx));brake.rotation_euler=(rx,0,0)
            brake.keyframe_insert('location',frame=f['frame']);brake.keyframe_insert('rotation_euler',frame=f['frame'])
    # Preserve the neutral assembled pose at save/export, rather than leaving
    # the last articulation sample evaluated in the viewport.
    for i,w in enumerate(manifest['wheels']):
        p=rest[f'S543_{i}_wheel']['p'];carrier=bpy.data.objects[w['carrier']];carrier.location=(p[0],-p[2],p[1]);carrier.rotation_euler=(0,0,0)
        carrier.keyframe_insert('location',frame=0);carrier.keyframe_insert('rotation_euler',frame=0)
        spin=bpy.data.objects[w['spin']];spin.rotation_euler=(0,0,0);spin.keyframe_insert('rotation_euler',frame=0)
        brake=bpy.data.objects[w['brake']];brake.location=(p[0],-p[2]+w['side']*.29,p[1]);brake.rotation_euler=(0,0,0)
        brake.keyframe_insert('location',frame=0);brake.keyframe_insert('rotation_euler',frame=0)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs'/filename),compress=True)
    if filename.endswith('Textured.blend'):
        vehicle=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];bpy.ops.object.select_all(action='DESELECT')
        for o in [vehicle]+engine_descendants(vehicle):o.select_set(True)
        for name in ['D12A_525A','S543_SUSPENSION']:
            ob=bpy.data.objects.get(name)
            if ob:
                for o in [ob]+engine_descendants(ob):o.select_set(False)
        bpy.context.view_layer.objects.active=vehicle
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
print('S543 attached to both native masters; separate browser asset; wheel origins corrected.')
