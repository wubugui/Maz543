"""Read-only native equipment audit views; does not modify saved vehicle geometry."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
repo=Path(__file__).resolve().parents[2]
source=Path(os.environ.get('MAZ_REVIEW_INPUT',str(repo/'testcar/outputs/MAZ543A_Master.blend'))).resolve()
out=Path(os.environ['MAZ_REVIEW_OUT']).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
for im in bpy.data.images:
 ref=repo/'external/maz543-references'/im.name
 if im.source=='FILE' and not im.packed_file and ref.exists():im.filepath=str(ref);im.reload()
scene=bpy.context.scene;scene.frame_set(0);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
w=bpy.data.worlds.new('Equipment audit world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.28,.32,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.8;scene.world=w
cd=bpy.data.cameras.new('Equipment audit camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=9.6
cam.location=(7,8,6);target=Vector((-1.3,0,1.25));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for loc,energy in [((-3,7,10),2300),((1,-5,7),1500)]:
 d=bpy.data.lights.new('Equipment audit area','AREA');d.energy=energy;d.size=6;o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
rows=[]
for view in ['exterior','bay-cutaway']:
 hidden=[]
 if view=='bay-cutaway':
  for o in bpy.data.objects:
   if o.name.startswith(('BL_Power_bay','BL_Hood_','BL_Louver_','BL_Bay_')) and not o.hide_render:
    o.hide_render=True;hidden.append(o.name)
 scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)
 rows.append({'view':view,'file':view+'.png','hidden_for_cutaway':hidden,'camera_world':[list(r) for r in cam.matrix_world]})
(out/'render-manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'renders':rows,'native_only':True,'saved_vehicle_modified':False,'scope':'Read-only current-production geometry review. Cutaway intentionally hides listed bay skins; camera is illustrative, not photo-calibrated.'},indent=2)+'\n')
