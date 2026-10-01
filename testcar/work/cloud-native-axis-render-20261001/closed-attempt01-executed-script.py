"""Temporary native inspection only; never save, rebuild, export, or edit saved drivers."""
import bpy,sys,argparse,json,hashlib,math,itertools,os
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=argparse.ArgumentParser();P.add_argument('--candidate',required=True);P.add_argument('--verification',required=True);P.add_argument('--resource-audit',required=True);P.add_argument('--out',required=True);P.add_argument('--pose',choices=['closed','open99'],required=True);a=P.parse_args(sys.argv[sys.argv.index('--')+1:])
SRC=Path(a.candidate);OUT=Path(a.out);OUT.mkdir(exist_ok=True);REPORT=OUT/(a.pose+'-render-report.json');PNG=OUT/(a.pose+'.png');assert not REPORT.exists() and not PNG.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED='3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f';assert sha(SRC)==EXPECTED
V=json.loads(Path(a.verification).read_text());A=json.loads(Path(a.resource_audit).read_text());assert V['candidate_sha256']==EXPECTED and V['status']=='FRESH_REOPEN_DISABLE_AUTOEXEC_PASS';assert A['candidate_sha256']==EXPECTED and not A['missing_images'] and not A['missing_fonts']
S=V['specifications'];NAMES=[s['hinge'] for s in S];assert NAMES==['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007']
bpy.ops.wm.open_mainfile(filepath=str(SRC));assert bpy.app.version==(4,5,13) and not bpy.context.preferences.filepaths.use_scripts_auto_execute
scene=bpy.context.scene;scene.frame_set(0);bpy.context.view_layer.update();cab=bpy.data.objects['cab'];scope=set(cab.children_recursive)|{cab};scope.update(bpy.data.objects[n] for n in A['included_extra_geometry']);geometry=sorted([o for o in scope if o.type in {'MESH','CURVE','FONT','SURFACE','META'}],key=lambda o:o.name);assert [o.name for o in geometry]==[o['name'] for o in A['scope_geometry']]
original_render_flags={o.name:o.hide_render for o in scope};original_materials={o.name:[m.name if m else None for m in o.data.materials] for o in geometry};original_material_count=len(bpy.data.materials)
# Read and pin pristine saved expressions/targets; no expression, target, transform-channel write.
def drivers():
 records=[]
 for s,baseline in zip(S,V['driver_records']):
  h=bpy.data.objects[s['hinge']];assert json.loads(h['maz_native_axis_control_v1'])==s
  assert h.rotation_mode=='QUATERNION' and h.parent==cab and not h.constraints
  ui=h.id_properties_ui('open_angle_deg').as_dict();assert ui['min']==0 and ui['max']==99 and ui['default']==0
  ad=h.animation_data;assert ad and not ad.action and not ad.nla_tracks and len(ad.drivers)==4
  expected={(r['data_path'],r['array_index']):r for r in baseline['drivers']}
  ds=[]
  for f in ad.drivers:
   d=f.driver;ref=expected[(f.data_path,f.array_index)]
   assert not f.mute and not f.lock and f.is_valid and d.is_valid and d.is_simple_expression
   assert d.type=='SCRIPTED' and not d.use_self and d.expression==ref['expression']
   assert not f.modifiers and not f.keyframe_points and not f.sampled_points and len(d.variables)==1
   v=d.variables[0];assert v.name=='a' and v.type=='SINGLE_PROP' and len(v.targets)==1
   t=v.targets[0];assert t.id==h and t.id_type=='OBJECT' and t.data_path=='["open_angle_deg"]' and not t.use_fallback_value
   ds.append({'data_path':f.data_path,'array_index':f.array_index,'expression':d.expression,'is_valid':f.is_valid,'driver_valid':d.is_valid,'simple_expression':d.is_simple_expression,'variable':v.name,'target_object':t.id.name,'target_data_path':t.data_path,'modifiers':len(f.modifiers)})
  records.append({'hinge':h.name,'angle_property':h['open_angle_deg'],'drivers':ds})
 return records
saved_drivers=drivers();assert all(r['angle_property']==0 for r in saved_drivers)

def set_degrees(deg):
 assert deg in {0,99}
 for n in NAMES:
  h=bpy.data.objects[n];h['open_angle_deg']=float(deg);h.update_tag(refresh={'OBJECT'})
 bpy.context.view_layer.update()

def vertices(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh()
 try:
  xyz=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3);w=np.asarray(e.matrix_world,dtype=np.float64);return xyz@w[:3,:3].T+w[:3,3]
 finally:e.to_mesh_clear()

# Isolation excludes only objects outside the fully listed cab scope. No cab flag is changed.
isolation=[]
for o in list(bpy.data.objects):
 if o not in scope and not o.hide_render:
  isolation.append({'name':o.name,'type':o.type,'original_hide_render':False});o.hide_render=True
