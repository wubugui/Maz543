"""Read-only, single saved pose diagnosis. Reuse pinned published broadphase.

Positive noncoplanar surface crossings only; never infer wheel solid containment.
No model is created, saved, moved, hidden or exported.
"""
import argparse, hashlib, json, sys, time, traceback
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser()
for n in ('candidate','original','inventory','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
encode=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
digest=lambda x:hashlib.sha256(encode(x).encode()).hexdigest()
START=time.monotonic();SCRIPT_SHA=sha(__file__)
LIMITS={'triangle_crossnorm_min_m2':1e-12,'both_plane_straddle_min_m':1e-9,
 'normal_cross_sine_min':1e-5,'overlap_segment_min_m':1e-7,
 'interior_barycentric_min':1e-6,'plane_and_reconstruction_residual_max_m':1e-10}
R={'status':'IN_PROGRESS','whole_vehicle_gates':'ALL 16 OPEN','source_saved':False,
 'scope':'Original +Y lower step versus original first +Y wheel at saved frame0, VIEWPORT evaluation',
 'method_limits':LIMITS,'script_sha256':SCRIPT_SHA}
def write(n,v):(a.out/n).write_text(encode(v)+'\n')
def checkpoint(stage):
 R['stage']=stage;write('datum-report.json',R);print('STAGE',stage,round(time.monotonic()-START,3),flush=True)
def bounds(v):return np.array([v.min(0),v.max(0)])
def gap(b,c):return np.maximum(0,np.maximum(np.array(b)[0]-np.array(c)[1],np.array(c)[0]-np.array(b)[1]))
def overlaps(b,c):return not np.any(gap(b,c)>0)
def get_array(seq,attr,width,dtype):
 x=np.empty(len(seq)*width,dtype=dtype);seq.foreach_get(attr,x);return x.reshape(-1,width)
def snapshot(o,dg,matrix=None,direct=False):
 e=o if direct else o.evaluated_get(dg);m=e.to_mesh()
 try:
  v=get_array(m.vertices,'co',3,np.float64);w=np.array(e.matrix_world if matrix is None else matrix,dtype=np.float64)
  v=v@w[:3,:3].T+w[:3,3];m.calc_loop_triangles();t=get_array(m.loop_triangles,'vertices',3,np.int32)
  return {'v':v,'t':t,'b':bounds(v),'sig':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest()}
 finally:e.to_mesh_clear()
def original_state():
 return [{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,
  'data':o.data.name if o.data else None,'matrix_world':[list(r) for r in o.matrix_world],
  'matrix_basis':[list(r) for r in o.matrix_basis],'hide_render':o.hide_render,
  'hide_viewport':o.hide_viewport,'hide_local':o.hide_get(),'select':o.select_get(),
  'collections':sorted(c.name for c in o.users_collection),
  'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in o.modifiers]}
  for o in sorted(bpy.data.objects,key=lambda o:o.name)]
def instance_descriptor(x):
 return {'object':x.object.original.name,'parent':x.parent.original.name if x.parent else None,
  'persistent_id':list(x.persistent_id),'matrix_world':[list(r) for r in x.matrix_world]}
def barycentric(tri,q):
 e1,e2=tri[1]-tri[0],tri[2]-tri[0];d=q-tri[0]
 den=np.dot(e1,e1)*np.dot(e2,e2)-np.dot(e1,e2)**2
 v=(np.dot(e2,e2)*np.dot(d,e1)-np.dot(e1,e2)*np.dot(d,e2))/den
 w=(np.dot(e1,e1)*np.dot(d,e2)-np.dot(e1,e2)*np.dot(d,e1))/den
 return np.array([1-v-w,v,w])
def crossing(A,B):
 """A strict positive witness. None is deliberately not a no-contact proof."""
 na=np.cross(A[1]-A[0],A[2]-A[0]);nb=np.cross(B[1]-B[0],B[2]-B[0])
 ca,cb=float(np.linalg.norm(na)),float(np.linalg.norm(nb))
 if min(ca,cb)<=LIMITS['triangle_crossnorm_min_m2']:return None
 na/=ca;nb/=cb;dA=(A-B[0])@nb;dB=(B-A[0])@na
 straddles=[float(-dA.min()),float(dA.max()),float(-dB.min()),float(dB.max())]
 if min(straddles)<=LIMITS['both_plane_straddle_min_m']:return None
 direction=np.cross(na,nb);sine=float(np.linalg.norm(direction))
 if sine<=LIMITS['normal_cross_sine_min']:return None
 direction/=sine
 def section(T,d):
  points=[]
  for i in range(3):
   j=(i+1)%3
   if d[i]==0:points.append(T[i])
   if d[i]*d[j]<0:points.append(T[i]+(T[j]-T[i])*(d[i]/(d[i]-d[j])))
  if len(points)!=2:return None
  return np.array(sorted(points,key=lambda q:float(q@direction)))
 sa,sb=section(A,dA),section(B,dB)
 if sa is None or sb is None:return None
 ta,tb=sa@direction,sb@direction;lo,hi=max(ta[0],tb[0]),min(ta[1],tb[1]);length=float(hi-lo)
 if length<=LIMITS['overlap_segment_min_m']:return None
 def at(s,t,v):return s[0]+(s[1]-s[0])*((v-t[0])/(t[1]-t[0]))
 seg=np.array([at(sa,ta,lo),at(sa,ta,hi)]);segB=np.array([at(sb,tb,lo),at(sb,tb,hi)])
 q=seg.mean(0);ba,bb=barycentric(A,q),barycentric(B,q)
 planes=[float(abs((q-A[0])@na)),float(abs((q-B[0])@nb))]
 recon=[float(np.linalg.norm(ba@A-q)),float(np.linalg.norm(bb@B-q))]
 line_delta=float(np.max(np.linalg.norm(seg-segB,axis=1)))
 if min(ba.min(),bb.min())<=LIMITS['interior_barycentric_min']:return None
 if max(planes+recon+[line_delta])>LIMITS['plane_and_reconstruction_residual_max_m']:return None
 # Physical distance of the shared interior point to each triangle edge.
 edge_margin=[]
 for T,bary,crossnorm in ((A,ba,ca),(B,bb,cb)):
  edge_margin.append([float(bary[i]*crossnorm/np.linalg.norm(T[(i+2)%3]-T[(i+1)%3])) for i in range(3)])
 return {'status':'STRICT_NONCOPLANAR_TRIANGLE_SURFACE_CROSSING',
  'step_triangle_world_m':A.tolist(),'wheel_triangle_world_m':B.tolist(),
  'shared_segment_world_m':seg.tolist(),'shared_interior_point_world_m':q.tolist(),
  'triangle_crossnorms_m2':[ca,cb],'normal_cross_sine':sine,
  'step_vertices_signed_distance_to_wheel_plane_m':dA.tolist(),
  'wheel_vertices_signed_distance_to_step_plane_m':dB.tolist(),
  'both_plane_straddle_margins_m':straddles,'intersection_segment_length_m':length,
  'point_step_barycentric':ba.tolist(),'point_wheel_barycentric':bb.tolist(),
  'point_edge_distance_margins_m':edge_margin,'point_plane_residuals_m':planes,
  'point_barycentric_reconstruction_residuals_m':recon,'segment_two_constructions_max_delta_m':line_delta}
def predicate_controls():
 A=np.array([[0.,0,0],[2,0,0],[0,2,0]])
 B=np.array([[.3,.3,-1],[.3,.3,1],[1.1,.3,0]])
 cases=[('crossing',B,True),('separated',B+np.array([3,0,0]),False),
  ('coplanar',np.array([[.2,.2,0],[.8,.2,0],[.2,.8,0]]),False),
  ('touch_only',np.array([[.3,.3,0],[.3,.3,1],[1.1,.3,1]]),False),
  ('degenerate',np.array([[.3,.3,-1],[.3,.3,0],[.3,.3,1]]),False)]
 rows=[]
 # Rotation, translation and both winding reversals exercise the world-coordinate predicate.
 ang=.431;rot=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1.]])
 for mode in range(4):
  for name,b,expect in cases:
   aa=A.copy();bb=b.copy()
   if mode==1:aa=aa[::-1]
   if mode==2:bb=bb[::-1]
   if mode==3:aa=aa@rot.T+[-4,1.5,.9];bb=bb@rot.T+[-4,1.5,.9]
   got=crossing(aa,bb) is not None;assert got==expect,(mode,name,got)
   rows.append([mode,name,expect,got])
 return rows
