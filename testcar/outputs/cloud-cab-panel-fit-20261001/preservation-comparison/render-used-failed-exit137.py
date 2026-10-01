"""Actual before/after left seat-base visibility; never hide additional geometry."""
import bpy,hashlib,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/cloud-cab-panel-fit-20261001'
OUT=BASE/'preservation-comparison';OUT.mkdir(exist_ok=True);records=[]
for label,iteration,expected in [('before-selection-bug','iteration-02',0),('after-selection-fix','iteration-03',3600)]:
 source=BASE/iteration/'MAZ543A_Master.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest()
 audit=json.loads(source.with_suffix('.readback.json').read_text());assert audit['candidate_sha256']==sha
 if expected:
  assert len(audit['seat_base_semantic_preservation'])==4 and all(x['matches_source_and_render_visible'] for x in audit['seat_base_semantic_preservation']) and not audit['native_structure_failures']
 path=OUT/('native-seat-base-'+label+'.png');assert not path.exists()
 bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(0);bpy.context.view_layer.update()
 assert len(bpy.data.objects['cab_0064'].data.vertices)==expected
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4
 scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.use_motion_blur=False
 world=bpy.data.worlds.new('Seat-base inspection world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.38,.42,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4;scene.world=world
 data=bpy.data.cameras.new('Actual footwell inspection camera');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
 cam.location=(-4.95,-1.325,1.60);target=Vector((-4.45,-1.025,1.60));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=17;data.clip_start=.01;data.clip_end=100
 ld=bpy.data.lights.new('Footwell inspection fill','AREA');ld.energy=15;ld.size=.22;l=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(l);l.location=(-4.92,-1.22,1.65);l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
 records.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':sha,'source_trial':iteration,'remaining_visible_seat_base_vertices':expected,'camera_world':[list(r) for r in cam.matrix_world],'renderer':'Cycles CPU4threads48samples no denoise','view':'Inside left front footwell, aimed at front seat base; other seat bases are verified by source hashes and render paths, not claimed visible in this image','additional_geometry_hidden_for_image':False,'source_file_changed':False,'panel_installation':'STILL FAILED / 15 rest surface pairs','all16VehicleGates':'OPEN'})
 (OUT/'render-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print('SEAT_BASE_COMPARISON_RENDERED',label,flush=True)
