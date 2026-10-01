"""Pinned MAZ native barrel-axis controls, no auto-executed Python required.

Run with official Blender 4.5.13 --background --factory-startup --disable-autoexec
--threads 1 --python-exit-code 17 --python THIS -- --testcar-root PATH --out PATH
--mode trial|build|verify [--candidate PATH].  Trial never saves. Build saves once,
only after all in-memory gates pass; verify freshly opens the one saved candidate.

Original four EMPTYs, quaternion mode, hierarchy, mesh fields and closed world
geometry remain intact. Model-derived fitted axes are NOT factory hinge data.
"""
import argparse, copy, hashlib, json, math, sys, traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix

SOURCE_SHA='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
INPUTS={
 'axis':('work/cloud-door-barrel-axis-20261001/axis-report.json','523f0a0936a30042411db574a9a507b505bd0b5b85770d39f6618095895dcd27'),
 'trial':('work/cloud-door-barrel-motion-trial-20261001/trial-report.json','ce03060e60a7cb0749c18452bb623311383a896b6923ec5941724d3387bc4dd9'),
 'scope':('work/cloud-cab-door-dependencies-20261001/inventory.json','40e771f244ef6a49f90699f3e60c0e01c6a7885baaea77852fac7d75c891a570')}
SPECS=[('cab_pivot_002',-1,0),('cab_pivot_003',-1,1),('cab_pivot_006',1,0),('cab_pivot_007',1,1)]
PROP='open_angle_deg'; META='maz_native_axis_control_v1'; TOL=2e-5
I4=np.eye(4); I3=np.eye(3)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def require(test,message):
 if not test:raise ValueError(message)

def as_plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'id_type':v.bl_rna.identifier,'name':v.name_full}
 if hasattr(v,'to_dict'):return {k:as_plain(x) for k,x in v.to_dict().items()}
 try:return [as_plain(x) for x in v]
 except TypeError:raise ValueError('Unsupported stored value '+str(type(v)))

def scalar_rna(o):
 return {p.identifier:as_plain(getattr(o,p.identifier)) for p in o.bl_rna.properties
  if p.identifier!='rna_type' and p.type in {'BOOLEAN','INT','FLOAT','STRING','ENUM'} and not p.is_readonly}

def authored(o):
 return {k:as_plain(getattr(o,k)) for k in ['location','rotation_mode','rotation_euler',
  'rotation_quaternion','rotation_axis_angle','scale','delta_location','delta_rotation_euler',
  'delta_rotation_quaternion','delta_scale','matrix_basis','matrix_parent_inverse','matrix_world']}

def object_state(o):
 return {'transform':authored(o),'type':o.type,'parent':o.parent.name if o.parent else None,
 'parent_type':o.parent_type,'parent_bone':o.parent_bone,'data':o.data.name if o.data else None,
 'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_get':o.hide_get(),
 'collections':sorted(c.name for c in o.users_collection),'custom':{k:as_plain(o[k]) for k in o.keys()},
 'constraints':[(c.type,scalar_rna(c)) for c in o.constraints],
 'modifiers':[(m.name,m.type,scalar_rna(m),[(p.identifier,as_plain(getattr(m,p.identifier))) for p in m.bl_rna.properties if p.type=='POINTER' and isinstance(getattr(m,p.identifier),bpy.types.ID)]) for m in o.modifiers]}

def array(collection,field,width,dtype):
 a=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(field,a)
 return a.reshape(-1,width) if width>1 else a

