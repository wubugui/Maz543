"""Render the unaccepted steering pose from the same actual footwell camera."""
import bpy,hashlib,json,argparse,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/cloud-steering-photo-hypothesis-20261001'
source=BASE/'MAZ543A_Master.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest()
audit=json.loads(source.with_suffix('.readback.json').read_text())
assert audit['candidate_sha256']==sha and not audit['saved_identity_failures'] and len(audit['rest_surface_intersections'])==1 and len(audit['additional_known_panel_wall_intersections'])==2
ap=argparse.ArgumentParser();ap.add_argument('--view',choices=['footwell','cab'],default='footwell');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
expected=3600;path=BASE/('native-steering-photo-hypothesis-'+args.view+'.png');assert not path.exists()
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(0);bpy.context.view_layer.update()
assert len(bpy.data.objects['cab_0064'].data.vertices)==expected
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.cycles.max_bounces=4;scene.cycles.glossy_bounces=2;scene.cycles.transmission_bounces=4;scene.cycles.transparent_max_bounces=4
scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.use_motion_blur=False
world=bpy.data.worlds.new('Seat-base inspection world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.38,.42,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
data=bpy.data.cameras.new('Actual footwell inspection camera');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
cam.location=(-4.95,-1.325,1.60);target=Vector((-4.45,-1.025,1.60));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=17;data.clip_start=.01;data.clip_end=100
ld=bpy.data.lights.new('Footwell inspection fill','AREA');ld.energy=15;ld.size=.22;l=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(l);l.location=(-4.92,-1.22,1.65);l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
if args.view=='cab':
 cam.location=(-4.40,-1.025,2.32);target=Vector((-4.82,-1.025,1.97));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.resolution_x=1000;scene.render.resolution_y=1000
 l.location=(-4.43,-1.025,2.22);ld.energy=20;ld.size=.30;l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
record={'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':sha,'camera_world':[list(r) for r in cam.matrix_world],'renderer':'Cycles CPU2threads32samples no denoise, max bounces4 glossy2 transmission4 transparent4','comparison':('Same camera and lighting as cloud-cab-panel-fit-20261001/preservation-comparison-recovery; compare its after-selection-fix image' if args.view=='footwell' else 'General left-cab view; not a matched before/after photometric comparison'),'all_seat_bases_retained':True,'additional_geometry_hidden_for_image':False,'source_file_changed':False,'installation':'FAILED: one scoped steering/cushion and two separate panel/wall object pairs','all16VehicleGates':'OPEN'}
(BASE/('render-provenance-'+args.view+'.json')).write_text(json.dumps(record,indent=2)+'\n');print('STEERING_HYPOTHESIS_RENDERED',flush=True)
