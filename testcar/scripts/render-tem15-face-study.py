"""Real Cycles views of the independent partial TEM15 face; source photo not loaded."""
import bpy,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--view',choices=['front','oblique'],required=True);parser.add_argument('--lighting02',action='store_true');parser.add_argument('--lighting03',action='store_true');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-tem15-face-study-20261001/iteration-02';source=OUT/'study.blend';manifest=json.loads((OUT/'build.json').read_text());expected=manifest['model_sha256'];assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
assert json.loads((OUT/'readback.json').read_text())['status']=='PASS_PARTIAL_TEM15_STRUCTURE'
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.render.threads_mode='FIXED';sc.render.threads=2;sc.cycles.samples=64 if (args.lighting02 or args.lighting03) else 96;sc.cycles.use_denoising=args.lighting02 or args.lighting03;sc.cycles.max_bounces=6;sc.cycles.transmission_bounces=6;sc.render.resolution_x=720 if (args.lighting02 or args.lighting03) else 1000;sc.render.resolution_y=648 if (args.lighting02 or args.lighting03) else 900;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
w=bpy.data.worlds.new('TEM15 neutral review environment');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.16,.18,.20,1);w.node_tree.nodes['Background'].inputs[1].default_value=.4;sc.world=w
light_rows=[((.08,.08,.13),3,.07),((-.09,-.08,.10),1,.07)] if args.lighting03 else [((-.07,.08,.13),3,.09),((.09,-.04,.10),1,.07)]
for pos,power,size in light_rows:
 d=bpy.data.lights.new('Study softbox','AREA');d.energy=power*(.15 if (args.lighting02 or args.lighting03) else 1);d.size=size;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Study camera');cam=bpy.data.objects.new(d.name,d);sc.collection.objects.link(cam);sc.camera=cam;d.type='ORTHO';d.ortho_scale=.108;d.clip_start=.001;d.clip_end=5
results=[]
for view,pos in [(args.view,{'front':(0,0,.2),'oblique':(.075,-.06,.16)}[args.view])]:
 stem=view+('-lighting03' if args.lighting03 else '-lighting02' if args.lighting02 else '');p=OUT/(stem+'.png');assert not p.exists();cam.location=pos;target=Vector((0,0,-.005));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 results.append({'view':view,'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'camera_world':[list(r) for r in cam.matrix_world],'source_sha256':expected,'renderer':'Blender4.5.13 actual Cycles CPU2','samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'area_light_factor':.15 if (args.lighting02 or args.lighting03) else 1,'area_light_positions_power_size':light_rows,'source_photograph_pixels_loaded':False,'no_extra_geometry_hidden':True})
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected;(OUT/(stem+'.render.json')).write_text(json.dumps({'views':results,'source_saved':False,'scope':'Independent partial photo-form study, not installed or manufacturing geometry; all16OPEN'},indent=2)+'\n');print('TEM15_REAL_VIEWS_COMPLETE',flush=True)
