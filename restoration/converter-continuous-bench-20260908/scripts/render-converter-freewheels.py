"""Inspection render from saved native component; does not save modified asset."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
contact='--contact-bench' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/('MAZ543A_Converter_Freewheel_ContactBench.blend' if contact else 'MAZ543A_Converter_Freewheels.blend')))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24
scene.cycles.use_denoising=True;scene.render.resolution_x=960;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.28,.31,.36,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
for ob in bpy.data.objects:
    if '_retainer_' in ob.name:ob.hide_render=True
cam=bpy.data.cameras.new('CV_inspection_camera');camera=bpy.data.objects.new('CV_inspection_camera',cam);scene.collection.objects.link(camera)
camera.location=(-.29,-.105,.055);target=Vector((-.009,0,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
cam.type='ORTHO';cam.ortho_scale=.215;cam.clip_start=.001;scene.camera=camera
for name,pos,power,size in [('key',(-.20,-.12,.21),18,.20),('fill',(-.08,.21,.08),12,.17),('rim',(.13,-.08,.17),20,.12)]:
    data=bpy.data.lights.new('CV_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new('CV_'+name,data);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
for frame,label in ([(0,'initial'),(110,'overrunning'),(200,'relocked')] if contact else [(0,'locked'),(60,'released')]):
    prefix='converter-freewheel-contact' if contact else 'converter-freewheels'
    scene.frame_set(frame);scene.render.filepath=str(ROOT/f'outputs/{prefix}-{label}.png')
    bpy.ops.render.render(write_still=True)