def mesh_signature(m):
 """Stored topology/coordinates, flags, all native attribute payloads, UVs,
 materials, deform weights and shape keys. Runtime caches/normals are excluded;
 custom split-normal storage is covered by attributes. Field inventory is explicit.
 """
 h=hashlib.sha256(); inventory=[]
 def feed(label,value):h.update(label.encode()+b'\0');h.update(value if isinstance(value,bytes) else json.dumps(value,sort_keys=True,allow_nan=False).encode());inventory.append(label)
 for label,c,f,w,t in [
  ('vertices.co',m.vertices,'co',3,np.float32),('vertices.select',m.vertices,'select',1,np.bool_),('vertices.hide',m.vertices,'hide',1,np.bool_),
  ('edges.vertices',m.edges,'vertices',2,np.int32),('edges.select',m.edges,'select',1,np.bool_),('edges.hide',m.edges,'hide',1,np.bool_),('edges.seam',m.edges,'use_seam',1,np.bool_),('edges.sharp',m.edges,'use_edge_sharp',1,np.bool_),
  ('loops.vertex_index',m.loops,'vertex_index',1,np.int32),('loops.edge_index',m.loops,'edge_index',1,np.int32),
  ('polygons.loop_start',m.polygons,'loop_start',1,np.int32),('polygons.loop_total',m.polygons,'loop_total',1,np.int32),('polygons.material_index',m.polygons,'material_index',1,np.int32),('polygons.use_smooth',m.polygons,'use_smooth',1,np.bool_),('polygons.select',m.polygons,'select',1,np.bool_),('polygons.hide',m.polygons,'hide',1,np.bool_)]:feed(label,array(c,f,w,t).tobytes())
 feed('mesh.scalar_rna',scalar_rna(m));feed('mesh.custom',{k:as_plain(m[k]) for k in m.keys()});feed('materials',[as_plain(x) for x in m.materials])
 feed('attribute_order',[(a.name,a.domain,a.data_type) for a in m.attributes])
 for a in m.attributes:
  feed('attribute:'+a.name+':scalars',scalar_rna(a))
  if not len(a.data):continue
  for p in a.data[0].bl_rna.properties:
   if p.identifier=='rna_type':continue
   require(p.type in {'BOOLEAN','INT','FLOAT','STRING'},'Unsupported mesh attribute RNA '+a.name+'/'+p.identifier)
   if p.type=='STRING':feed('attribute:'+a.name+':'+p.identifier,[getattr(x,p.identifier) for x in a.data]);continue
   dt={'BOOLEAN':np.bool_,'INT':np.int32,'FLOAT':np.float32}[p.type]
   feed('attribute:'+a.name+':'+p.identifier,array(a.data,p.identifier,p.array_length or 1,dt).tobytes())
 feed('uv_layer_state',[(u.name,scalar_rna(u)) for u in m.uv_layers]);feed('uv_active_index',m.uv_layers.active_index)
 # UV payloads are also attributes; this is an independent read of corner UVs.
 for u in m.uv_layers:feed('uv:'+u.name,array(u.data,'uv',2,np.float32).tobytes())
 # This baseline has no deform groups, but reject instead of ignoring them.
 require(all(not v.groups for v in m.vertices),'Unsupported deform weights on '+m.name)
 require(m.shape_keys is None,'Unsupported shape keys on '+m.name)
 return {'sha256':h.hexdigest(),'fields':inventory,'counts':[len(m.vertices),len(m.edges),len(m.loops),len(m.polygons)]}