bpy.context.view_layer.update()
visible=[o for o in geometry if not o.hide_render]
# Preserve original collection visibility and per-ray flags. Names are not a physical acceptance gate.
collection_flags=[{'name':c.name,'hide_render':c.hide_render} for c in bpy.data.collections]
assert len(visible)==472
for o in scope:assert o.hide_render==original_render_flags[o.name]
pose_records=[];pose_bounds=[];closed_tips={};tip_ids={w['hinge']:(w['tip_object'],w['tip_vertex']) for w in V['poses'][0]['actual_angle_and_tip_witnesses']}
for deg in [0,99]:
 set_degrees(deg);dg=bpy.context.evaluated_depsgraph_get();points=[];witnesses=[]
 for o in visible:
  vs=vertices(o,dg)
  if len(vs):points.extend([vs.min(0).tolist(),vs.max(0).tolist()])
 for s in S:
  h=bpy.data.objects[s['hinge']];e=h.evaluated_get(dg);matrix=np.asarray(e.matrix_world);actual=math.degrees(math.atan2(matrix[1,0],matrix[0,0]));requested=deg*s['angle_sign'];assert abs(actual-requested)<2e-5
  obj,index=tip_ids[h.name];tip=vertices(bpy.data.objects[obj],dg)[index]
  if deg==0:closed_tips[h.name]=tip.copy()
  distance=float(np.linalg.norm(tip-closed_tips[h.name]));assert distance>1.0 if deg==99 else distance==0
  witnesses.append({'hinge':h.name,'property_deg':h['open_angle_deg'],'requested_signed_angle_deg':requested,'actual_evaluated_signed_angle_deg':actual,'shell_tip_object':obj,'shell_tip_vertex':index,'shell_tip_world':tip.tolist(),'shell_tip_displacement_from_closed_m':distance})
 points=np.asarray(points);minimum=points.min(0);maximum=points.max(0);pose_bounds.extend([minimum,maximum]);pose_records.append({'pose_deg':deg,'bounds_world':[minimum.tolist(),maximum.tolist()],'witnesses':witnesses,'driver_checks':drivers()})
union=np.asarray(pose_bounds);minimum=union.min(0);maximum=union.max(0);corners=[Vector(v) for v in itertools.product(*zip(minimum,maximum))];target=(Vector(minimum)+Vector(maximum))/2
# Explicit rendering, compositing, color, lighting and camera settings supersede inherited inspection setup only.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=False;scene.cycles.seed=20261001;scene.cycles.use_animated_seed=False
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3;scene.cycles.transmission_bounces=6;scene.cycles.transparent_max_bounces=8
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=20;scene.render.film_transparent=False;scene.render.use_motion_blur=False;scene.render.use_border=False;scene.render.use_crop_to_border=False
scene.use_nodes=False;scene.render.use_compositing=False;scene.render.use_sequencer=False;scene.display_settings.display_device='sRGB';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0.;scene.view_settings.gamma=1.;scene.view_settings.use_curve_mapping=False;scene.render.dither_intensity=1.
world=bpy.data.worlds.new('INSPECTION ONLY - explicit world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.125,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
cd=bpy.data.cameras.new('INSPECTION ONLY - same-camera union frame');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);cam.location=target+Vector((-8.,-7.,5.));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=4.;cd.clip_start=.01;cd.clip_end=100;scene.camera=cam
for _ in range(80):
 bpy.context.view_layer.update();uv=[world_to_camera_view(scene,cam,p) for p in corners]
 if all(.065<=p.x<=.935 and .21<=p.y<=.79 for p in uv):break
 cd.ortho_scale*=1.03
assert all(.065<=p.x<=.935 and .21<=p.y<=.79 for p in uv),'Framing clipped union bound'
lights=[]
for name,offset,energy,size in [('key',(-3,-5,7),1100,5),('fill',(-4,5,4),850,5),('rim',(5,1,5),1000,4)]:
 ld=bpy.data.lights.new('INSPECTION ONLY - '+name,'AREA');ld.energy=energy;ld.shape='DISK';ld.size=size;l=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(l);l.location=target+Vector(offset);l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler();lights.append({'name':name,'location':list(l.location),'rotation':list(l.rotation_euler),'energy_w':energy,'size_m':size})
