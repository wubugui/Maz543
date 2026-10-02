"""Repair retained neutral support/wheel/drum relationships in memory only.

Zero steering and existing zero camber are preserved. No suspension hardpoint,
shaft or CV assumption is changed. The72qualified glyphs receive native
Shrinkwrap Modifier Apply at neutral, while Solidify and original FONT sources
remain editable; neutral evaluated geometry/UV/materials must be preserved. Existing drum geometry is
qualified against the original cylindrical authoring before it follows spin.
"""
import argparse,ast,hashlib,json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',required=True);p.add_argument('--repository',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);base=Path(a.base);out=Path(a.output);repo=Path(a.repository);out.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0'
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert sha(base.read_bytes())==a.sha
AUTHORING_SHA256='d1fdc631ff369ab4f7af1c85e828bbd3d053ff35a2ec5291d0d475bbc68f7059'
assert sha((repo/'testcar/lib/maz543.ts').read_bytes())==AUTHORING_SHA256, 'Drum authoring evidence changed'
bpy.ops.wm.open_mainfile(filepath=str(base));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
assert bpy.context.scene.frame_current==0 and bpy.context.scene.frame_subframe==0
assert bpy.context.evaluated_depsgraph_get().mode=='VIEWPORT'
def update():bpy.context.view_layer.update()
def ob(n):return bpy.data.objects[n]
def points(o,appearance=False):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:
  v=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',v);v=v.reshape(-1,3);w=np.asarray(e.matrix_world,dtype=np.float64);m.calc_loop_triangles();tri=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',tri)
  if appearance:
   uv=[]
   for layer in m.uv_layers:
    values=np.empty(len(layer.data)*2,dtype=np.float32);layer.data.foreach_get('uv',values);uv.append({'name':layer.name,'loops':len(layer.data),'sha256':sha(values.tobytes()),'active_render':layer.active_render})
   material_indices=np.empty(len(m.polygons),dtype=np.int32);m.polygons.foreach_get('material_index',material_indices)
   signature={'uv':uv,'active_uv':m.uv_layers.active.name if m.uv_layers.active else None,'evaluated_materials':[x.name if x else None for x in m.materials],'object_material_slots':[(slot.link,slot.material.name if slot.material else None) for slot in o.material_slots],'polygon_material_index_sha256':sha(material_indices.tobytes())}
   return v@w[:3,:3].T+w[:3,3],tri,signature
  return v@w[:3,:3].T+w[:3,3],tri
 finally:e.to_mesh_clear()
def geometry_axis(o,u):
 xyz,_=points(o);v,V=np.linalg.eigh(np.cov(xyz-xyz.mean(axis=0),rowvar=False));k=max(range(3),key=lambda j:abs(np.dot(V[:,j],u)));axis=V[:,k];axis*=1 if axis@u>=0 else -1;return xyz.mean(axis=0),axis,v
def reparent(o,parent):
 m=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_world=m;update()

# Reuse the pinned production audit's structural transform rejection, including
# non-object parenting, physical simulation, armatures and linked-library inputs.
guard_path=repo/'testcar/scripts/audit-candidate-cab-static-dependencies.py';guard_source=guard_path.read_bytes();assert sha(guard_source)=='0ca53737b57995ca86bc01612f60175e36cf2199d04edd55017f94ab1c9e1a51'
node=next(n for n in ast.parse(guard_source).body if isinstance(n,ast.FunctionDef) and n.name=='structural_transform_issues');ctx={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard_path),'exec'),ctx)
roots=[];scope=set();station=[]
for i in range(4):
 carrier=ob(f'wheels_pivot_{1+7*i:03d}');spin=ob(f'wheels_pivot_{2+7*i:03d}');brake=ob(f'brakes_pivot_{1+i:03d}');upr=ob(f'S543_{i}_upright');king=ob(f'S543_{i}_steering_kingpin')
 assert spin.parent==carrier and carrier.parent==ob('wheels') and brake.parent==ob('brakes') and king.parent==upr
 for o in (carrier,brake):roots.append(o);scope.add(o);scope.update(o.children_recursive)
 station.append((i,carrier,spin,brake,upr,king))
