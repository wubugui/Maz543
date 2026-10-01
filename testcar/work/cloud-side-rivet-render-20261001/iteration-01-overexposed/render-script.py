"""Actual native same-camera isolated before/after inspection; no model save.

PNG destinations are supplied explicitly. No output is added to Git or converted
to a text container; new LFS publication remains a separate required step.
"""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['before','after'],required=True);p.add_argument('--output-root',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=Path(a.output_root).resolve();OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
image=OUT/('native-rivet-'+a.mode+'.png');assert not image.exists(),'Retain previous image; choose a new output directory'
replay=None
if a.mode=='after':
 script=ROOT/'scripts/trial-side-rivet-native-attachment.py'
 assert sha(script)=='ec3237350de3f7443048993f56e8945b6a1b51e3a1d9285fae10d15dd2b4ec01'
 spec=importlib.util.spec_from_file_location('native_attachment_replay',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 replay=module.run(out=OUT/'attachment-replay')
 assert replay['status']=='FITTED_NATIVE_HEAD_ATTACHMENT_TRIAL_PASS'
else:
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
scene=bpy.context.scene;names=['BL_Cab_-1_side_monocoque','BL_Cab_-1_side_rivets']

def signature():
 dg=bpy.context.evaluated_depsgraph_get();h=hashlib.sha256()
 for name in names:
  o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh()
  try:
   coords=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',coords)
   m.calc_loop_triangles();tris=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',tris)
   h.update(name.encode());h.update(coords.tobytes());h.update(tris.tobytes());h.update(np.asarray(e.matrix_world,dtype=np.float64).tobytes())
  finally:e.to_mesh_clear()
 return h.hexdigest()
original_signature=signature()
for o in bpy.data.objects:
 if o.type in {'MESH','CURVE','FONT','SURFACE','META','VOLUME','POINTCLOUD','LIGHT'}:o.hide_render=o.name not in names
# Temporary copies permit diagnostic finish only, never mutation of shared data.
for name,color in [(names[0],(.16,.25,.18,1)),(names[1],(.68,.45,.19,1))]:
 o=bpy.data.objects[name];o.data=o.data.copy();mat=bpy.data.materials.new('DIAGNOSTIC inspection '+name);mat.use_nodes=True
 n=mat.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=color;n.inputs['Metallic'].default_value=.12;n.inputs['Roughness'].default_value=.48
 o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0
# Actual original component60, fixed lower side-sill row. Same fixed view for both.
center=Vector((-3.8103582859039307,1.512,1.1445000171661377))
cd=bpy.data.cameras.new('Native attachment inspection same camera');camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera)
scene.camera=camera;cd.type='ORTHO';cd.ortho_scale=.085;cd.clip_start=.001;cd.clip_end=100
camera.location=center+Vector((.16,.06,.035));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
for label,delta,power,size in [('key',(.035,.11,.08),9,.12),('fill',(-.05,.10,.035),3,.08)]:
 d=bpy.data.lights.new('DIAGNOSTIC '+label,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o)
 o.location=center+Vector(delta);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
w=bpy.data.worlds.new('Native inspection world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.1,.13,.16,1);w.node_tree.nodes['Background'].inputs[1].default_value=.3;scene.world=w
mat=bpy.data.materials.new('DIAGNOSTIC caption emission');mat.use_nodes=True
nodes=mat.node_tree.nodes;nodes.clear();em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.92,.96,1,1);em.inputs['Strength'].default_value=1
output=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(em.outputs[0],output.inputs['Surface'])
caption='NATIVE / ORIGINAL' if a.mode=='before' else 'NATIVE / FITTED ATTACHMENT TRIAL'
line='Original head: 11.99996 mm stand-off' if a.mode=='before' else 'Same head: base now meets original skin'
for title,y,size in [(caption,.027,.0024),(line,-.023,.00185),('Isolated native geometry; gold/green = inspection finish',-.027,.00135)]:
 cu=bpy.data.curves.new('Inspection label','FONT');cu.body=title;cu.size=size;cu.materials.append(mat);o=bpy.data.objects.new(cu.name,cu);scene.collection.objects.link(o);o.parent=camera;o.location=(-.037,y,-.10)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.use_motion_blur=False;scene.render.filepath=str(image);scene.render.film_transparent=False
bpy.context.view_layer.update();assert signature()==original_signature,'Inspection setup changed geometry'
bpy.ops.render.render(write_still=True)
assert signature()==original_signature and sha(SOURCE)==EXPECTED
r={'status':'ACTUAL_NATIVE_RENDER_COMPLETED_NOT_VISUALLY_ACCEPTED_YET','mode':a.mode,'source_sha256':EXPECTED,
 'source_sha256_after':sha(SOURCE),'saved_blend':False,'native_asset_published':False,'png_lfs_published':False,
 'image_filename':image.name,'image_bytes':image.stat().st_size,'image_sha256':sha(image),'shown_objects':names,
 'inspected_component':60,'diagnostic_material_override':{'skin':'green','original_retained_heads':'gold'},
 'camera_world_matrix':[list(x) for x in camera.matrix_world],'ortho_scale':cd.ortho_scale,'target':list(center),
 'engine':'Cycles CPU2 32samples native denoise','resolution':[1200,900],'evaluated_geometry_signature_before_after_exact':original_signature,
 'replay_report_sha256':sha(OUT/'attachment-replay/attachment-report.json') if replay else None,
 'limits':['Isolated geometry and diagnostic finish, not full vehicle appearance or original paint','Native Blender render, not browser execution or screenshot','Fitted attachment repair, not factory head/fastener/batch acceptance','All10 unsupported heads and known6 closed contacts retained in replay; local view does not show all of them','Source remains unchanged; PNG exists locally only until explicit authorized delivery']}
(OUT/('render-'+a.mode+'.json')).write_text(json.dumps(r,indent=2)+'\n')
print('NATIVE_ATTACHMENT_RENDER',a.mode,str(image),sha(image),flush=True)