try:
 checkpoint('input_validation')
 pins={'candidate':(a.candidate,'3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f'),
  'original':(a.original,'8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'),
  'published_inventory':(a.inventory,'7929cddd99fbdeb4a38acbd69ea98133bf14a4a8fdf0db56ecc8a6161d9f2221')}
 for k,(path,h) in pins.items():assert sha(path)==h,(k,sha(path))
 R['inputs']={k:{'path':str(path),'sha256':h,'bytes':path.stat().st_size} for k,(path,h) in pins.items()}
 prior=json.loads(a.inventory.read_text());assert not prior['errors'];rows=prior['objects'];assert len(rows)==10353
 byname={r['name']:r for r in rows};assert len(byname)==10353
 stepnames=['BL_Cab_-1_step']+[f'BL_Step_-1_{i}' for i in range(20)]
 steps=[byname[n] for n in stepnames]
 wheelrows=[r for r in rows if r['parent']=='wheels_pivot_002']
 assert len(wheelrows)==275
 assert all(r['source_object'].startswith(('BL_Tyre_0_','BL_Rim_0_','BL_Hub_0_','BL_Wheel_0_')) for r in wheelrows)
 wheels=[r for r in wheelrows if r['instance'] is None];assert len(wheels)==186
 pairnames=[(s['name'],w['name']) for s in steps for w in wheels if overlaps(s['bounds_m'],w['bounds_m'])]
 union=np.array([[min(r['bounds_m'][0][i] for r in steps) for i in range(3)],
  [max(r['bounds_m'][1][i] for r in steps) for i in range(3)]])
 broad={'status':'REUSED_PUBLISHED_SNAPSHOT_NOT_FRESH_ALL_SCENE_EVALUATION',
  'inventory_sha256':pins['published_inventory'][1],'source_entry_count':len(rows),
  'original_step_source_count':21,'step_instance_entries':[r['name'] for r in rows if r['source_object'] in stepnames and r['instance'] is not None],
  'first_wheel_selection':'Exact prior parent wheels_pivot_002; every member retains distinct source_object identity; all match tyre0/rim0/hub0/wheel0 names',
  'first_wheel_entries':len(wheelrows),'first_wheel_source_objects':len(wheels),'first_wheel_instances':len(wheelrows)-len(wheels),
  'original_step_union_bounds_m':union.tolist(),'source_pair_count':21*len(wheels),
  'aabb_overlapping_source_pairs':pairnames,
  'all_scene_union_aabb_overlapping_entries':[r['name'] for r in rows if r.get('bounds_m') and overlaps(union,r['bounds_m'])],
  'wheel_union_separation_rows':[{'entry':r['name'],'bounds_m':r['bounds_m'],'step_union_axis_gap_m':gap(union,r['bounds_m']).tolist(),
    'prior_duplicate_of':r.get('exact_duplicate_geometry_placement_of')} for r in wheelrows],
  'interpretation':'Positive axis gaps separate boxes only in the pinned snapshot; overlapping boxes are not collisions. No full wheel solidity or enclosure assertion.'}
 write('reused-broadphase.json',broad)
 selected=set(stepnames)|{w for s,w in pairnames}
 # Include actual tread, rim and hub geometry as freshly verified datums even where boxes separate.
 selected|={'BL_Tyre_0_curved_tread_blocks','BL_Rim_0_bead_lock','BL_Rim_0_pressed_dish',
  'BL_Hub_0_cover','BL_Hub_0_planetary_case','BL_Hub_0_oil_plug'}
 targetrows=[r for r in rows if r['source_object'] in selected]
 assert bpy.app.version[:3]==(4,5,13)
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 bpy.ops.wm.open_mainfile(filepath=str(a.candidate));scene=bpy.context.scene
 assert scene.frame_current==0 and not bpy.context.preferences.filepaths.use_scripts_auto_execute
 controls={n:float(bpy.data.objects[n]['open_angle_deg']) for n in ('cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007')}
 assert all(x==0 for x in controls.values());bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();assert dg.mode=='VIEWPORT'
 state0=original_state();state_sha0=digest(state0)
 R.update(blender_version=bpy.app.version_string,frame=scene.frame_current,door_controls=controls,depsgraph_mode=dg.mode,
  original_object_count=len(state0),original_state_sha256_start=state_sha0,
  state_fields=list(state0[0].keys()),predicate_controls=predicate_controls())
 checkpoint('fresh_selected_geometry_matches_published_snapshot')
 cache={};fresh=[];instcache={}
 for x in dg.object_instances:
  if x.is_instance and x.object.original.name in selected:
   d=instance_descriptor(x);key=encode(d);assert key not in instcache
   instcache[key]=snapshot(x.object,dg,x.matrix_world.copy(),direct=True)
 for r in targetrows:
  if r['instance'] is None:m=snapshot(bpy.data.objects[r['source_object']],dg)
  else:
   d={k:v for k,v in r['instance'].items() if k!='manifest_index'};m=instcache.pop(encode(d))
  assert m['sig']==r['evaluated_position_triangle_sha256'],r['name']
  assert np.array_equal(m['b'],np.array(r['bounds_m'])),r['name']
  assert len(m['v'])==r['vertices'] and len(m['t'])==r['triangles'],r['name']
  cache[r['name']]=m
  fresh.append({'entry':r['name'],'source_object':r['source_object'],'prior_signature_matched':True,
   'evaluated_position_triangle_sha256':m['sig'],'vertices':len(m['v']),'triangles':len(m['t']),
   'bounds_m':m['b'].tolist(),'is_instance':r['instance'] is not None,
   'instance_descriptor':r['instance'],'prior_duplicate_of':r.get('exact_duplicate_geometry_placement_of')})
 assert not instcache,'Additional relevant instance not represented in pinned inventory'
 for r in targetrows:
  if r.get('exact_duplicate_geometry_placement_of'):
   assert cache[r['name']]['sig']==cache[r['exact_duplicate_geometry_placement_of']]['sig']
 write('fresh-selected-geometry.json',fresh)
 R['fresh_evaluated_entries']=len(fresh);R['fresh_source_objects']=len(selected)
 R['fresh_instances']=sum(x['is_instance'] for x in fresh)
 checkpoint('strict_triangle_crossing_checks')
 results=[];witnesses=[]
 for sn,wn in pairnames:
  sm,wm=cache[sn],cache[wn];sv,wv=sm['v'][sm['t']],wm['v'][wm['t']]
  wbmin,wbmax=wv.min(1),wv.max(1);candidates=0;positives=[];best=None
  for si,A in enumerate(sv):
   ids=np.flatnonzero(np.all(wbmax>=A.min(0),axis=1)&np.all(wbmin<=A.max(0),axis=1));candidates+=len(ids)
   for wi in ids:
    w=crossing(A,wv[wi])
    if w is not None:
     positives.append([si,int(wi)]);score=min(min(z) for z in w['point_edge_distance_margins_m'])
     if best is None or score>best[0]:best=(score,si,int(wi),w)
  rr={'step':sn,'wheel':wn,'triangle_aabb_candidate_count':candidates,'strict_positive_triangle_pair_count':len(positives),
   'status':'SURFACE_CROSSING_FOUND' if best else 'NO_STRICT_CROSSING_WITNESS_FOUND_NOT_CLEARANCE',
   'strict_positive_triangle_pairs':positives}
  if best:
   score,si,wi,w=best;w.update(step=sn,wheel=wn,step_triangle_index=si,wheel_triangle_index=wi,
    step_triangle_vertex_indices=sm['t'][si].tolist(),wheel_triangle_vertex_indices=wm['t'][wi].tolist(),
    selected_by='Largest minimum triangle-edge distance at the shared segment midpoint among strict positive pairs',
    step_evaluated_position_triangle_sha256=sm['sig'],wheel_evaluated_position_triangle_sha256=wm['sig'])
   rr['selected_witness_index']=len(witnesses);witnesses.append(w)
  results.append(rr);print('PAIR',sn,wn,candidates,len(positives),flush=True)
 write('triangle-pairs.json',results);write('crossing-witnesses.json',witnesses)
 curve=bpy.data.objects['BL_Cab_-1_step'];cd=curve.data
 curve_record={'object':curve.name,'curve_data':cd.name,'bevel_depth_m':cd.bevel_depth,
  'bevel_resolution':cd.bevel_resolution,'use_fill_caps':cd.use_fill_caps,
  'world_matrix':[list(r) for r in curve.matrix_world],'splines':[]}
 for s in cd.splines:
  assert s.type=='POLY'
  pts=[list(curve.matrix_world@x.co.to_3d()) for x in s.points]
  curve_record['splines'].append({'type':s.type,'cyclic':s.use_cyclic_u,'world_path_points_m':pts})
 tyre=cache['BL_Tyre_0_VI203_profile'];tread=cache['BL_Tyre_0_curved_tread_blocks']
 datums={'status':'EXISTING_GEOMETRY_REFERENCE_ONLY_NOT_FACTORY_HARDPOINTS','curve':curve_record,
  'curve_bounds_m':cache[curve.name]['b'].tolist(),'tyre_profile_bounds_m':tyre['b'].tolist(),
  'tyre_tread_block_bounds_m':tread['b'].tolist(),'negative_X_is_forward':True,
  'step_bars':[{'object':n,'bounds_m':cache[n]['b'].tolist(),'center_m':cache[n]['b'].mean(0).tolist(),
   'source_of_dimensions':'Existing evaluated geometry only'} for n in stepnames[1:]],
  'curve_rear_end_minus_profile_forward_bound_m':float(cache[curve.name]['b'][1,0]-tyre['b'][0,0]),
  'last_bar_rear_end_minus_profile_forward_bound_m':float(cache['BL_Step_-1_19']['b'][1,0]-tyre['b'][0,0]),
  'interpretation':'X overlap is a datum comparison, not collision depth. Native curve is an uncapped authoring path; it is not a certified support structure. All geometry is inherited, not a factory measurement.'}
 write('existing-datums.json',datums)
 checkpoint('preservation_and_terminal_checks')
 for n in sorted(selected):assert snapshot(bpy.data.objects[n],dg)['sig']==cache[n]['sig'],n
 state1=original_state();assert state1==state0
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 for k,(path,h) in pins.items():assert sha(path)==h,k
 assert sha(__file__)==SCRIPT_SHA
 R.update(status='BOUNDED_ORIGINAL_STEP_DATUM_DIAGNOSTIC_COMPLETE',
  datum_decision='REJECT_EXISTING_LOWER_STEP_AS_VERIFIED_INSTALLATION_BASELINE' if witnesses else 'EXISTING_LOWER_STEP_BASELINE_REMAINS_UNVERIFIED',
  surface_crossing_object_pairs=len(witnesses),strict_positive_triangle_pairs=sum(r['strict_positive_triangle_pair_count'] for r in results),
  crossing_step_objects=sorted({w['step'] for w in witnesses}),crossing_wheel_objects=sorted({w['wheel'] for w in witnesses}),
  original_state_sha256_end=digest(state1),original_state_unchanged=True,selected_source_geometry_unchanged=True,
  input_hashes_unchanged=True,script_sha256_end=sha(__file__),elapsed_seconds=time.monotonic()-START,
  limitations=['Published complete snapshot reused for broadphase; only listed selected geometry freshly evaluated.',
   'Positive strict triangle crossings establish intersecting surfaces; no wheel volume, penetration depth, factory fit or continuous-motion claim.',
   'No strict witness in a tested pair does not establish clearance; coplanar, edge-only, near-degenerate and enclosure cases remain outside the predicate.',
   'No original part hidden, deleted, moved or saved; no new model or render; no dimensions refitted or hardpoints invented.',
   'The saved native control candidate remains LOCAL_ONLY_LFS_BLOCKED; all 16 whole-vehicle gates stay OPEN.'])
 R['outputs']={n:{'sha256':sha(a.out/n),'bytes':(a.out/n).stat().st_size} for n in
  ('reused-broadphase.json','fresh-selected-geometry.json','triangle-pairs.json','crossing-witnesses.json','existing-datums.json')}
 checkpoint('complete')
except Exception:
 R.update(status='FAILED_NOT_ACCEPTED',error=traceback.format_exc(),elapsed_seconds=time.monotonic()-START)
 write('datum-report.json',R);write('FAILURE.json',R);raise
