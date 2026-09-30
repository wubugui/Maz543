"""Unedited inspection images from the saved curved strip study."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1000;scene.render.resolution_y=820;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.27,.32,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
camera=bpy.data.objects.new('CS_camera',bpy.data.cameras.new('CS_camera'));scene.collection.objects.link(camera);camera.location=(-.072,-.008,.074);target=Vector((0,.008,.065));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.046;camera.data.clip_start=.0001;scene.camera=camera
for name,pos,power in [('key',(-.06,.04,.1),1.2),('fill',(-.04,-.02,.04),.7)]:
    data=bpy.data.lights.new('CS_'+name,'AREA');data.energy=power;data.size=.05;ob=bpy.data.objects.new('CS_'+name,data);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
for frame,label in [(0,'preloaded'),(12,'compressed'),(25,'limit-study')]:
    scene.frame_set(frame);scene.render.filepath=str(ROOT/f'outputs/converter-curved-strip-{label}.png');bpy.ops.render.render(write_still=True)
