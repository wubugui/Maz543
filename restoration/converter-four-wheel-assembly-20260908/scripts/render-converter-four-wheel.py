"""Native assembly inspection renders; removable walls are hidden for visibility."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_FourWheelAssembly.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1100;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.16,.20,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
for ob in bpy.data.objects:
    if ob.get('inspectionHide')=='housing' or ob.get('shellRole'):ob.hide_render=True
camera=bpy.data.objects.new('CA_camera',bpy.data.cameras.new('CA_camera'));scene.collection.objects.link(camera)
camera.location=(-1.2,-.75,.68);target=Vector((0,0,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.9;scene.camera=camera
for name,pos,power in [('key',(-.8,.5,1),90),('fill',(.4,-.7,.4),65)]:
    light=bpy.data.lights.new('CA_'+name,'AREA');light.energy=power;light.size=.7;ob=bpy.data.objects.new('CA_'+name,light);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
for label,explode in [('assembled',False),('exploded',True)]:
    if explode:
        for key,offset in [('pump',.18),('turbine',-.20),('front_reactor',-.085),('rear_reactor',.035),('fixed_support',.28)]:bpy.data.objects['CA_'+key].location.x=offset
        camera.data.ortho_scale=1.05
    scene.render.filepath=str(ROOT/f'outputs/converter-four-wheel-{label}.png');bpy.ops.render.render(write_still=True)
