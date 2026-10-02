"""One saved closed-pose MAZ step-envelope installation diagnostic; never save a model.
Native Cube/Boolean/Bevel recipe reproduces the pinned existing layout; no hand-built mesh.
All existing evaluable scene geometry participates, regardless of visibility.
AABB proximity, triangle surface candidates and strict interior witnesses remain distinct.
"""
import argparse, collections, hashlib, importlib.util, json, math, sys, time, traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--layout-report',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SCRIPT_SHA=sha(__file__);START=time.monotonic();EPS=2e-5;NEAR=.35
report={'status':'IN_PROGRESS_NOT_ACCEPTED','whole_vehicle_gates':'ALL 16 OPEN','source_saved':False,'door_state':'SAVED CLOSED ENDPOINT ONLY; no motion or continuous clearance'}
def write(name,obj):
 (a.out/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')
def checkpoint(stage):
 report['stage']=stage;write('fit-report.json',report);print('STAGE',stage,round(time.monotonic()-START,3),flush=True)
checkpoint('initialize')

def array(c,f,w,dtype):
 x=np.empty(len(c)*w,dtype=dtype);c.foreach_get(f,x);return x.reshape(-1,w) if w>1 else x

def bounds(v):return np.array([v.min(0),v.max(0)])
def gap(b,c):return np.maximum(0,np.maximum(b[0]-c[1],c[0]-b[1]))
def overlaps(b,c,eps=0):return bool(np.all(gap(b,c)<=eps))
def snapshot(o,dg,world_override=None):
 e=o.evaluated_get(dg);m=e.to_mesh()
 if m is None:return None
 try:
  v=array(m.vertices,'co',3,np.float64);w=np.asarray(e.matrix_world if world_override is None else world_override,dtype=np.float64)
  v=v@w[:3,:3].T+w[:3,3];m.calc_loop_triangles();t=array(m.loop_triangles,'vertices',3,np.int32)
  return {'v':v,'t':t,'faces':len(m.polygons),'b':bounds(v) if len(v) else None,'sig':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest()}
 finally:e.to_mesh_clear()
def tree(m):
 if 'tree' not in m:m['tree']=BVHTree.FromPolygons(m['v'].tolist(),m['t'].tolist(),all_triangles=True,epsilon=0.)
 return m['tree']
def simple_state(o):
 return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'data':o.data.name if o.data else None,
 'matrix_world':[list(x) for x in o.matrix_world],'matrix_basis':[list(x) for x in o.matrix_basis],
 'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_local':o.hide_get(),'select':o.select_get(),
 'collections':sorted(c.name for c in o.users_collection),'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in o.modifiers]}
def topology_components(m):
 # Exact-coordinate seam welding used only analytically, never changes native meshes.
 v,t=m['v'],m['t'];u,inv=np.unique(v,axis=0,return_inverse=True);wt=inv[t];parent=np.arange(len(u))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(x,y):
  x,y=find(int(x)),find(int(y))
  if x!=y:parent[y]=x
 for x,y,z in wt:union(x,y);union(y,z)
 groups={}
 for i,row in enumerate(wt):groups.setdefault(find(int(row[0])),[]).append(i)
 groups=sorted(groups.values(),key=lambda ids:int(t[ids].min()))
 rows=[];assignment=np.full(len(t),-1,dtype=int)
 for ci,ids in enumerate(groups):
  edges=collections.Counter();orient=collections.Counter()
  for row in wt[ids]:
   for j in range(3):
    x,y=int(row[j]),int(row[(j+1)%3]);edges[tuple(sorted((x,y)))]+=1;orient[(x,y)]+=1
  bad=sum(n!=2 for n in edges.values());badwind=sum(orient[(x,y)]!=orient[(y,x)] for x,y in edges)
  vv=np.unique(t[ids]);assignment[ids]=ci
  rows.append({'component':ci,'min_original_vertex_index':int(vv.min()),'vertices':len(vv),'triangles':len(ids),'bounds_m':bounds(v[vv]).tolist(),
  'exact_weld_edge_incidence_not_two':bad,'exact_weld_edge_winding_imbalance':badwind,'closed_oriented_surface':bad==0 and badwind==0,'_ids':ids})
 return rows,assignment

def winding(m,p):
 # Numerical oriented solid angle, evaluated triangles; valid solid interpretation only on closed oriented component.
 q=m['v'][m['t']]-np.asarray(p);u,v,w=q[:,0],q[:,1],q[:,2];lu=np.linalg.norm(u,axis=1);lv=np.linalg.norm(v,axis=1);lw=np.linalg.norm(w,axis=1)
 numerator=np.einsum('ij,ij->i',u,np.cross(v,w));denominator=lu*lv*lw+np.einsum('ij,ij->i',u,v)*lw+np.einsum('ij,ij->i',v,w)*lu+np.einsum('ij,ij->i',w,u)*lv
 return float(np.sum(2*np.arctan2(numerator,denominator))/(4*np.pi))
def interior(m,p):
 if np.any(np.asarray(p)<=m['b'][0]+EPS) or np.any(np.asarray(p)>=m['b'][1]-EPS):return None
 hit=tree(m).find_nearest(Vector(p));d=float(hit[3]) if hit[0] is not None else None
 if d is None or d<=EPS:return None
 wn=winding(m,p)
 if abs(abs(wn)-1)<1e-6:return {'point_m':list(map(float,p)),'distance_to_enclosing_surface_m':d,'oriented_winding_number':wn}
 return None

def candidate_points(src,dst,ids):
 # Every candidate triangle supplies vertices, centroid, midpoints and a clipped-to-box centroid.
 for i in ids:
  tri=src['v'][src['t'][i]]
  for label,q in [('centroid',tri.mean(0)),('edge_01',(tri[0]+tri[1])/2),('edge_12',(tri[1]+tri[2])/2),('edge_20',(tri[2]+tri[0])/2)]+[(f'vertex_{j}',tri[j]) for j in range(3)]:
   if np.all(q>dst['b'][0]+EPS) and np.all(q<dst['b'][1]-EPS):yield int(i),label,q
  poly=[q.copy() for q in tri]
  for axis in range(3):
   for sign,limit in [(1,dst['b'][0,axis]+2*EPS),(-1,dst['b'][1,axis]-2*EPS)]:
    out=[]
    for j,u in enumerate(poly):
     v=poly[(j+1)%len(poly)];du=sign*(u[axis]-limit);dv=sign*(v[axis]-limit)
     if du>=0:out.append(u)
     if (du>=0)!=(dv>=0):out.append(u+(v-u)*(du/(du-dv)))
    poly=out
    if not poly:break
   if not poly:break
  if len(poly)>=3:yield int(i),'triangle_clipped_to_inset_aabb_centroid',np.mean(poly,axis=0)

def witness(src,dst,ids):
 # First successful original-triangle point, with signed-angle and nearest-surface checks.
 for i,label,q in candidate_points(src,dst,ids):
  result=interior(dst,q)
  if result:return dict(result,source_triangle=i,point_construction=label)
 return None

def category(name):
 name=name.split('::')[-1]
 if name=='BL_Cab_-1_step' or name.startswith('BL_Step_-1_'):return 'EXISTING_LOW_STEP_AUTHORING_SCHEME'
 if name in ('cab_0062','cab_0063'):return 'MIXED_LEGACY_BATCH_COMPONENT_ID_REQUIRED'
 if name.startswith('BL_Cab_') or name.startswith('BL_Door_'):return 'CAB_BODY_OR_DOOR'
 if any(s in name.lower() for s in ['tyre','tire','wheel','tread']):return 'WHEEL_TYRE_NAME_LEAD'
 return 'OTHER_ACTUAL_VEHICLE_GEOMETRY'

try:
 assert bpy.app.version[:3]==(4,5,13)
 pin={'candidate':(a.candidate,'3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f'),
 'original':(a.repo/'testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend','8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'),
 'layout_report':(a.layout_report,'032e788adbc4db4e3987a7736687acf79ab830665ba95b05e7302d89f0d8c6ea'),
 'layout_recipe':(a.repo/'testcar/scripts/build-step-layout-study.py','b295070b1d492c0d376ee732586003928bb94f12db503dbfc089dca93d152812'),
 'topology_provenance':(a.repo/'testcar/reference/cab-step-primary-topology-20261001.json','8edcf765400b3a7c684a6eb7461427a11472aff9a42f8e572b2f878ff26addad'),
 'native_assembly':(a.repo/'testcar/work/cloud-native-step-assembly-20261001/native-assembly-report.json','e8b4781c1d05fc0a539e9b52ed84226c16fcc057eec9fa20627f8feb75dc4e17')}
 for key,(path,expected) in pin.items():assert sha(path)==expected,(key,sha(path))
 report['inputs']={k:{'filename':v[0].name,'sha256':v[1],'bytes':v[0].stat().st_size} for k,v in pin.items()}
 layout=json.loads(a.layout_report.read_text());P=layout['params_m'];report['params_m']=P;report['parameter_provenance']=layout['parameter_provenance']
 bpy.ops.wm.open_mainfile(filepath=str(a.candidate));scene=bpy.context.scene;assert scene.frame_current==0;assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();assert dg.mode=='VIEWPORT'
 original=list(bpy.data.objects);original_names=sorted(o.name for o in scene.objects);before={o.name:simple_state(o) for o in original};active=bpy.context.view_layer.objects.active
 original_mesh_names=set(bpy.data.meshes.keys());original_curve_names=set(bpy.data.curves.keys());original_collection_names=set(bpy.data.collections.keys())
 controls={n:float(bpy.data.objects[n]['open_angle_deg']) for n in ['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007']};assert all(v==0 for v in controls.values())
 report.update(blender_version=bpy.app.version_string,script_sha256=SCRIPT_SHA,frame=0,door_controls=controls,depsgraph_mode=dg.mode,original_objects=len(original),data_objects=len(bpy.data.objects))
 collection_flags={c.name:[c.hide_viewport,c.hide_render,c.hide_select] for c in bpy.data.collections}
 scene_flags={'frame':scene.frame_current,'render_engine':scene.render.engine,'camera':scene.camera.name if scene.camera else None}
 def get_instances():
  return [{'object':x.object.original.name,'parent':x.parent.original.name if x.parent else None,'persistent_id':list(x.persistent_id),'matrix_world':[list(row) for row in x.matrix_world]} for x in dg.object_instances if x.is_instance]
 instances=get_instances();report['evaluated_instance_count']=len(instances)
 write('instance-manifest.json',instances)
 checkpoint('native_layout_reconstruction')
 col=bpy.data.collections.new('TEMP_INSTALLATION_FIT_ONLY');scene.collection.children.link(col)
 def cube(name,center,dims):
  bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
 xmin,xmax=P['x_frame'];yc=P['y_center'];width=P['width'];fw=P['frame_rect_section_width'];fh=P['frame_rect_section_height'];fz=P['z_frame_center']
 base=cube('FRAME__connected_lower_envelope',((xmin+xmax)/2,yc-width/2+fw/2,fz),(xmax-xmin,fw,fh))
 parts=[cube('TOOL__outer_longitudinal_rail',((xmin+xmax)/2,yc+width/2-fw/2,fz),(xmax-xmin,fw,fh))]
 for i,x in enumerate(P['x_stations']):parts.append(cube(f'TOOL__transverse_station_{i+1}',(x,yc,fz),(fw,width,fh)))
 for o in parts:
  mod=base.modifiers.new('Editable native union '+o.name,'BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=o;o.hide_render=True;o.hide_set(True);o.display_type='WIRE'
 bevel=base.modifiers.new('Fitted edge softening only','BEVEL');bevel.width=P['frame_bevel_display_fit'];bevel.segments=3;bevel.affect='EDGES'
 treads=[cube(f'TREAD_REGION_{i+1}__plain_envelope',((xa+xb)/2,yc,P['z_tread_center']),(xb-xa,width,P['tread_thickness'])) for i,(xa,xb) in enumerate(P['tread_x'])]
 bpy.context.view_layer.update();study={o.name:snapshot(o,dg) for o in [base]+treads}
 study_report=[]
 for old in layout['model_objects']:
  m=study[old['name']];comps,_=topology_components(m)
  assert len(m['v'])==old['evaluated_vertices'] and m['faces']==old['evaluated_faces'] and np.array_equal(m['b'],np.array(old['bounds_world_m']))
  assert len(comps)==1 and comps[0]['closed_oriented_surface']
  study_report.append({'name':old['name'],'vertices':len(m['v']),'triangles':len(m['t']),'faces':m['faces'],'bounds_m':m['b'].tolist(),'closed_oriented_components':1,'evaluated_sha256':m['sig'],'exact_match_to_pinned_report_counts_and_bounds':True})
 report['reconstructed_study']=study_report
 # Both a contained point and a hollow frame-center point ensure containment is not AABB-only.
 c_inside=interior(study[base.name],[(xmin+xmax)/2,yc-width/2+fw/2,fz]);c_void=interior(study[base.name],[-4.4,yc,fz]);assert c_inside and c_void is None
 report['local_method_controls']={'frame_rail_interior_detected':c_inside,'frame_open_void_rejected':True,'tread_center_interior_detected':bool(interior(study[treads[0].name],[-4.5,yc,P['z_tread_center']]))}
 assert report['local_method_controls']['tread_center_interior_detected']
 whole_box=np.array([[xmin,yc-.08,.8764],[xmax,yc+.08,P['sill_min_z_inherited']]])
 checkpoint('all_actual_vehicle_geometry_broad_phase')
 inventory=[];cache={};errors=[]
 entries=[(o.name,o,None,None) for o in sorted(original,key=lambda o:o.name)]
 for j,inst in enumerate(instances):
  entries.append((f"INSTANCE_{j:04d}::{inst['object']}",bpy.data.objects[inst['object']],inst['matrix_world'],inst))
 for idx,(key,o,world_override,inst) in enumerate(entries):
  if o.type not in {'MESH','CURVE','SURFACE','FONT','META'}:continue
  try:
   m=snapshot(o,dg,world_override)
   row={'name':key,'source_object':o.name,'instance':inst,'in_scene':o.name in scene.objects,'type':o.type,'parent':before[o.name]['parent'],'data':before[o.name]['data'],'flags':[o.hide_render,o.hide_viewport,o.hide_get()],
   'category':category(o.name),'collections':before[o.name]['collections']}
   if m is None or not len(m['v']):row['status']='NO_EVALUATED_VERTICES';inventory.append(row);continue
   row.update(vertices=len(m['v']),triangles=len(m['t']),bounds_m=m['b'].tolist(),evaluated_position_triangle_sha256=m['sig'],near_layout_aabb_lower_bound_m=float(np.linalg.norm(gap(m['b'],whole_box))))
   row['physical_pair_axis_gaps_m']={n:gap(m['b'],s['b']).tolist() for n,s in study.items()}
   if row['near_layout_aabb_lower_bound_m']<=NEAR and len(m['t']):cache[key]=m
   inventory.append(row)
  except Exception as exc:errors.append({'object':key,'error':str(exc)})
  if idx%1500==0:print('INVENTORY',idx,len(cache),round(time.monotonic()-START,3),flush=True)
 write('all-geometry-inventory.json',{'scope':'ALL evaluable original scene objects, hidden and tool geometry retained; VIEWPORT evaluator at saved frame0','objects':inventory,'errors':errors})
 assert not errors,errors
 report['broad_phase']={'evaluable_objects':len(inventory),'nearby_objects':len(cache),'distance_cutoff_m':NEAR,'proximity_region_m':whole_box.tolist(),'errors':errors,'all_geometry_inventory_sha256':sha(a.out/'all-geometry-inventory.json')}
 checkpoint('targeted_evaluated_triangle_checks')
 pairs=[];component_maps={};nearby=[]
 for name,m in cache.items():
  pair_names=[n for n,s in study.items() if overlaps(m['b'],s['b'],EPS)]
  comps,assignment=topology_components(m);component_maps[name]=comps
  nearby.append({'name':name,'category':category(name),'bounds_m':m['b'].tolist(),'components':[{k:v for k,v in c.items() if k!='_ids'} for c in comps]})
  for sn in pair_names:
   s=study[sn];hits=sorted([list(x) for x in tree(s).overlap(tree(m))]);ids=sorted(set(j for i,j in hits))
   # Include every original triangle with AABB overlap, not only BVH surface hits: catches full containment.
   tri_v=m['v'][m['t']];tri_min=tri_v.min(1);tri_max=tri_v.max(1)
   tids=np.where(np.all(tri_max>=s['b'][0]-EPS,1)&np.all(tri_min<=s['b'][1]+EPS,1))[0]
   bycomp={}
   for ti in tids:bycomp.setdefault(int(assignment[ti]),[]).append(int(ti))
   witnesses=[];inverse=[]
   for ci,localids in bycomp.items():
    w=witness(m,s,localids)
    if w:witnesses.append(dict(w,original_component=ci,original_component_closed_oriented=comps[ci]['closed_oriented_surface']))
   # If a layout component sits wholly inside a closed original component, surfaces need not intersect.
   for ci,c in enumerate(comps):
    cb=np.array(c['bounds_m'])
    if not c['closed_oriented_surface'] or not overlaps(cb,s['b'],EPS):continue
    cm={'v':m['v'],'t':m['t'][c['_ids']],'b':cb}
    w=witness(s,cm,range(len(s['t'])))
    if w:inverse.append(dict(w,original_component=ci))
   row={'study':sn,'existing':name,'category':category(name),'aabb_axis_gaps_m':gap(m['b'],s['b']).tolist(),
    'bvh_triangle_surface_candidate_count':len(hits),'bvh_triangle_surface_pairs':hits,'overlapping_original_triangle_aabbs':len(tids),
    'original_surface_inside_study_solid_witnesses':witnesses,'study_surface_inside_closed_original_component_witnesses':inverse,
    'status':'STRICT_INTERIOR_SURFACE_INTRUSION' if witnesses or inverse else ('TRIANGLE_SURFACE_CANDIDATES_ONLY' if hits else 'AABB_PROXIMITY_ONLY_NO_INTERIOR_WITNESS')}
   pairs.append(row)
 write('nearby-components.json',nearby);write('targeted-pairs.json',pairs)
 report['targeted_summary']={'pair_count':len(pairs),'surface_candidate_pairs':sum(bool(x['bvh_triangle_surface_candidate_count']) for x in pairs),'strict_interior_witness_pairs':sum(x['status']=='STRICT_INTERIOR_SURFACE_INTRUSION' for x in pairs),'rows':[{k:v for k,v in x.items() if k not in ('bvh_triangle_surface_pairs',)} for x in pairs]}
 checkpoint('upper_station_datum_probes')
 probes=[]
 for i,x in enumerate(P['x_stations']):
  point=Vector((x,yc,P['interface_center_z']));near=[]
  for name,m in cache.items():
   h=tree(m).find_nearest(point)
   if h[0] is not None and h[3]<=.30:near.append({'object':name,'distance_m':float(h[3]),'nearest_point_m':list(h[0]),'triangle':int(h[2]),'category':category(name)})
  rays=[]
  for y in [yc,1.48]:
   origin=Vector((x,y,P['interface_center_z']+P['interface_size'][2]/2));hits=[]
   for name,m in cache.items():
    h=tree(m).ray_cast(origin,Vector((0,0,1)),.4)
    if h[0] is not None:hits.append({'object':name,'distance_m':float(h[3]),'point_m':list(h[0]),'triangle':int(h[2]),'category':category(name)})
   rays.append({'origin_m':list(origin),'direction':[0,0,1],'max_distance_m':.4,'hits_sorted':sorted(hits,key=lambda x:x['distance_m'])})
  probes.append({'station':i+1,'fitted_x_m':x,'unknown_interface_center_m':list(point),'nearest_original_surfaces':sorted(near,key=lambda x:x['distance_m'])[:15],'finite_upward_datum_rays':rays})
 write('station-datum-probes.json',{'not_solids':True,'not_hardpoints':True,'scope':'Finite 3 stations / 2 upward rays each; excludes geometry with broad AABB farther than350mm from region. No bracket, load path or material assertion.','stations':probes})
 # Check retained legacy platform identity against prior evaluated full-batch signature.
 prior=json.loads(pin['native_assembly'][0].read_text());identity=[]
 for ob in prior['objects']:
  if ob['name'] not in ['cab_0062','cab_0063','BL_Cab_-1_step','BL_Cab_-1_side_monocoque'] and not ob['name'].startswith('BL_Step_-1_'):continue
  m=cache.get(ob['name']) or snapshot(bpy.data.objects[ob['name']],dg)
  identity.append({'object':ob['name'],'prior_signature':ob['position_topology_sha256'],'current_signature':m['sig'],'equal':m['sig']==ob['position_topology_sha256']})
 assert all(x['equal'] for x in identity)
 report['legacy_identity_vs_original_source']=identity
 # Explicitly remove only temporary study objects; restore original selection/active without changing transforms or visibility.
 checkpoint('preservation_readback')
 for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(col)
 for m in list(bpy.data.meshes):
  if m.name not in original_mesh_names and m.users==0:bpy.data.meshes.remove(m)
 for o in original:
  if o.name in bpy.context.view_layer.objects:o.select_set(before[o.name]['select'])
 bpy.context.view_layer.objects.active=active;bpy.context.view_layer.update()
 after={o.name:simple_state(o) for o in original};assert before==after
 assert sorted(o.name for o in scene.objects)==original_names
 assert collection_flags=={c.name:[c.hide_viewport,c.hide_render,c.hide_select] for c in bpy.data.collections}
 assert scene_flags=={'frame':scene.frame_current,'render_engine':scene.render.engine,'camera':scene.camera.name if scene.camera else None}
 # Full evaluated geometry readback: detects original coordinate/topology changes in every broad-phase participant.
 unchanged=[]
 for row in inventory:
  o=bpy.data.objects[row['source_object']];m=snapshot(o,dg,row['instance']['matrix_world'] if row['instance'] else None)
  if row.get('status')=='NO_EVALUATED_VERTICES':assert m is None or len(m['v'])==0;continue
  assert m['sig']==row['evaluated_position_triangle_sha256'],o.name
  unchanged.append(o.name)
 assert instances==get_instances()
 report['preservation']={'evaluated_instances_and_matrices_unchanged':True,'object_inventory_state_matrices_parents_data_flags_selection_unchanged':True,'scene_collection_flags_unchanged':True,'original_evaluated_geometry_hashes_unchanged':len(unchanged),'original_candidate_sha256_after':sha(a.candidate),'immutable_source_sha256_after':sha(pin['original'][0]),'all_temporary_objects_removed':True,'saved_any_model':False}
 assert sha(a.candidate)==pin['candidate'][1] and sha(pin['original'][0])==pin['original'][1] and sha(__file__)==SCRIPT_SHA
 report.update(status='BOUNDED_INSTALLATION_DIAGNOSTIC_COMPLETE_NOT_INSTALLATION_ACCEPTANCE',seconds_script=time.monotonic()-START,
 existing_six_closed_contact_pairs='PRESERVED OPEN; every original evaluated geometry hash and object transform unchanged; no cab6 reclassification',
 limits=['FITTED single +Y side only; no symmetry or manufacturer dimensions','Only saved frame0 closed-door endpoint; no motion, suspension or continuous clearance','VIEWPORT evaluated mesh geometry; no shader displacement, render tessellation or all-Blender-RNA equality claim','AABB gaps are componentwise lower bounds, not shortest distances; non-overlap does not establish mounting or strength','BVH pairs are numerical triangle-surface candidates; alone do not establish volumetric interference or safe fit','Strict interior witnesses use closed oriented evaluated study solids, >20um nearest-surface margin, and winding abs(1) within1e-6. Finite absence of witness does not prove no containment','Existing component topology uses exact coordinate seam welding only in analysis; no native mesh change','Unknown support and upper interface graphics are not modeled as material; station probes are finite datum observations, not real hardpoints','No deletion, relocation or hiding of existing legacy assemblies; no new blend/GLB, renderer or browser claim; ALL16 OPEN'])
 write('fit-report.json',report);print('RESULT',report['status'],'pairs',len(pairs),'intrusions',report['targeted_summary']['strict_interior_witness_pairs'],flush=True)
except Exception as exc:
 report.update(status='FAILED_NOT_ACCEPTED',error=str(exc),traceback=traceback.format_exc(),seconds_script=time.monotonic()-START);write('fit-report.json',report);raise