ancestors=set()
for o in [*scope,*[s[4] for s in station]]:
 q=o.parent
 while q:ancestors.add(q);q=q.parent
eligibility=[];issues=[];observed_actions=[];shrink=[]
for o in sorted(scope|ancestors|{s[5] for s in station},key=lambda o:o.name):
 local=ctx['structural_transform_issues'](o)
 if o.constraints:local.append(o.name+': constraints are not qualified')
 if o.instance_type!='NONE':local.append(o.name+': instancing is not qualified')
 if o.animation_data:
  ad=o.animation_data
  if ad.drivers or ad.nla_tracks:local.append(o.name+': driver or NLA dependency is not qualified')
  if ad.action:observed_actions.append({'object':o.name,'action':ad.action.name,'frame':0,'scope':'Evaluated at frame0 and held; no timeline equivalence claim'})
 if o.data:
  if getattr(o.data,'animation_data',None):local.append(o.name+': geometry data animation')
  if getattr(o.data,'shape_keys',None):local.append(o.name+': keyed geometry')
  for prop in o.data.bl_rna.properties:
   if prop.type=='POINTER' and isinstance(getattr(o.data,prop.identifier,None),bpy.types.Object):local.append(o.name+': geometry Object pointer '+prop.identifier)
 for m in o.modifiers:
  if not m.show_viewport:continue
  if m.type in {'BEVEL','SOLIDIFY','WEIGHTED_NORMAL'}:
   for prop in m.bl_rna.properties:
    if prop.type=='POINTER' and isinstance(getattr(m,prop.identifier,None),bpy.types.Object):local.append(o.name+': intrinsic modifier Object pointer '+prop.identifier)
  elif m.type=='SHRINKWRAP':
   # Exact tyre lettering profile only. Target and lettering share the same
   # spin frame, so each sampled spin moves both through the same rigid map.
   i=o.get('tyreIndex');target=ob(f'BL_Tyre_{i}_VI203_profile') if isinstance(i,int) and 0<=i<4 else None
   valid=target is not None and o.name.startswith(f'BL_Tyre_{i}_emboss_') and m.name=='Conform legend to actual sidewall' and m.target==target and m.auxiliary_target is None and o.parent==target.parent==ob(f'wheels_pivot_{2+7*i:03d}') and m.wrap_method=='NEAREST_SURFACEPOINT' and m.wrap_mode=='ON_SURFACE' and abs(m.offset+.00005)<1e-10 and not m.vertex_group
   if not valid:local.append(o.name+': unqualified Shrinkwrap profile')
   shrink.append({'object':o.name,'target':m.target.name if m.target else None,'qualified_exact_profile':valid,'common_spin':o.parent.name if o.parent else None})
  else:local.append(o.name+': active modifier not supported '+m.type)
 eligibility.append({'object':o.name,'issues':local});issues.extend(local)
assert len(shrink)==72 and not issues,issues

# Reject observed reverse dependencies beyond the moved complete subtrees.
# Node/collection/data references are checked conservatively; unreadable RNA is
# an error, not ignored. This remains a bounded structural audit, not a proof of
# all possible Blender internals or renderer-material displacement.
reverse=[]
def target_in_scope(v):
 return isinstance(v,bpy.types.Object) and v in scope or isinstance(v,bpy.types.Collection) and any(o in scope for o in v.all_objects)
def check_id(block,owner,label):
 if block is None:return
 for prop in block.bl_rna.properties:
  if prop.type=='POINTER' and prop.identifier not in {'rna_type','id_data','original'}:
   v=getattr(block,prop.identifier)
   if target_in_scope(v) and owner not in scope:reverse.append([owner.name,label,prop.identifier,v.name])
