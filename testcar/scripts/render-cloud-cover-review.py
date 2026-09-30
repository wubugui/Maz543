"""Render actual saved candidate for native visual inspection, not web evidence."""
import bpy,os,math,json
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(os.environ['MAZ_CANDIDATE_DIR']).resolve()
bpy.ops.wm.open_mainfile(filepath=str(root/'MAZ543A_Master.blend'))
repo=Path(__file__).resolve().parents[2]
for image in bpy.data.images:
    ref=repo/'external/maz543-references'/image.name
    if image.source=='FILE' and not image.packed_file and ref.exists():image.filepath=str(ref);image.reload()
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
world=bpy.data.worlds.new('Cloud inspection world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.20,.23,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7;scene.world=world
cam_data=bpy.data.cameras.new('Cloud review camera');cam=bpy.data.objects.new('Cloud review camera',cam_data);scene.collection.objects.link(cam);scene.camera=cam
cam.location=(-8.6,-5.8,5.6);target=Vector((-4.4,0,2.18));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=3.65
for name,position,power,size in [('Cloud key',(-7,-5,9),1800,5),('Cloud fill',(-2,5,7),1300,4)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=position;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
hinge=bpy.data.objects['BL_Front_cover_hinge'];base=hinge.matrix_basis.copy()
for angle in [0,60]:
 hinge.matrix_basis=base@Matrix.Rotation(math.radians(angle),4,'Y');bpy.context.view_layer.update();scene.render.filepath=str(root/f'native-cover-{angle:02d}.png');bpy.ops.render.render(write_still=True)
print('NATIVE_REVIEW_RENDERED')
