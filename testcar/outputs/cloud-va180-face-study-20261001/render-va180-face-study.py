"""Actual small-scene VA180 front/oblique review, without saving staging changes."""
import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'outputs/cloud-va180-face-study-20261001/study.blend');p.add_argument('--view',choices=['front','oblique'],required=True)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=args.input.resolve();out=src.parent/('native-va180-'+args.view+'.png');assert not out.exists()
sha=hashlib.sha256(src.read_bytes()).hexdigest();audit=json.loads((src.parent/'readback.json').read_text());assert audit['source_sha256']==sha and not audit['failures']
bpy.ops.wm.open_mainfile(filepath=str(src));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=2
sc.cycles.max_bounces=8;sc.cycles.transmission_bounces=6;sc.cycles.transparent_max_bounces=6
sc.render.resolution_x=1280;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
world=bpy.data.worlds.new('VA180 inspection environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.70,.75,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;sc.world=world
def aim(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Actual study review camera');cam=bpy.data.objects.new(data.name,data);sc.collection.objects.link(cam);sc.camera=cam;data.type='ORTHO';data.ortho_scale=.123;data.clip_start=.001
cam.location=(0,0,.24) if args.view=='front' else (.10,-.055,.17);aim(cam,(0,0,-.013));
for name,loc,power,size in [('Key',(.06,.07,.16),10,.12),('Fill',(-.09,-.025,.1),4,.09)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;aim(o,(0,0,-.005))
button=bpy.data.objects['BUTTON PRESS REVIEW — travel is fitted'];button['press_mm']=0 if args.view=='front' else 1;button.update_tag();bpy.context.view_layer.update()
sc.render.filepath=str(out);bpy.ops.render.render(write_still=True);assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
r={'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_sha256':sha,'view':args.view,'camera_world':[list(row) for row in cam.matrix_world],'button_review_press_mm':button['press_mm'],'actual_renderer':'Blender Cycles CPU2/48samples, no denoise','source_saved_or_changed':False,'source_photograph_used_as_texture':False,'scope':'Independent partial front study, not installed; metric dimensions/typography/press travel fitted; upper voltage scale and minor ticks unresolved','all16VehicleGates':'OPEN'}
(src.parent/('render-'+args.view+'.json')).write_text(json.dumps(r,indent=2)+'\n');print('VA180_FACE_RENDERED',args.view,flush=True)
