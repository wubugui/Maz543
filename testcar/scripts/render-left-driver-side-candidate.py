"""Actual same-camera left-cab interior comparison, no geometry hidden/replaced."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-left-driver-side-20261001';records=[]
for label,path in [('before',ROOT/'outputs/cloud-hood-tyre-composite-20261001/MAZ543A_Master.blend'),('after',OUT/'MAZ543A_Master.blend')]:
 sha=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;scene.frame_set(0);bpy.context.view_layer.update()
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4;scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.use_motion_blur=False
 scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 world=bpy.data.worlds.new('Driver side review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.38,.42,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=world
 d=bpy.data.cameras.new('Driver seat inspection camera');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(-4.40,-1.025,2.32);target=Vector((-4.82,-1.025,1.97));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=17;d.clip_start=.01;d.clip_end=100
 for loc,power,size in [((-4.40,-1.025,2.40),90,.22),((-4.9,-1.0,2.48),50,.16)]:
  ld=bpy.data.lights.new('Driver interior inspection fill','AREA');ld.energy=power;ld.size=size;l=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(l);l.location=loc;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/('left-cab-'+label+'.png'));bpy.ops.render.render(write_still=True)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
 records.append({'file':'left-cab-'+label+'.png','source_sha256':sha,'actual_renderer':'Cycles CPU4 threads24samples denoise','camera_world':[list(r) for r in cam.matrix_world],'focal_length_mm':17,'view':'Inside vehicle LEFT cab, facing forward from driver eye vicinity; fitted inspection camera','geometry_hidden_for_render':False,'source_saved_or_changed':False,'all16VehicleGates':'OPEN'});(OUT/'render-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print('LEFT_CAB_RENDERED',label,flush=True)