def snapshot(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh()
 try:
  v=array(m.vertices,'co',3,np.float64);w=np.asarray(e.matrix_world,dtype=np.float64);m.calc_loop_triangles()
  return (v@w[:3,:3].T+w[:3,3],array(m.loop_triangles,'vertices',3,np.int32),w.copy())
 finally:e.to_mesh_clear()

def exact_snapshot(a,b):return all(np.array_equal(x,y) for x,y in zip(a,b))

def driver_description(fc):
 d=fc.driver
 return {'data_path':fc.data_path,'array_index':fc.array_index,'mute':fc.mute,'lock':fc.lock,'is_valid':fc.is_valid,
 'driver_type':d.type,'expression':d.expression,'use_self':d.use_self,'is_valid_driver':d.is_valid,
 'simple':d.is_simple_expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':as_plain(t.id),'id_type':t.id_type,'data_path':t.data_path,'bone_target':t.bone_target,'transform_type':t.transform_type,'transform_space':t.transform_space,'use_fallback_value':t.use_fallback_value,'fallback_value':t.fallback_value} for t in v.targets]} for v in d.variables],
 'modifiers':[(m.type,scalar_rna(m)) for m in fc.modifiers],
 'keyframe_count':len(fc.keyframe_points),'sampled_count':len(fc.sampled_points)}

def animation_state(o):
 a=o.animation_data
 if a is None:return None
 return {'action':as_plain(a.action),'nla':[(t.name,len(t.strips)) for t in a.nla_tracks],
 'drivers':[driver_description(f) for f in a.drivers]}

def value_guard(value):
 require(type(value) in {int,float} and math.isfinite(value) and 0<=value<=99,'open_angle_deg must be a finite number in [0,99]')
 return float(value)

def property_guard(h):
 require(PROP in h,'Missing native angle property')
 value_guard(h[PROP]);u=h.id_properties_ui(PROP).as_dict()
 require(u.get('min')==0 and u.get('max')==99 and u.get('soft_min')==0 and u.get('soft_max')==99 and u.get('default')==0,'Damaged native angle default/range')

def set_angle(h,value):
 property_guard(h);h[PROP]=value_guard(value);h.update_tag(refresh={'OBJECT'})

def structure_guard(h):
 require(h.type=='EMPTY' and h.data is None and h.parent_type=='OBJECT' and h.parent and h.parent.name=='cab','Unsupported hinge/parent')
 require(h.rotation_mode=='QUATERNION','Unsupported rotation mode')
 require(list(h.rotation_quaternion)==[1.,0.,0.,0.] and list(h.rotation_euler)==[0.,0.,0.], 'Nonidentity rest rotation')
 require(list(h.scale)==[1.,1.,1.] and list(h.delta_scale)==[1.,1.,1.] and list(h.delta_location)==[0.,0.,0.] and list(h.delta_rotation_euler)==[0.,0.,0.] and list(h.delta_rotation_quaternion)==[1.,0.,0.,0.],'Unsupported scale/delta transforms')
 require(np.array_equal(np.asarray(h.matrix_basis)[:3,:3],I3) and np.array_equal(np.asarray(h.matrix_parent_inverse),I4),'Nonidentity basis linear/parent inverse')
 require(not h.constraints and h.animation_data is None and not h.library and not h.override_library and not h.rigid_body and not h.pose,'Unsupported controller dependency')
 seen=[];p=h.parent
 while p:
  require(p.name not in seen,'Parent cycle');seen.append(p.name)
  require(p.type=='EMPTY' and p.parent_type=='OBJECT' and not p.constraints and p.animation_data is None and not p.library and not p.override_library and not p.rigid_body and np.array_equal(np.asarray(p.matrix_world),I4),'Unsupported ancestor '+p.name)
  p=p.parent
 require(seen==['cab','MAZ543_REFERENCE_CHASSIS'],'Unexpected ancestor chain')
 require(PROP not in h and META not in h,'Already configured or conflicting property')


def measure_axes(axis,trial,scope):
 require([d['hinge'] for d in axis['doors']]==[x[0] for x in SPECS],'Damaged axis order')
 require([d['hinge'] for d in trial['doors']]==[x[0] for x in SPECS],'Damaged trial order')
 result=[]
 for (name,side,index),ad,td,sd in zip(SPECS,axis['doors'],trial['doors'],scope['doors']):
  h=bpy.data.objects[name];structure_guard(h)
  require(sd['hinge']==name and len(sd['parts'])==11,'Damaged door scope')
  parts=[p['name'] for p in sd['parts']]
  require(set(parts)=={o.name for o in h.children_recursive} and all(bpy.data.objects[n].parent==h for n in parts),'Unexpected door hierarchy')
  names=[f'BL_Door_{side}_{index}_hinge_{z}' for z in [1.47,1.94,2.38]]
  require([b['name'] for b in ad['barrels']]==names and len(names)==3,'Damaged barrel names')
  require(ad['barrel_axes_mutual_offset_m']<1e-6 and all(abs(v-1)<1e-8 for v in ad['barrel_axis_dot_pivot_axis']),'Damaged axis alignment report')
  centers=[]
  for n,b in zip(names,ad['barrels']):
   o=bpy.data.objects[n];require(o.type=='MESH' and len(o.data.vertices)==48,'Unexpected native barrel')
   w=np.asarray(o.matrix_world);v=array(o.data.vertices,'co',3,np.float64)@w[:3,:3].T+w[:3,3];c=v.mean(0);centers.append(c)
   require(np.array_equal(c,np.asarray(b['center'])),'Axis center differs from actual barrel')
   delta=v-c;values,vectors=np.linalg.eigh(delta.T@delta/len(v));a=vectors[:,-1];a=a if a[2]>=0 else -a
   require(np.linalg.norm(a-np.asarray(b['axis']))<1e-12 and np.linalg.norm(a-[0,0,1])<1e-12,'Damaged barrel axis')
   axial=delta@a
   for extreme in [axial.min(),axial.max()]:
    ring=v[np.abs(axial-extreme)<1e-6];require(len(ring)==24,'Damaged barrel ring')
    radial=ring-ring.mean(0);r=np.linalg.norm(radial,axis=1)
    require(r.max()-r.min()<1e-6 and np.linalg.norm((ring.mean(0)-c)[:2])<1e-6,'Noncircular/noncoaxial barrel ring')
  require(max(np.linalg.norm((c-centers[0])[:2]) for c in centers)<1e-6,'Native barrels not coaxial')
  inv=np.linalg.inv(np.asarray(h.matrix_world));c=np.mean(centers,axis=0);p=inv[:3,:3]@c+inv[:3,3];p[2]=0
  require(np.array_equal(p,np.asarray(td['measured_local_axis_point'])) and np.isfinite(p).all(),'Damaged measured local axis')
  result.append({'hinge':name,'source_side':side,'angle_sign':-side,'parts':parts,'barrels':names,
   'axis_local':p.tolist(),'original_authored':authored(h),'original_custom':{k:as_plain(h[k]) for k in h.keys()},
   'source_sha256':SOURCE_SHA,'scope':'FITTED_NATIVE_AXIS_CONTROLS_ONLY','range_deg':[0,99]})
 return result


def expressions(spec):
 x,y,_=spec['axis_local'];lx,ly,_=spec['original_authored']['location'];sign=spec['angle_sign'];t=f'({sign}*a*0.017453292519943295)'
 # L + p*(1-cos) + q*sin has exactly zero correction at a=0, unlike L+p-p.
 raw={('location',0):f'{lx!r}+{x!r}*(1-cos({t}))+{y!r}*sin({t})',
 ('location',1):f'{ly!r}+{y!r}*(1-cos({t}))-{x!r}*sin({t})',
 ('rotation_quaternion',0):f'cos({t}/2)',('rotation_quaternion',3):f'sin({t}/2)'}
 # Out-of-domain raw scripting bypass does not clamp or extrapolate; native
 # expression evaluation becomes invalid. The public setter rejects before edit.
 return {k:f'({v}) if 0<=a<=99 else sqrt(-1)' for k,v in raw.items()}


def install(specs):
 for s in specs:
  h=bpy.data.objects[s['hinge']];structure_guard(h)
  h[PROP]=0.;h.id_properties_ui(PROP).update(min=0.,max=99.,soft_min=0.,soft_max=99.,default=0.,precision=3,description='Fitted existing barrel-axis door opening in degrees; 0 closed, 99 maximum. Factory mechanism unverified.')
  h[META]=json.dumps(s,sort_keys=True,separators=(',',':'))
  for (path,index),expr in expressions(s).items():
   f=h.driver_add(path,index)
   for m in list(f.modifiers):f.modifiers.remove(m)
   d=f.driver;d.type='SCRIPTED';d.use_self=False
   v=d.variables.new();v.name='a';v.type='SINGLE_PROP';v.targets[0].id_type='OBJECT';v.targets[0].id=h;v.targets[0].data_path='["'+PROP+'"]'
   d.expression=expr
  h.update_tag(refresh={'OBJECT'})
 bpy.context.view_layer.update()


def controls_guard(specs):
 records=[]
 for s in specs:
  h=bpy.data.objects[s['hinge']];property_guard(h)
  require(h.rotation_mode=='QUATERNION' and not h.constraints and h.parent.name=='cab','Controller structure damaged')
  require(json.loads(h[META])==s,'Authored/axis metadata damaged')
  require({k:as_plain(h[k]) for k in s['original_custom']}==s['original_custom'],'Original custom property changed')
  a=h.animation_data;require(a is not None and a.action is None and not a.nla_tracks,'Action/NLA feedback unsupported')
  exp=expressions(s);require(len(a.drivers)==4 and {(f.data_path,f.array_index) for f in a.drivers}==set(exp),'Incorrect native driver topology')
  for f in a.drivers:
   d=f.driver
   require(not f.mute and not f.lock and f.is_valid and d.is_valid and d.is_simple_expression,'Muted/invalid/non-simple driver')
   require(not f.modifiers and not f.keyframe_points and not f.sampled_points,'Unexpected FCurve modifier/keys')
   require(d.type=='SCRIPTED' and not d.use_self and d.expression==exp[(f.data_path,f.array_index)],'Incorrect driver expression')
   require(len(d.variables)==1,'Incorrect variable count');v=d.variables[0]
   require(v.name=='a' and v.type=='SINGLE_PROP' and len(v.targets)==1,'Incorrect variable type')
   t=v.targets[0];require(t.id==h and t.id_type=='OBJECT' and t.data_path=='["'+PROP+'"]' and not t.use_fallback_value,'Unexpected driver target/fallback')
   # Only four transform outputs read one undriven scalar property. No transform
   # variables, frame, context, Python namespace, other IDs or property driver.
  records.append({'hinge':h.name,'ui':h.id_properties_ui(PROP).as_dict(),'drivers':[driver_description(f) for f in a.drivers]})
 return records


def expect_reject(label,fn,records):
 try:fn()
 except (ValueError,TypeError,KeyError) as exc:records.append({'test':label,'rejected':True,'reason':str(exc)});return
 raise ValueError('Negative control wrongly accepted: '+label)


def negative_controls(specs,axis,trial,scope):
 tests=[];h=bpy.data.objects[SPECS[0][0]]
 for x in [-1.,99.0001,float('nan'),float('inf'),True,'45',None]:expect_reject('bad input '+repr(x),lambda x=x:set_angle(h,x),tests)
 # No native mutation is necessary for damaged evidence rejection.
 damaged=copy.deepcopy(specs);damaged[0]['axis_local'][0]+=0.001
 expect_reject('damaged stored axis',lambda:controls_guard(damaged),tests)
 ui=h.id_properties_ui(PROP);ui.update(default=1.)
 try:expect_reject('bad default',lambda:property_guard(h),tests)
 finally:ui.update(default=0.)
 ui.update(max=100.)
 try:expect_reject('bad range',lambda:property_guard(h),tests)
 finally:ui.update(max=99.)
 f=h.animation_data.drivers[0];f.mute=True
 try:expect_reject('muted driver',lambda:controls_guard(specs),tests)
 finally:f.mute=False
 old=f.driver.expression;f.driver.expression='a'
 try:expect_reject('wrong expression',lambda:controls_guard(specs),tests)
 finally:f.driver.expression=old
 target=f.driver.variables[0].targets[0];old_path=target.data_path;target.data_path='location[0]'
 try:expect_reject('transform feedback target',lambda:controls_guard(specs),tests)
 finally:target.data_path=old_path
 h.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update();controls_guard(specs)
 # Invalid raw assignment is intentionally tested on the original native control
 # in memory and restored; no handler, clamping or trusted autoexec is involved.
 h[PROP]=100.;h.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update()
 invalid=[not f.driver.is_valid for f in h.animation_data.drivers]
 require(all(invalid),'Out-of-range raw assignment failed to invalidate native expressions')
 expect_reject('native out-of-range property',lambda:controls_guard(specs),tests)
 tests.append({'test':'raw bypass native expression invalidation','all_four_invalid':invalid})
 h[PROP]=0.
 for f in h.animation_data.drivers:f.driver.expression=f.driver.expression
 h.update_tag(refresh={'OBJECT'});bpy.context.view_layer.update();controls_guard(specs)
 return tests


def baseline(scope):
 dg=bpy.context.evaluated_depsgraph_get();names=[p['name'] for d in scope['doors'] for p in d['parts']]
 require(len(names)==44 and len(set(names))==44,'Wrong moving scope')
 return {'objects':{o.name:object_state(o) for o in bpy.data.objects},
 'object_pointers':{o.name:o.as_pointer() for o in bpy.data.objects},
 'mesh_pointers':{m.name:m.as_pointer() for m in bpy.data.meshes},
 'meshes':{m.name:mesh_signature(m) for m in bpy.data.meshes},
 'animations':{o.name:animation_state(o) for o in bpy.data.objects},
 'closed':{n:snapshot(bpy.data.objects[n],dg) for n in names},
 'names':names}


def verify_identity(base,specs,in_memory):
 require(set(base['objects'])==set(bpy.data.objects.keys()),'Object inventory changed')
 require(set(base['meshes'])==set(bpy.data.meshes.keys()),'Mesh inventory changed')
 current={m.name:mesh_signature(m) for m in bpy.data.meshes}
 require(current==base['meshes'],'Original stored mesh fields changed')
 hinged={s['hinge'] for s in specs}
 for o in bpy.data.objects:
  expected=copy.deepcopy(base['objects'][o.name]);now=object_state(o)
  if o.name in hinged:
   del now['custom'][PROP];del now['custom'][META]
  require(now==expected,'Original closed object state changed: '+o.name)
  if o.name not in hinged:require(animation_state(o)==base['animations'][o.name],'Unrelated animation changed: '+o.name)
  if in_memory:require(o.as_pointer()==base['object_pointers'][o.name],'Object identity replaced: '+o.name)
 if in_memory:require(all(m.as_pointer()==base['mesh_pointers'][m.name] for m in bpy.data.meshes),'Mesh identity replaced')
 dg=bpy.context.evaluated_depsgraph_get()
 for n in base['names']:require(exact_snapshot(snapshot(bpy.data.objects[n],dg),base['closed'][n]),'Closed evaluated mesh/triangles/world matrix changed: '+n)
 return {'object_count':len(base['objects']),'mesh_count':len(current),'closed_exact_evaluated_meshes_triangles_world_matrices':44,'in_memory_original_ID_pointers_exact':in_memory,'stored_mesh_field_signatures':current}


def pose_validation(base,specs):
 moving=set(base['names'])|{s['hinge'] for s in specs};fixed=set(base['objects'])-moving
 states=[]
 angles=[0.,0.731,15.,37.125,45.,75.,83.61,99.]
 for i in range(4):
  for a in angles:v=[0.]*4;v[i]=a;states.append(('individual',v))
 states += [('simultaneous',v) for v in [[15.,45.,75.,99.],[99.,99.,99.,99.],[0.731,37.125,83.61,14.37],[99.,0.,45.,0.],[0.,99.,0.,45.],[0.,0.,0.,0.]]]
 for cycle in range(3):states.extend([('repeat-open-'+str(cycle),[99.]*4),('repeat-close-'+str(cycle),[0.]*4)])
 dg=bpy.context.evaluated_depsgraph_get();rows=[]
 for label,values in states:
  for s,a in zip(specs,values):set_angle(bpy.data.objects[s['hinge']],a)
  bpy.context.view_layer.update();controls_guard(specs)
  for n in fixed:require(authored(bpy.data.objects[n])==base['objects'][n]['transform'],'Unrelated transform changed at pose: '+n)
  maxerr=0.;drifts=[];closed_count=0
  for s,deg in zip(specs,values):
   theta=s['angle_sign']*math.radians(deg);c=math.cos(theta);sn=math.sin(theta);r=np.array([[c,-sn,0],[sn,c,0],[0,0,1]])
   bw=np.asarray(s['original_authored']['matrix_world']);p=np.asarray(s['axis_local']);center=bw[:3,:3]@p+bw[:3,3];rw=bw[:3,:3]@r@np.linalg.inv(bw[:3,:3])
   for n in s['parts']:
    actual=snapshot(bpy.data.objects[n],dg);before=base['closed'][n];pred=(before[0]-center)@rw.T+center
    require(actual[0].shape==pred.shape and np.array_equal(actual[1],before[1]),'Pose topology changed: '+n)
    error=float(np.linalg.norm(actual[0]-pred,axis=1).max());maxerr=max(maxerr,error);require(error<TOL,'Measured-axis geometry mismatch: '+n)
    if deg==0:require(exact_snapshot(actual,before),'Closed identity not exact: '+n);closed_count+=1
    if n in s['barrels']:
     drift=float(np.linalg.norm(actual[0].mean(0)-before[0].mean(0)));require(drift<TOL,'Barrel center drift: '+n);drifts.append({'name':n,'drift_m':drift})
  rows.append({'kind':label,'degrees':values,'max_actual_vertex_formula_error_m':maxerr,'all_12_barrel_centers':drifts,'closed_exact_parts':closed_count,'unchanged_unrelated_transform_count':len(fixed)})
  print('POSE',label,values,'max_error_m',maxerr,'max_barrel_drift_m',max(d['drift_m'] for d in drifts),flush=True)
 return rows


def run(args):
 out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True);report_path=out/(args.mode+'-report.json')
 report={'status':'IN_PROGRESS_NOT_ACCEPTED','mode':args.mode,'asset_status':'LOCAL_ONLY_LFS_BLOCKED','source_saved':False}
 report_path.write_text(json.dumps(report,indent=2)+'\n')
 try:
  root=Path(args.testcar_root).resolve();source=root/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend';candidate=Path(args.candidate).resolve() if args.candidate else out/'MAZ543A_Native_Barrel_Axis_Controls.blend'
  require(bpy.app.version[:3]==(4,5,13),'Official Blender 4.5.13 required');require(not bpy.context.preferences.filepaths.use_scripts_auto_execute,'Run with --disable-autoexec')
  require(sha(source)==SOURCE_SHA,'Wrong original source SHA')
  require(candidate!=source and candidate.parent==out,'Candidate must be separate and inside explicit outside-repository work directory')
  if args.mode=='build':require(not candidate.exists(),'Refusing second candidate save or overwrite')
  data={}
  for key,(rel,expected) in INPUTS.items():require(sha(root/rel)==expected,'Damaged input SHA: '+key);data[key]=json.loads((root/rel).read_text());require(data[key]['source_sha256']==SOURCE_SHA,'Wrong evidence source: '+key)
  bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
  require(bpy.context.evaluated_depsgraph_get().mode=='VIEWPORT','Unsupported evaluation mode')
  specs=measure_axes(data['axis'],data['trial'],data['scope'])
  # Mutation rejection test on a controller before installation, then exact restore.
  h=bpy.data.objects[SPECS[0][0]];saved=h.rotation_quaternion.copy();h.rotation_quaternion=(math.cos(.1),0.,0.,math.sin(.1));bpy.context.view_layer.update();pretests=[]
  try:expect_reject('nonidentity actual rest quaternion',lambda:structure_guard(h),pretests)
  finally:h.rotation_quaternion=saved;bpy.context.view_layer.update()
  specs=measure_axes(data['axis'],data['trial'],data['scope']);base=baseline(data['scope'])
  report.update(blender_version=bpy.app.version_string,script_sha256=sha(__file__),source_sha256=SOURCE_SHA,input_sha256={k:sha(root/v[0]) for k,v in INPUTS.items()},specifications=specs,preflight_negative_tests=pretests,driver_topology='16 simple expressions: per hinge location[0,1], quaternion[0,3], each SINGLE_PROP from same undriven open_angle_deg; no transform/context/frame variable; zero FCurve modifiers',autoexec_enabled=False,native_axis_formula='original_basis @ Translation(p - Rz(angle)*p) @ Rz(angle); original identity rest quaternion verified, never assumed',factory_axis_claim=False,whole_vehicle_gates='16 OPEN',closed_contact_gates='6 original closed contacts remain OPEN',limits=['Fitted existing simplified barrel axes, no manufacturer hinge mechanism or dimension claim','No head-attachment repair, new geometry, reparenting, origin changes, hiding or body movement','Finite pose samples only; no continuous clearance, physics, scene animation, rendering or browser acceptance','No LFS/Git/upload/production promotion; saved native asset remains LOCAL_ONLY_LFS_BLOCKED','Stored mesh signature covers explicit authored fields and every attribute payload; excludes runtime caches/computed normals','Raw Python property assignment can bypass UI bounds: out-of-range invalidates native driver evaluation and validator rejects; use bounded UI or set_angle API'])
  if args.mode=='verify':
   require(candidate.exists(),'Candidate missing');report['candidate_sha256_before']=sha(candidate)
   bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False);bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
   require(not bpy.context.preferences.filepaths.use_scripts_auto_execute,'Autoexec unexpectedly enabled')
   report['initial_identity']=verify_identity(base,specs,False)
  else:install(specs);report['initial_identity']=verify_identity(base,specs,True)
  report['driver_records']=controls_guard(specs)
  report['negative_tests']=negative_controls(specs,data['axis'],data['trial'],data['scope'])
  report['poses']=pose_validation(base,specs)
  report['final_identity']=verify_identity(base,specs,args.mode!='verify');report['final_driver_records']=controls_guard(specs)
  report['maximum_vertex_formula_error_m']=max(r['max_actual_vertex_formula_error_m'] for r in report['poses'])
  report['maximum_barrel_center_drift_m']=max(b['drift_m'] for r in report['poses'] for b in r['all_12_barrel_centers'])
  report['threshold_m']=TOL;report['pose_count']=len(report['poses']);report['source_sha256_after']=sha(source);require(report['source_sha256_after']==SOURCE_SHA,'Original source changed')
  report['status']='NATIVE_CONTROL_IN_MEMORY_PASS' if args.mode!='verify' else 'FRESH_REOPEN_DISABLE_AUTOEXEC_PASS'
  # Only this line may save; it is reached after all in-memory tests and rest restore.
  if args.mode=='build':
   report['status']='IN_MEMORY_PASS_SAVE_PENDING';report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
   require(bpy.ops.wm.save_as_mainfile(filepath=str(candidate),check_existing=True,compress=True,relative_remap=False)=={'FINISHED'},'Native save failed')
   report.update(status='SAVED_AWAITING_FRESH_REOPEN',candidate_path=str(candidate),candidate_bytes=candidate.stat().st_size,candidate_sha256=sha(candidate),save_count=1)
  if args.mode=='verify':require(sha(candidate)==report['candidate_sha256_before'],'Verifier modified saved candidate');report.update(candidate_path=str(candidate),candidate_bytes=candidate.stat().st_size,candidate_sha256=sha(candidate),save_count=0)
  # Deduplicate the very large per-mesh field inventory in the human report.
  for key in ['initial_identity','final_identity']:
   manifest=report[key].pop('stored_mesh_field_signatures');mp=out/(args.mode+'-'+key+'-mesh-signatures.json');mp.write_text(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n');report[key]['mesh_signature_manifest_sha256']=sha(mp);report[key]['mesh_signature_manifest_file']=mp.name
  report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print('RESULT',report['status'],'source_unchanged',report['source_sha256_after'],'saved',args.mode=='build',flush=True)
 except Exception as exc:
  report.update(status='FAILED_NOT_ACCEPTED',error=str(exc),traceback=traceback.format_exc());report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--testcar-root',required=True);p.add_argument('--out',required=True);p.add_argument('--mode',choices=['trial','build','verify'],default='trial');p.add_argument('--candidate');run(p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []))