def check_drivers(block,owner,label):
 ad=getattr(block,'animation_data',None)
 if ad:
  for f in ad.drivers:
   for var in f.driver.variables:
    for t in var.targets:
     if target_in_scope(t.id) and owner not in scope:reverse.append([owner.name,label,f.data_path,t.id.name])
def check_tree(tree,owner,seen):
 if tree is None or tree.as_pointer() in seen:return
 seen.add(tree.as_pointer())
 for node in tree.nodes:
  check_id(node,owner,'node')
  for socket in node.inputs:
   if hasattr(socket,'default_value') and target_in_scope(socket.default_value) and owner not in scope:reverse.append([owner.name,tree.name,node.name,socket.name])
  if hasattr(node,'node_tree'):check_tree(node.node_tree,owner,seen)
for o in bpy.data.objects:
 check_drivers(o,o,'object');check_drivers(o.data,o,'data')
 if o.data and getattr(o.data,'shape_keys',None):check_drivers(o.data.shape_keys,o,'shape_keys')
 if o.instance_collection and target_in_scope(o.instance_collection) and o not in scope:reverse.append([o.name,'instance_collection',o.instance_collection.name])
 check_id(o.data,o,'data');check_id(o.rigid_body_constraint,o,'rigid_body_constraint')
 for item in [*o.constraints,*o.modifiers]:
  check_id(item,o,item.name)
  if item.type=='NODES':check_tree(item.node_group,o,set())
assert not reverse,reverse

geoms=[o for o in scope if o.type in {'MESH','CURVE','FONT'}];assert len(geoms)==776,len(geoms);baseline={o.name:points(o,True) for o in geoms};outside={o.name:o.matrix_world.copy() for o in bpy.data.objects if o not in scope};rows=[];detached=[];new=[]
# Apply only the exact qualified front-tyre fit operation. Retain native
# Solidify thickness editing and every glyph; original FONT sources stay intact.
def glyph_source_signature(o):
 return {'type':o.type,'data_name':o.data.name,'body':o.data.body,'font':o.data.font.name,'size':o.data.size,'extrude':o.data.extrude,'bevel_depth':o.data.bevel_depth,'world':[list(x) for x in o.matrix_world],'visibility':[o.hide_render,o.hide_viewport,o.hide_get()]}
def raw_mesh_signature(data):
 v=np.empty(len(data.vertices)*3,dtype=np.float32);data.vertices.foreach_get('co',v);idx=np.empty(len(data.loops),dtype=np.int32);data.loops.foreach_get('vertex_index',idx)
 uv=[]
 for layer in data.uv_layers:
  values=np.empty(len(layer.data)*2,dtype=np.float32);layer.data.foreach_get('uv',values);uv.append((layer.name,sha(values.tobytes())))
 return {'vertices':sha(v.tobytes()),'loop_vertex_indices':sha(idx.tobytes()),'uv':uv,'materials':[m.name if m else None for m in data.materials]}
qualified_glyphs=[ob(row['object']) for row in shrink];assert len(qualified_glyphs)==72
qualified_glyph_names={o.name for o in qualified_glyphs}
source_fonts={};glyph_sharing_before={};sharing_peer_signatures={};glyph_visibility={}
for obj in qualified_glyphs:
 source_font=ob('SOURCE_'+obj.name);assert source_font.type=='FONT';source_fonts[source_font.name]=glyph_source_signature(source_font)
 glyph_visibility[obj.name]=(obj.hide_render,obj.hide_viewport,obj.hide_get())
 peers=sorted(o.name for o in bpy.data.objects if o.data==obj.data);glyph_sharing_before[obj.name]={'mesh':obj.data.name,'users':obj.data.users,'object_users':peers}
 for name in peers:
  if name not in qualified_glyph_names:sharing_peer_signatures[name]=raw_mesh_signature(ob(name).data)