# New camera-facing native FONT annotations use Blender builtin font, no image editing or scene asset replacement.
lm=bpy.data.materials.new('INSPECTION ONLY - label emission');lm.use_nodes=True;ns=lm.node_tree.nodes;ns.clear();em=ns.new('ShaderNodeEmission');em.inputs[0].default_value=(.85,.91,1,1);em.inputs[1].default_value=1.;mo=ns.new('ShaderNodeOutputMaterial');lm.node_tree.links.new(em.outputs[0],mo.inputs['Surface'])
width=cd.ortho_scale;height=width*scene.render.resolution_y/scene.render.resolution_x
labels=[('MAZ-543A | NATIVE SAVED CANDIDATE',.452,.0185),('ALL FOUR DOORS: '+('CLOSED / 0 deg' if a.pose=='closed' else 'OPEN / 99 deg')+'  |  ISOLATED COMPLETE CAB',.402,.016),('Saved scalar properties drive the original four controllers',.358,.013),('Same camera + original materials | Native Cycles CPU2 | Candidate SHA 3b230c12',-.378,.012),('LOCAL ONLY / LFS BLOCKED | No whole-vehicle or browser acceptance',-.418,.012),('Axis controls only: no 140-head repair or new step layout | 6 contacts + 16 gates OPEN',-.458,.0115)]
for i,(body,y,size) in enumerate(labels):
 t=bpy.data.curves.new('INSPECTION ONLY - label '+str(i),'FONT');t.body=body;t.align_x='LEFT';t.size=width*size;t.space_character=1.;o=bpy.data.objects.new(t.name,t);scene.collection.objects.link(o);o.parent=cam;o.location=(-width*.455,height*y,-2.);o.rotation_euler=(0,0,0);t.materials.append(lm);o.visible_shadow=False
set_degrees(0 if a.pose=='closed' else 99);final_before=drivers();bpy.context.view_layer.update()
for o in scope:assert o.hide_render==original_render_flags[o.name]
for o in geometry:assert [m.name if m else None for m in o.data.materials]==original_materials[o.name]
r={'status':'READY_TO_RENDER','candidate':str(SRC),'candidate_sha256':EXPECTED,'candidate_bytes':SRC.stat().st_size,'source_saved':False,'asset_status':'LOCAL_ONLY_LFS_BLOCKED','blender':bpy.app.version_string,'autoexec_enabled':False,'script_sha256':sha(__file__),'verification_report_sha256':sha(a.verification),'resource_audit_sha256':sha(a.resource_audit),'pose':a.pose,'frame':0,'pose_regression':pose_records,'saved_driver_records_before_any_property_write':saved_drivers,'render_pose_driver_records':final_before,'union_bounds_world':[minimum.tolist(),maximum.tolist()],'union_corner_projected_coordinates':[list(v) for v in uv],'camera_world':[list(row) for row in cam.matrix_world],'ortho_scale':cd.ortho_scale,'original_geometry_count':len(geometry),'retained_originally_render_visible_geometry_count':len(visible),'geometry_retained':[o.name for o in geometry],'extra_retained_outside_cab_root':A['included_extra_geometry'],'scope_render_flags_unchanged':True,'outside_scope_temporary_hidden':isolation,'original_collection_flags_retained':collection_flags,'original_material_bindings_unchanged':True,'original_material_count':original_material_count,'material_changes':'None. One NEW annotation-only emission material; original materials and nodes untouched.','image_font_resource_changes':'None; all preflight resources available, no remapping/reloading/substitution.','mesh_geometry_changes':'None','compositor':'Disabled; inherited compositor and sequencer bypassed','camera_view':'Front-left elevated orthographic. Occlusion remains; numerical witnesses verify all four saved controls.','render_settings':{'engine':'CYCLES','device':'CPU','threads':2,'samples':32,'denoising':True,'resolution':[1600,1100],'view_transform':'AgX','look':'AgX - Medium High Contrast','exposure':0,'gamma':1,'world_rgba':[.10,.125,.16,1],'world_strength':.5,'lights':lights,'motion_blur':False,'max_bounces':6,'transmission_bounces':6,'transparent_bounces':8},'labels':[x[0] for x in labels],'limits':['Explicit isolated cab hierarchy plus 24 named front parts; outside-cab original render objects temporarily hidden only for the inspection','All original in-scope geometry and original hidden states retained including old geometry; no collision-improvement claim','Two endpoint views only, no continuous-clearance, manufacturer, mechanism, physics or browser acceptance','No 140-head repair or new step layout incorporated','Original six closed contacts and all sixteen vehicle gates remain OPEN']}
REPORT.write_text(json.dumps(r,indent=2)+'\n');scene.render.filepath=str(PNG);bpy.ops.render.render(write_still=True)
assert sha(SRC)==EXPECTED and drivers()==final_before
for o in scope:assert o.hide_render==original_render_flags[o.name]
r.update(status='NATIVE_RENDER_COMPLETE_PENDING_PIXEL_REVIEW',candidate_sha256_after=sha(SRC),image={'file':PNG.name,'bytes':PNG.stat().st_size,'sha256':sha(PNG)},driver_records_after_render=drivers());REPORT.write_text(json.dumps(r,indent=2)+'\n');print('NATIVE_SAVED_CONTROL_RENDERED',a.pose,PNG,flush=True)
