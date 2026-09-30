"""Actual native before/after renders; neither output is a browser screenshot."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-tyre-lettering-20260930';views=[]
for label,filename in [('before',ROOT/'outputs/MAZ543A_Master.blend'),('after',OUT/'MAZ543A_Master.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(filename));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 world=bpy.data.worlds.new('Tyre inspection world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.24,.27,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7;scene.world=world
 target=Vector((2.42,1.1875,.77));data=bpy.data.cameras.new('Tyre inspection camera');cam=bpy.data.objects.new('Tyre inspection camera',data);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(2.42,4.5,1.1);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=1.7
 for name,pos,power,size in [('Side key',(3.8,3.2,3.2),800,1.4),('Side fill',(.1,4,2),400,2.5)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.view_layer.update();views.append({'label':label,'cameraWorld':[list(r) for r in cam.matrix_world],'orthoScale':data.ortho_scale,'resolution':[960,960]});scene.render.filepath=str(OUT/f'native-tyre-{label}.png');bpy.ops.render.render(write_still=True)
assert views[0]['cameraWorld']==views[1]['cameraWorld']
(OUT/'render-comparison.json').write_text(json.dumps({'views':views,'scope':'Native Cycles before/after from identical camera; not webpage/GPU evidence'},indent=2));print('NATIVE_TYRE_COMPARISON_RENDERED')