selected_before=[o for o in bpy.context.selected_objects];active_before=bpy.context.view_layer.objects.active
apply_records=[];assert bpy.context.mode=='OBJECT'
apply_exception=None
try:
 for selected in selected_before:selected.select_set(False)
 for count,obj in enumerate(qualified_glyphs,1):
  m=next(m for m in obj.modifiers if m.type=='SHRINKWRAP');assert m.name=='Conform legend to actual sidewall'
  solid=next(m for m in obj.modifiers if m.type=='SOLIDIFY');solid_settings={'name':solid.name,'thickness':solid.thickness,'offset':solid.offset,'use_even_offset':solid.use_even_offset,'show_viewport':solid.show_viewport,'show_render':solid.show_render}
  users_before_optional_copy=obj.data.users;single_user=users_before_optional_copy>1
  if single_user:obj.data=obj.data.copy()
  users_at_apply=obj.data.users
  obj.select_set(True);bpy.context.view_layer.objects.active=obj
  returned=bpy.ops.object.modifier_apply(modifier=m.name);assert returned=={'FINISHED'},(obj.name,returned)
  obj.select_set(False);update()
  remaining=[mod.type for mod in obj.modifiers];assert remaining==['SOLIDIFY'],(obj.name,remaining)
  solid=obj.modifiers[0];assert solid_settings=={'name':solid.name,'thickness':solid.thickness,'offset':solid.offset,'use_even_offset':solid.use_even_offset,'show_viewport':solid.show_viewport,'show_render':solid.show_render}
  assert glyph_visibility[obj.name]==(obj.hide_render,obj.hide_viewport,obj.hide_get())
  apply_records.append({'object':obj.name,'operator':'bpy.ops.object.modifier_apply','applied_modifier':'Conform legend to actual sidewall','returned':sorted(returned),'original_mesh_sharing':glyph_sharing_before[obj.name],'made_single_user_copy':single_user,'mesh_users_before_optional_copy':users_before_optional_copy,'mesh_users_at_apply':users_at_apply,'result_object_users':sorted(o.name for o in bpy.data.objects if o.data==obj.data),'result_mesh':obj.data.name,'remaining_modifiers':remaining,'preserved_solidify':solid_settings})
  if count%18==0:print('APPLIED_NATIVE_TYRE_FITS',count,flush=True)
except Exception as exc:
 apply_exception=exc
finally:
 for glyph in qualified_glyphs:glyph.select_set(False)
 for selected in selected_before:selected.select_set(True)
 bpy.context.view_layer.objects.active=active_before
