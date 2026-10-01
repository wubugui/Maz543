"""Actual unaccepted panel-fit views; same left camera as the earlier driver image."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-cab-panel-fit-20261001/iteration-02'
SOURCE=OUT/'MAZ543A_Master.blend'
sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
audit=json.loads(SOURCE.with_suffix('.readback.json').read_text())
assert audit['candidate_sha256']==sha and not audit['native_structure_failures']
records=[]
for label,side in [('left',-1),('right',1)]:
 path=OUT/('native-panel-fit-'+label+'.png');assert not path.exists()
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(0);bpy.context.view_layer.update()
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4;scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.render.use_motion_blur=False
 scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 world=bpy.data.worlds.new('Panel fit review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.38,.42,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=world
 d=bpy.data.cameras.new('Fitted cabin inspection camera');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(-4.40,side*1.025,2.32);target=Vector((-4.82,side*1.025,1.97));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=17;d.clip_start=.01;d.clip_end=100
 for loc,power,size in [((-4.40,side*1.025,2.40),90,.22),((-4.9,side*1.0,2.48),50,.16)]:
  ld=bpy.data.lights.new('Cabin interior inspection fill','AREA');ld.energy=power;ld.size=size;l=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(l);l.location=loc;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==sha
 records.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':sha,'renderer':'Cycles CPU4threads64samples no denoise','camera_world':[list(r) for r in cam.matrix_world],'focal_length_mm':17,'view':label+' cabin fitted inspection','further_geometry_hidden_for_render':False,'source_saved_or_changed':False,'fit_status':'FAILED: 15 new-to-existing rest surface intersection pairs; original steering/seat intersections unresolved','all16VehicleGates':'OPEN'})
 (OUT/'render-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print('PANEL_FIT_RENDERED',label,flush=True)
