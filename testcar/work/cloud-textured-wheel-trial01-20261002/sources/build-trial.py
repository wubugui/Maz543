"""Native Textured front-four parent/animation study; never replace the source.

Uses retained meshes only. The original four kingpins' evaluated MetricUV
instability stays a separate known failure; no UV tolerance is introduced.
"""
import argparse, ast, hashlib, json, math, sys, traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector

p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);input_path=Path(a.inputs);out=Path(a.output)
I=json.loads(input_path.read_text());source=Path(I['source_path']);sha=lambda b:hashlib.sha256(b).hexdigest()
report={'status':'IN_PROGRESS_NOT_VALIDATED','saved_blend':False,'source_sha256':I['source_sha256'],
 'scope':'Existing zero-camber front-four hierarchy and original spin Euler-action activation; finite samples only',
 'known_open':['Original exact132-mesh evaluated-UV intake remains BLOCKED','Steering, CV, suspension installation and continuous mechanics remain unqualified','All16 vehicle gates OPEN','New binary is LOCAL_ONLY_LFS_BLOCKED; no export or browser claim']}
def write(name,value):
 with (out/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def update():bpy.context.view_layer.update()
def ob(name):return bpy.data.objects[name]
def matrix(o):return np.asarray(o.matrix_world,dtype=np.float64)
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def worlds():return {o.name:matrix(o).tolist() for o in bpy.data.objects}
def reparent(o,parent):
 m=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_world=m;update()

def main():
 helper=input_path.parent/'intake-helper-source.py';helper_bytes=helper.read_bytes()
 assert sha(helper_bytes)==I['helper_sha256']
 tree=ast.parse(helper_bytes);defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main']
 oldmain=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 stop=next(i for i,n in enumerate(oldmain.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='report' and isinstance(t.slice,ast.Constant) and t.slice.value=='station_fits' for t in n.targets))
 preflight=ast.FunctionDef(name='preflight',args=oldmain.args,body=oldmain.body[:stop+1]+[ast.Return(value=ast.Call(func=ast.Name(id='locals',ctx=ast.Load()),args=[],keywords=[]))],decorator_list=[])
 H=dict(bpy=bpy,np=np,json=json,math=math,hashlib=hashlib,sha=sha,I=I,input_path=input_path,out=out,source=source,issues=[],report={})
 exec(compile(ast.fix_missing_locations(ast.Module(body=defs+[preflight],type_ignores=[])),str(helper),'exec'),H)
 L=H['preflight']();assert not H['issues'],H['issues']
 write('preflight-summary.json',{k:v for k,v in H['report'].items() if k not in {'object_records','material_records'}})
 scope=set(I['scope_names']);moving_names=sorted(n for n in scope if ob(n).type=='MESH')
 assert len(scope)==160 and len(moving_names)==128 and all(not ob(n).modifiers for n in moving_names)
 assert len(bpy.data.objects)==8518 and not bpy.data.libraries
 handlers={n:len(getattr(bpy.app.handlers,n)) for n in ['frame_change_pre','frame_change_post','depsgraph_update_pre','depsgraph_update_post']}
 assert not any(handlers.values()),handlers
 simulation=[]
 for o in bpy.data.objects:
  if o.rigid_body or o.rigid_body_constraint or o.particle_systems or o.pose:simulation.append(o.name)
  for m in o.modifiers:
   if m.type in {'CLOTH','FLUID','SOFT_BODY','DYNAMIC_PAINT','MESH_CACHE','MESH_SEQUENCE_CACHE','PARTICLE_SYSTEM','OCEAN','NODES'}:simulation.append(o.name+':'+m.type)
 assert not simulation,simulation
 assert not bpy.context.scene.rigidbody_world and not bpy.data.cache_files
 report['timeline_preflight']={'handlers':handlers,'simulation_cache_rejections':simulation,'samples':[31,91]}
 obj_before={o.name:o.as_pointer() for o in bpy.data.objects};world_before=worlds()
 parent_before={o.name:o.parent.name if o.parent else None for o in bpy.data.objects}
 visibility={o.name:[o.hide_render,o.hide_viewport,o.hide_get(),sorted(c.name for c in o.users_collection)] for o in bpy.data.objects}
 actions={o.name:(o.animation_data.action.name if o.animation_data and o.animation_data.action else None) for o in bpy.data.objects}
 def action_record(action):
  return {'name':action.name,'curves':[{'path':f.data_path,'index':f.array_index,'mute':f.mute,
   'modifiers':[H['rna_values'](m) for m in f.modifiers],
   'keys':[[*k.co,*k.handle_left,*k.handle_right,k.interpolation,k.easing,k.handle_left_type,k.handle_right_type] for k in f.keyframe_points],
   'samples':[[*k.co] for k in f.sampled_points]} for f in H['curves_of'](action)]}
 action_before={x.name:digest(action_record(x)) for x in bpy.data.actions}
 material_before={m.name:digest({'rna':H['rna_values'](m),'tree':H['node_tree_record'](m.node_tree)}) for m in bpy.data.materials}
 def mesh_record(m):
  v=H['mesh_summary'](m,Matrix.Identity(4))[0]
  for key,seq,prop,width,typ in [('edge_endpoints',m.edges,'vertices',2,np.int32),('loop_edges',m.loops,'edge_index',1,np.int32),
   ('corner_normals',m.corner_normals,'vector',3,np.float32),('vertex_normals',m.vertex_normals,'vector',3,np.float32),('polygon_normals',m.polygon_normals,'vector',3,np.float32),
   ('smooth',m.polygons,'use_smooth',1,np.bool_),('sharp',m.edges,'use_edge_sharp',1,np.bool_),('seam',m.edges,'use_seam',1,np.bool_)]:
   v[key]=H['array_hash'](seq,prop,width,typ)[0]
  v.update(has_custom_normals=m.has_custom_normals,normals_domain=m.normals_domain)
  return v
 def snap(name):
  o=ob(name);e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
  try:return mesh_record(m),H['mesh_summary'](m,e.matrix_world)[1]
  finally:e.to_mesh_clear()
 raw_before={n:mesh_record(ob(n).data) for n in I['geometry_names']}
 baseline={n:snap(n) for n in I['geometry_names']}
 source_samples={};source_spin_samples=[]
 for frame in (31,91):
  bpy.context.scene.frame_set(frame);update();source_samples[frame]={n:matrix(ob(n)).tolist() for n in world_before if n not in scope}
  for s in I['stations']:
   spin=ob(s['spin']);curves=H['curves_of'](spin.animation_data.action)
   assert spin.rotation_mode=='QUATERNION' and len(curves)==3
   assert sorted((f.data_path,f.array_index) for f in curves)==[('rotation_euler',0),('rotation_euler',1),('rotation_euler',2)]
   assert all(not f.mute and not f.modifiers and len(f.keyframe_points)==122 for f in curves)
   requested=[float(next(f for f in curves if f.array_index==j).evaluate(frame)) for j in range(3)]
   basis=np.asarray(spin.matrix_basis);assert np.array_equal(basis,np.eye(4)) and abs(requested[1])>1
   source_spin_samples.append({'station':s['station'],'frame':frame,'mode':spin.rotation_mode,'action':spin.animation_data.action.name,'sampled_euler':requested,'actual_basis_identity':True,'actual_rotation_angle':float(spin.matrix_basis.to_quaternion().angle)})
 bpy.context.scene.frame_set(0);update();assert worlds()==world_before,'Original frame0 did not restore exactly'
 write('source-action-mismatch.json',source_spin_samples)
 new=[];detached=[];fits=L['fits']
 for s,fit in zip(I['stations'],fits):
  assert fit['station']==s['station'] and fit['source_cylinder_dimensions_match'] and fit['kingpin_vertical_axis_qualified']
  joint=bpy.data.objects.new(f"S543_{s['station']}_native_steering_joint_frame",None);bpy.context.scene.collection.objects.link(joint)
  joint.empty_display_type='ARROWS';joint.empty_display_size=.1;joint.matrix_world=Matrix.Translation(Vector(fit['kingpin_centre_m']));reparent(joint,ob(s['upright']))
  joint['candidate_scope']='Neutral steering only; existing kingpin axis. CV and suspension installation are unqualified.';joint.lock_rotation=(True,True,False);new.append(joint.name)
  for key in ('carrier','brake'):
   o=ob(s[key]);ad=o.animation_data;assert ad and ad.action
   action=ad.action;detached.append({'object':o.name,'action':action.name,'old_fake_user':action.use_fake_user,'old_slot_handle':ad.action_slot_handle})
   action.use_fake_user=True;ad.action=None;reparent(o,joint)
  reparent(ob(s['drum']),ob(s['spin']))
  spin=ob(s['spin']);assert np.array_equal(np.asarray(spin.matrix_basis),np.eye(4));spin.rotation_mode='XYZ';update()
 report['constructed_joint_frames']=new;report['detached_retained_actions']=detached;report['spin_modes_changed_to']='XYZ'
 neutral=[];support=[]
 for n in I['geometry_names']:
  sig,xyz=snap(n);old,oldxyz=baseline[n];err=float(np.max(np.linalg.norm(xyz-oldxyz,axis=1)))
  changed=[k for k in old if sig[k]!=old[k]]
  row={'name':n,'max_vertex_error_m':err,'changed_summary_fields':changed}
  assert err<2e-6,(n,err)
  if n in moving_names:assert not changed,(n,changed);neutral.append(row)
  else:
   assert set(changed)<=set(['authored_geometry_uv','uv_layers']),(n,changed)
   row['known_original_uv_repeat_failure_retained']=True;support.append(row)
 report['neutral']={'count':len(neutral),'max_vertex_error_m':max(r['max_vertex_error_m'] for r in neutral),'limit_m':2e-6}
 write('neutral.json',{'moving':neutral,'original_support_differences_not_accepted':support})
 trials=[]
 for s in I['stations']:
  spin=ob(s['spin']);ad=spin.animation_data;act=ad.action;slot=ad.action_slot;slot_handle=ad.action_slot_handle;basis=spin.matrix_basis.copy();euler=spin.rotation_euler.copy();m0=spin.matrix_world.copy()
  moving=[o.name for o in spin.children_recursive if o.type=='MESH'];fixed=[o.name for o in ob(s['brake']).children_recursive if o.type=='MESH']
  before={n:snap(n) for n in moving+fixed};axis=np.asarray((m0.to_3x3()@Vector((0,1,0))).normalized());centre=np.asarray(m0.translation)
  ad.action=None
  try:
   for angle in (.731,math.pi):
    spin.rotation_euler=(0,angle,0);update();d=spin.matrix_world@m0.inverted();actual=float(d.to_quaternion().angle);assert abs(actual-angle)<2e-6
    delta=np.asarray(d);rigid=0.;patherr=0.;brakeerr=0.;witness={}
    for n in moving:
     sig,xyz=snap(n);old,oldxyz=before[n];assert sig==old,n
     predicted=oldxyz@delta[:3,:3].T+delta[:3,3];rigid=max(rigid,float(np.max(np.linalg.norm(xyz-predicted,axis=1))))
     rv=oldxyz-centre;rv-=np.outer(rv@axis,axis);path=np.linalg.norm(xyz-oldxyz,axis=1)
     patherr=max(patherr,float(np.max(np.abs(path-2*np.linalg.norm(rv,axis=1)*abs(math.sin(angle/2))))))
     if n in (s['drum'],s['merged_tyre']):witness[n]=float(path.max())
    for n in fixed:
     sig,xyz=snap(n);old,oldxyz=before[n];assert sig==old,n;brakeerr=max(brakeerr,float(np.max(np.linalg.norm(xyz-oldxyz,axis=1))))
    row={'station':s['station'],'requested_radians':angle,'actual_rotation_radians':actual,'moving_meshes':len(moving),'fixed_meshes':len(fixed),'max_rigid_error_m':rigid,'max_radius_path_error_m':patherr,'max_fixed_brake_error_m':brakeerr,'real_displacement_m':witness}
    trials.append(row);assert rigid<2e-5 and patherr<2e-5 and brakeerr<2e-6,row
    assert len(witness)==2 and min(witness.values())>.001,row
  finally:
   spin.rotation_euler=euler;spin.matrix_basis=basis;ad.action=act;ad.action_slot=slot;update();assert ad.action_slot_handle==slot_handle
  for n in moving+fixed:
   sig,xyz=snap(n);old,oldxyz=before[n];assert sig==old and np.array_equal(xyz,oldxyz),('restore',n)
 write('manual-spin-samples.json',trials);report['manual_samples']=trials
 timeline=[]
 for frame in (31,91):
  bpy.context.scene.frame_set(frame);update()
  assert {n:matrix(ob(n)).tolist() for n in world_before if n not in scope}==source_samples[frame],('outside timeline change',frame)
  for s in I['stations']:
   spin=ob(s['spin']);curves=H['curves_of'](spin.animation_data.action);expected=[float(next(f for f in curves if f.array_index==j).evaluate(frame)) for j in range(3)]
   expected_basis=Matrix.Rotation(expected[1],4,'Y');err=float(np.max(np.abs(np.asarray(spin.matrix_basis)-np.asarray(expected_basis))))
   assert err<2e-6 and abs(spin.rotation_euler.y-expected[1])<2e-6
   timeline.append({'station':s['station'],'frame':frame,'actual_euler_y':spin.rotation_euler.y,'original_fcurve_y':expected[1],'basis_max_element_error':err,'mode':spin.rotation_mode})
 bpy.context.scene.frame_set(0);update();write('native-action-samples.json',timeline);report['native_action_samples']=timeline
 assert {o.name:o.as_pointer() for o in bpy.data.objects if o.name not in new}==obj_before
 assert {n:matrix(ob(n)).tolist() for n in world_before if n not in scope}=={n:world_before[n] for n in world_before if n not in scope}
 assert all(visibility[o.name]==[o.hide_render,o.hide_viewport,o.hide_get(),sorted(c.name for c in o.users_collection)] for o in bpy.data.objects if o.name in visibility)
 expected_parents={s[key] for s in I['stations'] for key in ['carrier','brake','drum']}
 assert {n for n in parent_before if (ob(n).parent.name if ob(n).parent else None)!=parent_before[n]}==expected_parents
 assert {n for n in actions if (ob(n).animation_data.action.name if ob(n).animation_data and ob(n).animation_data.action else None)!=actions[n]}=={r['object'] for r in detached}
 assert {x.name:digest(action_record(x)) for x in bpy.data.actions}==action_before,'Original action keys changed'
 assert {m.name:digest({'rna':H['rna_values'](m),'tree':H['node_tree_record'](m.node_tree)}) for m in bpy.data.materials}==material_before
 for n in I['geometry_names']:assert mesh_record(ob(n).data)==raw_before[n],('raw changed',n)
 for n in moving_names:
  sig,xyz=snap(n);old,oldxyz=baseline[n];assert sig==old and float(np.max(np.linalg.norm(xyz-oldxyz,axis=1)))<2e-6
 assert sha(source.read_bytes())==I['source_sha256']
 report['final_protection']={'original_identity':8518,'outside_neutral_matrices_exact':len(world_before)-len(scope),'parent_edges_changed':12,'retained_action_datablocks':len(action_before),'all_original_action_keys_unchanged':True,'all_materials_unchanged':len(material_before),'raw_meshes_unchanged':len(raw_before),'original_file_unchanged':True}
 report['image_resources']=[{'name':im.name,'source':im.source,'filepath':im.filepath,'packed':bool(im.packed_file or len(im.packed_files))} for im in bpy.data.images]
 unpacked=[r for r in report['image_resources'] if r['source'] in {'FILE','TILED','MOVIE','SEQUENCE'} and not r['packed']]
 assert not unpacked,('Unpacked resources need independent save-path qualification',unpacked)
 persistent={'object_names':sorted(bpy.data.objects.keys()),'world_matrices_sha256':digest(worlds()),'parents_sha256':digest({o.name:o.parent.name if o.parent else None for o in bpy.data.objects}),
  'actions_sha256':digest({x.name:digest(action_record(x)) for x in bpy.data.actions}),
  'raw_geometry':{n:mesh_record(ob(n).data) for n in I['geometry_names']},'moving_evaluated':{n:snap(n)[0] for n in moving_names},'source_sha256':I['source_sha256']}
 write('saved-state-expected.json',persistent)
 dest=out/I['save_filename'];assert not dest.exists() and dest.resolve()!=source.resolve()
 bpy.ops.wm.save_as_mainfile(filepath=str(dest),check_existing=True,relative_remap=False)
 assert dest.is_file() and sha(source.read_bytes())==I['source_sha256']
 report.update(status='SCOPED_NATIVE_BUILD_SAVED_FRESH_OPEN_PENDING',saved_blend=True,saved_bytes=dest.stat().st_size,saved_sha256=sha(dest.read_bytes()),saved_path=str(dest),asset_delivery='LOCAL_ONLY_LFS_BLOCKED')

try:
 main()
except BaseException as exc:
 report.update(status='NATIVE_TRIAL_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
 write('native-report.json',report)
 raise
else:
 write('native-report.json',report);print(report['status'],flush=True)