font_failures=[name for name,sig in source_fonts.items() if glyph_source_signature(ob(name))!=sig]
peer_failures=[name for name,sig in sharing_peer_signatures.items() if raw_mesh_signature(ob(name).data)!=sig]
construction={'status':'FAILED_NATIVE_FIT_CONSTRUCTION' if apply_exception or font_failures or peer_failures else 'NATIVE_SHRINKWRAP_APPLY_CONSTRUCTION_ONLY','applied':apply_records,'source_fonts_checked':len(source_fonts),'source_font_failures':font_failures,'sharing_peer_objects_checked':len(sharing_peer_signatures),'sharing_peer_failures':peer_failures,'operator_error':None if apply_exception is None else type(apply_exception).__name__+': '+str(apply_exception),'source_sha256':a.sha,'saved_blend':False}
(out/'construction.json').write_text(json.dumps(construction,indent=2)+'\n')
if apply_exception is not None:raise apply_exception
assert len(apply_records)==72 and not font_failures and not peer_failures
for i,carrier,spin,brake,upr,king in station:
 # The cylinder source authoring is testcar/lib/maz543.ts: cylinder(brake,.335,
 # .13,...) followed by two shoes and actuator. Fit actual circular end rings.
 drum=ob(f'brakes_{3+4*i:04d}');assert drum.parent==brake and drum.type=='MESH' and not drum.modifiers and len(drum.data.vertices)==148
 def fit_drum():
  xyz,_=points(drum);m=np.array(spin.matrix_world.inverted(),dtype=float);local=xyz@m[:3,:3].T+m[:3,3];r=np.linalg.norm(local[:,[0,2]],axis=1);sel=r>r.max()*.99;xy=local[sel][:,[0,2]];A=np.c_[2*xy[:,0],2*xy[:,1],np.ones(len(xy))];b=(xy*xy).sum(axis=1);cx,cz,k=np.linalg.lstsq(A,b,rcond=None)[0];rad=math.sqrt(k+cx*cx+cz*cz);err=np.max(np.abs(np.linalg.norm(xy-[cx,cz],axis=1)-rad));axrange=[float(local[:,1].min()),float(local[:,1].max())]
  return {'circle_centre_spin_xz_m':[float(cx),float(cz)],'fitted_radius_m':rad,'radial_max_residual_m':float(err),'axis_span_m':axrange,'ring_vertices':int(sel.sum()),'source_correspondence':'Original cylinder(brake,.335,.13) then two torus shoes and actuator in testcar/lib/maz543.ts; actual neutral envelope, radius, axial width and radial residual agree'}
 drum_fit=fit_drum();assert np.linalg.norm(drum_fit['circle_centre_spin_xz_m'])<2e-6 and abs(drum_fit['fitted_radius_m']-.335)<2e-6 and abs(drum_fit['axis_span_m'][1]-drum_fit['axis_span_m'][0]-.13)<2e-6 and drum_fit['radial_max_residual_m']<2e-6,drum_fit
 kp,ka,kv=geometry_axis(king,np.array((0,0,1.)));assert ka[2]>.999999 and kv[2]>20*kv[1]
 control=bpy.data.objects.new(f'S543_{i}_native_steering_joint_frame',None);bpy.context.scene.collection.objects.link(control);control.empty_display_type='ARROWS';control.empty_display_size=.1;control.matrix_world=Matrix.Translation(Vector(kp));reparent(control,upr);new.append(control.name)
 control['joint_scope']='Existing native kingpin cylinder axis; neutral only. Source trunnions/bearings and internal CV are not reconstructed by this control.'
 control['steering_state']='Neutral only; rotate the native local Z control only after steering/CV qualification'
 control.lock_rotation=(True,True,False)
 for o in (carrier,brake):
  assert o.animation_data and o.animation_data.action
  detached.append({'object':o.name,'action':o.animation_data.action.name});o.animation_data.action=None;reparent(o,control)
 reparent(drum,spin);update()
 rows.append({'station':i,'joint_frame':control.name,'native_kingpin_centre_m':kp.tolist(),'native_kingpin_axis':ka.tolist(),'drum':drum.name,'drum_fit':drum_fit,'spin':spin.name,'stationary_brake':brake.name})

neutral=[];neutral_failures=[]
for o in geoms:
 v,t,appearance_after=points(o,True);old,ot,appearance_before=baseline[o.name];topology=v.shape==old.shape and np.array_equal(t,ot);appearance_equal=appearance_after==appearance_before
 error=float(np.max(np.linalg.norm(v-old,axis=1))) if v.shape==old.shape and len(v) else None
 row={'name':o.name,'vertices_before':len(old),'vertices_after':len(v),'triangle_indices_equal':topology,'max_position_error_m':error,'evaluated_uv_material_sha256_before':sha(json.dumps(appearance_before,sort_keys=True).encode()),'evaluated_uv_material_sha256_after':sha(json.dumps(appearance_after,sort_keys=True).encode()),'uv_material_exactly_equal':appearance_equal}
 if not topology or not appearance_equal or error is None or error>=2e-6:
  neutral_failures.append(o.name)
  if not appearance_equal:row.update(appearance_before=appearance_before,appearance_after=appearance_after)
 neutral.append(row)
neutral_max=max((r['max_position_error_m'] for r in neutral if r['max_position_error_m'] is not None),default=0.)
(out/'neutral.json').write_text(json.dumps({'status':'FAIL' if neutral_failures else 'SCOPED_NEUTRAL_GEOMETRY_UV_MATERIAL_PASS','objects':neutral,'failures':neutral_failures,'max_vertex_error_m':neutral_max,'limit_m':2e-6},indent=2)+'\n')
assert not neutral_failures,neutral_failures
spin_trials=[];negative_controls=[];restorations=[]
for i,carrier,spin,brake,upr,king in station:
 original_action=spin.animation_data.action;spin.animation_data.action=None;basis=spin.matrix_basis.copy();m0=spin.matrix_world.copy();moving=[o for o in spin.children_recursive if o.type in {'MESH','CURVE','FONT'}];snap={o.name:points(o) for o in moving};brake_geoms=[o for o in brake.children_recursive if o.type in {'MESH','CURVE','FONT'}];fixed={o.name:points(o) for o in brake_geoms}
 sample_exception=None;cleanup_exception=None;old_euler=spin.rotation_euler.copy()
 try:
  # Reproduce and explicitly reject the old Euler-in-Quaternion no-motion path.
  assert spin.rotation_mode=='QUATERNION';spin.rotation_euler.y=.731;update();negative_matrix_error=max(abs(spin.matrix_world[r][c]-m0[r][c]) for r in range(4) for c in range(4));negative_vertex_error=0.
  for name in [rows[i]['drum'],f'BL_Tyre_{i}_VI203_profile']:
   v,_=points(ob(name));negative_vertex_error=max(negative_vertex_error,float(np.max(np.linalg.norm(v-snap[name][0],axis=1))))
  assert negative_matrix_error==0. and negative_vertex_error==0.
  negative_controls.append({'station':i,'attempted_euler_y_radians':.731,'rotation_mode':spin.rotation_mode,'world_matrix_delta':negative_matrix_error,'drum_and_tyre_vertex_delta_m':negative_vertex_error,'rejected_as_motion_trial':True})
  spin.rotation_euler=old_euler;spin.matrix_basis=basis;update()
  axis=np.asarray((m0.to_3x3()@Vector((0,1,0))).normalized(),dtype=float);centre0=np.asarray(m0.translation,dtype=float)
  for angle in [.731,math.pi]:
   spin.matrix_basis=basis@Matrix.Rotation(angle,4,'Y');update();actual_delta=spin.matrix_world@m0.inverted();observed_angle=actual_delta.to_quaternion().angle;assert abs(observed_angle-angle)<2e-6,(i,angle,observed_angle);delta=np.asarray(actual_delta,dtype=np.float64);assert np.linalg.norm(delta[:3,:3]-np.eye(3))>.1;maxerror=0.0;trajectory_error=0.;vertex_count=0;motion={};sample_objects=[]
   for o in moving:
    now,t=points(o);old,ot=snap[o.name];assert now.shape==old.shape and np.array_equal(t,ot),o.name;expected=old@delta[:3,:3].T+delta[:3,3];maxerror=max(maxerror,float(np.max(np.linalg.norm(now-expected,axis=1))) if len(now) else 0.);vertex_count+=len(now)
    radius_vector=old-centre0;radius_vector-=np.outer(radius_vector@axis,axis);radius=np.linalg.norm(radius_vector,axis=1);observed_path=np.linalg.norm(now-old,axis=1);expected_path=2*radius*abs(math.sin(angle/2));trajectory_error=max(trajectory_error,float(np.max(np.abs(observed_path-expected_path))) if len(now) else 0.)
    sample_objects.append({'name':o.name,'max_rigid_vertex_error_m':float(np.max(np.linalg.norm(now-expected,axis=1))) if len(now) else 0.,'max_radius_trajectory_error_m':float(np.max(np.abs(observed_path-expected_path))) if len(now) else 0.,'max_actual_displacement_m':float(np.max(observed_path)) if len(now) else 0.})
    if o.name in [rows[i]['drum'],f'BL_Tyre_{i}_VI203_profile']:motion[o.name]={'max_observed_displacement_m':float(np.max(observed_path)),'max_expected_radius_trajectory_m':float(np.max(expected_path))}
   fixederror=0.
   for o in brake_geoms:
    now,t=points(o);old,ot=fixed[o.name];assert now.shape==old.shape and np.array_equal(t,ot);fixederror=max(fixederror,float(np.max(np.linalg.norm(now-old,axis=1))))
   (out/f'spin-{i}-{angle:.6f}.json').write_text(json.dumps({'station':i,'angle':angle,'observed_angle':observed_angle,'objects':sample_objects,'fixed_brake_error_m':fixederror,'limit_m':2e-5,'fixed_limit_m':2e-6},indent=2)+'\n')
   assert maxerror<2e-5 and trajectory_error<2e-5 and fixederror<2e-6,(i,angle,maxerror,trajectory_error,fixederror)
   assert len(motion)==2 and all(r['max_observed_displacement_m']>.001 for r in motion.values()),motion
   # Measured circular axis at every sampled spin, using the native current frame.
   drum=ob(rows[i]['drum']);xyz,_=points(drum);drum_motion=float(np.max(np.linalg.norm(xyz-snap[drum.name][0],axis=1)));assert drum_motion>.001,(i,angle,drum_motion);inv=np.asarray(spin.matrix_world.inverted(),dtype=float);local=xyz@inv[:3,:3].T+inv[:3,3];rad=np.linalg.norm(local[:,[0,2]],axis=1);xy=local[rad>rad.max()*.99][:,[0,2]];q=np.linalg.lstsq(np.c_[2*xy,np.ones(len(xy))],(xy*xy).sum(axis=1),rcond=None)[0];centre_offset=float(np.linalg.norm(q[:2]));assert centre_offset<2e-6
   spin_trials.append({'station':i,'requested_radians':angle,'observed_world_rotation_radians':observed_angle,'original_rotation_mode':spin.rotation_mode,'drum_max_vertex_displacement_m':drum_motion,'drum_and_tyre_radius_trajectory':motion,'all_spin_vertex_max_radius_trajectory_error_m':trajectory_error,'spin_geometry_objects':len(moving),'vertices':vertex_count,'max_rigid_vertex_error_m':maxerror,'stationary_brake_geometry_objects':len(brake_geoms),'stationary_brake_max_vertex_error_m':fixederror,'drum_circular_axis_to_spin_axis_m':centre_offset})
 except Exception as exc:
  sample_exception=exc
 finally:
  try:spin.rotation_euler=old_euler;spin.matrix_basis=basis;spin.animation_data.action=original_action;update()
  except Exception as exc:cleanup_exception=exc
 restore_error=0.;restore_failures=[]
 for o in moving:
  try:
   v,t=points(o);old,ot=snap[o.name]
   if v.shape!=old.shape or not np.array_equal(t,ot):restore_failures.append({'object':o.name,'error':'restored topology differs'})
   else:restore_error=max(restore_error,float(np.max(np.linalg.norm(v-old,axis=1))) if len(v) else 0.)
  except Exception as exc:restore_failures.append({'object':o.name,'error':type(exc).__name__+': '+str(exc)})
 restored_matrix_error=max(abs(spin.matrix_world[r][c]-m0[r][c]) for r in range(4) for c in range(4));action_restored=spin.animation_data.action==original_action;euler_restored=tuple(spin.rotation_euler)==tuple(old_euler)
 if cleanup_exception is not None:restore_failures.append({'error':type(cleanup_exception).__name__+': '+str(cleanup_exception)})
 if restore_error>=2e-6 or restored_matrix_error>=1e-9 or not action_restored or not euler_restored:restore_failures.append({'error':'restored pose exceeded a fixed gate or action/Euler state differed'})
 restorations.append({'station':i,'geometry_objects':len(moving),'max_vertex_error_m':restore_error,'world_matrix_error':restored_matrix_error,'original_action_restored':action_restored,'original_euler_restored':euler_restored,'rotation_mode':spin.rotation_mode,'restoration_failures':restore_failures,'prior_sample_error':None if sample_exception is None else type(sample_exception).__name__+': '+str(sample_exception)})
 (out/f'restoration-{i}.json').write_text(json.dumps(restorations[-1],indent=2)+'\n')
 if restore_failures:raise AssertionError(('Restoration evidence saved',restore_failures)) from sample_exception
 if sample_exception is not None:raise sample_exception
outside_changed=[]
for name,m in outside.items():
 if max(abs(ob(name).matrix_world[r][c]-m[r][c]) for r in range(4) for c in range(4))>1e-9:outside_changed.append(name)
assert not outside_changed,outside_changed
assert sha(base.read_bytes())==a.sha
result={'status':'NATIVE_PARENT_DRUM_AND_APPLIED_TYRE_FIT_SCOPED_PASS','source_sha256':a.sha,'source_sha256_after':sha(base.read_bytes()),'saved_blend':False,'version':bpy.app.version_string,'build':bpy.app.build_hash.decode(),'autoexec':False,'rows':rows,'detached_original_actions_preserved':detached,'retained_actions_held_at_frame0':observed_actions,'new_native_joint_frames':new,'input_shrinkwrap_profiles_qualified':shrink,'input_eligibility_object_count':len(eligibility),'neutral_geometry':neutral,'neutral_max_vertex_error_m':max(r['max_position_error_m'] for r in neutral),'spin_trials':spin_trials,'outside_original_world_matrices_checked':len(outside),'outside_world_changes':outside_changed,'structural_guard_sha256':sha(guard_source),'source_authoring_sha256':sha((repo/'testcar/lib/maz543.ts').read_bytes()),'limits':['Camber remains approximately0 degrees and the nominal1degree defect is not fixed. No sign, load, tyre-pressure or ride-height qualification.','No halfshaft/Cardan flange was transformed; its support bearing and internal CV interface remain unresolved.','Added neutral steering joint frames remain unturned. No turn-angle, tie-rod, CV, interactive control or steering-travel claim.','Parenting and drum spin are verified at retained frame0 and two spin samples; full original timeline behavior and browser parity are unverified.','The72front glyphs use native Shrinkwrap Modifier Apply at neutral; Solidify, source FONT objects, evaluated neutral vertices/triangles and UV/material signatures are retained. No manual vertex/face construction occurred.','No complete collision, bearing-seat/contact or force certificate.','No blend or GLB saved or production promoted.'],'all16VehicleGates':'OPEN'}
result['limits'].append('The retained drum is the simplified cylinder proxy identified by the original authoring and actual circular sections; no real drum wall, bore, hub-centering land or bearing seat was created or certified.')
result['old_euler_path_negative_controls']=negative_controls;result['spin_pose_restorations']=restorations
result['native_shrinkwrap_apply']=apply_records;result['preserved_source_fonts']=source_fonts;result['sharing_peer_signatures_preserved']=sorted(sharing_peer_signatures)
result['limits'].append('EXPORT INCOMPATIBILITY: testcar/scripts/export-va180-cab-candidate.py excludes the S543_SUSPENSION ancestor branch. This native candidate reparents front wheel/brake objects below uprights in that branch; reusing that exporter unchanged could omit them. Exporter adaptation and browser parity are explicitly not performed here; do not export or promote this candidate through the old selection rule.')
result['limits'].append('The separate plus-one-degree no-closure result applies only to inherited fixed reconstructed hardpoints, rigid arm lengths and zero wheel-axis offset relative to the upright. It neither proves a factory impossibility nor justifies changing an arm length or fixed inner axis; source-resolved knuckle/spindle/trunnion/CV relationships remain necessary.')
out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'neutral_max_vertex_error_m':result['neutral_max_vertex_error_m'],'spin_trials':len(spin_trials)}),flush=True)
