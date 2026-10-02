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
def snapshot(o,dg,world_override=None,layout_legacy_bounds=False,direct_evaluated=False):
 e=o if direct_evaluated else o.evaluated_get(dg);m=e.to_mesh()
 if m is None:return None
 try:
  legacy_bounds=bounds(np.asarray([tuple(e.matrix_world@v.co) for v in m.vertices],dtype=np.float64)) if layout_legacy_bounds else None
  v=array(m.vertices,'co',3,np.float64);w=np.asarray(e.matrix_world if world_override is None else world_override,dtype=np.float64)
  v=v@w[:3,:3].T+w[:3,3];m.calc_loop_triangles();t=array(m.loop_triangles,'vertices',3,np.int32)
  return {'v':v,'t':t,'legacy_b':legacy_bounds,'faces':len(m.polygons),'b':bounds(v) if len(v) else None,'sig':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest()}
 finally:e.to_mesh_clear()
def tree(m):
 if 'tree' not in m:m['tree']=BVHTree.FromPolygons(m['v'].tolist(),m['t'].tolist(),all_triangles=True,epsilon=0.)
 return m['tree']
def simple_state(o):
 return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'data':o.data.name if o.data else None,
 'matrix_world':[list(x) for x in o.matrix_world],'matrix_basis':[list(x) for x in o.matrix_basis],
 'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_local':o.hide_get(),'select':o.select_get(),
 'collections':sorted(c.name for c in o.users_collection),'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in o.modifiers]}
def topology_components(m,weld=True):
 # Exact-coordinate seam welding used only analytically, never changes native meshes.
 v,t=m['v'],m['t']
 if weld:u,inv=np.unique(v,axis=0,return_inverse=True)
 else:u,inv=v,np.arange(len(v))
 wt=inv[t];parent=np.arange(len(u))
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
 if name in globals().get('original_boolean_tools',{}):return 'ORIGINAL_BOOLEAN_CONSTRUCTION_TOOL'
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
 report['original_object_type_counts']=dict(collections.Counter(o.type for o in original))
 report['excluded_non_geometry_objects']=[{'name':o.name,'type':o.type} for o in original if o.type not in {'MESH','CURVE','SURFACE','FONT','META'}]
 assert all(o.type in {'MESH','CURVE','SURFACE','FONT','META','EMPTY','CAMERA','LIGHT','ARMATURE','LATTICE','SPEAKER','LIGHT_PROBE'} for o in original),'Unsupported geometry-bearing object type requires explicit handling'
 report.update(blender_version=bpy.app.version_string,script_sha256=SCRIPT_SHA,frame=0,door_controls=controls,depsgraph_mode=dg.mode,original_objects=len(original),data_objects=len(bpy.data.objects))
 collection_flags={c.name:[c.hide_viewport,c.hide_render,c.hide_select] for c in bpy.data.collections}
 scene_flags={'frame':scene.frame_current,'render_engine':scene.render.engine,'camera':scene.camera.name if scene.camera else None}
 def get_instances():
  entries=[]
  for x in dg.object_instances:
   if not x.is_instance:continue
   descriptor={'object':x.object.original.name,'parent':x.parent.original.name if x.parent else None,'persistent_id':list(x.persistent_id),'matrix_world':[list(row) for row in x.matrix_world]}
   m=snapshot(x.object,dg,x.matrix_world.copy(),direct_evaluated=True) if x.object.type in {'MESH','CURVE','SURFACE','FONT','META'} else None
   entries.append((descriptor,m))
  entries.sort(key=lambda entry:json.dumps(entry[0],sort_keys=True))
  return [x[0] for x in entries],[x[1] for x in entries]
 instances,instance_geometry=get_instances();report['evaluated_instance_count']=len(instances)
 write('instance-manifest.json',instances)
 original_boolean_tools={}
 for o in original:
  for mod in o.modifiers:
   if mod.type=='BOOLEAN' and mod.object:original_boolean_tools.setdefault(mod.object.name,[]).append({'owner':o.name,'modifier':mod.name,'operation':mod.operation})
 report['original_boolean_tool_references']=original_boolean_tools
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
 bpy.context.view_layer.update();study={o.name:snapshot(o,dg,layout_legacy_bounds=True) for o in [base]+treads}
 study_report=[]
 for old in layout['model_objects']:
  m=study[old['name']];comps,_=topology_components(m,weld=False);welded_comps,_=topology_components(m)
  report.setdefault('study_topology_diagnostics',{})[old['name']]={'raw_indexed':[{k:v for k,v in c.items() if k!='_ids'} for c in comps],'exact_coordinate_welded':[{k:v for k,v in c.items() if k!='_ids'} for c in welded_comps],'exact_duplicate_vertex_count':len(m['v'])-len(np.unique(m['v'],axis=0)),'zero_area_triangles':int(np.sum(np.linalg.norm(np.cross(m['v'][m['t']][:,1]-m['v'][m['t']][:,0],m['v'][m['t']][:,2]-m['v'][m['t']][:,0]),axis=1)<1e-14))}
  if old['name'].startswith('FRAME'):
   unique,inv,counts=np.unique(m['v'],axis=0,return_inverse=True,return_counts=True)
   deg_tri=m['v'][m['t']];crossnorm=np.linalg.norm(np.cross(deg_tri[:,1]-deg_tri[:,0],deg_tri[:,2]-deg_tri[:,0]),axis=1)
   edge_ids=sorted({tuple(sorted((int(row[j]),int(row[(j+1)%3])))) for row in m['t'] for j in range(3)})
   zero_edges=[list(e) for e in edge_ids if np.array_equal(m['v'][e[0]],m['v'][e[1]])]
   diag={'unchanged_native_recipe':True,'raw_triangle_count':len(m['t']),'exact_zero_area_triangle_count':int(np.sum(crossnorm==0)),'near_zero_area_triangle_count_crossnorm_lt1e_14':int(np.sum(crossnorm<1e-14)),
    'exact_zero_length_triangulated_edges':zero_edges,'coincident_vertex_groups':[{'world_position_m':unique[j].tolist(),'evaluated_vertex_indices':np.where(inv==j)[0].tolist()} for j in np.where(counts>1)[0]],
    'degenerate_triangle_records':[{'triangle':int(j),'evaluated_vertex_indices':m['t'][j].tolist(),'cross_product_norm_m2':float(crossnorm[j]),'bounds_m':bounds(deg_tri[j]).tolist()} for j in np.where(crossnorm<1e-14)[0]],
    'interpretation':'Raw indexed edge incidence2 does not certify geometric solid validity. No mesh repair performed. Frame winding witnesses are numerical candidates only; material occupancy/solid safety UNKNOWN.'}
   write('frame-degeneracy-diagnostic.json',diag)
   report['frame_geometry_status']='DEGENERATE_NATIVE_RECIPE_SOLID_VALIDITY_NOT_ESTABLISHED'
  write('fit-report.json',report)
  assert len(m['v'])==old['evaluated_vertices'] and m['faces']==old['evaluated_faces'] and np.array_equal(m['legacy_b'],np.array(old['bounds_world_m'])), (old['name'],len(m['v']),m['faces'],m['legacy_b'].tolist(),old['bounds_world_m'])
  assert len(comps)==1 and comps[0]['closed_oriented_surface'],report['study_topology_diagnostics'][old['name']]
  study_report.append({'name':old['name'],'vertices':len(m['v']),'triangles':len(m['t']),'faces':m['faces'],'bounds_m':m['b'].tolist(),'raw_indexed_closed_oriented_components':1,'geometric_solid_accepted':not old['name'].startswith('FRAME'),'evaluated_sha256':m['sig'],'exact_match_to_pinned_report_counts_and_float32_mathutils_bounds':True,'pinned_mathutils_bounds_m':m['legacy_b'].tolist(),'float64_diagnostic_bounds_max_delta_m':float(np.max(np.abs(m['b']-m['legacy_b'])))})
 report['reconstructed_study']=study_report
 # Both a contained point and a hollow frame-center point ensure containment is not AABB-only.
 c_inside=interior(study[base.name],[(xmin+xmax)/2,yc-width/2+fw/2,fz]);c_void=interior(study[base.name],[-4.4,yc,fz]);assert c_inside and c_void is None
 report['local_method_controls']={'frame_rail_interior_detected':c_inside,'frame_open_void_rejected':True,'tread_center_interior_detected':bool(interior(study[treads[0].name],[-4.5,yc,P['z_tread_center']]))}
 assert report['local_method_controls']['tread_center_interior_detected']
 whole_box=np.array([[xmin,yc-.08,.8764],[xmax,yc+.08,P['sill_min_z_inherited']]])
 checkpoint('rejected_layout_native_side_render')
 original_geometry={o.name:snapshot(o,dg)['sig'] for o in original if o.type in {'MESH','CURVE','SURFACE','FONT','META'} and snapshot(o,dg) is not None}
 old_world=scene.world;old_camera=scene.camera;old_engine=scene.render.engine
 def diagnostic_mat(name,color):
  m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.42;return m
 base.data.materials.append(diagnostic_mat('DIAGNOSTIC_ORANGE_INVALID_FRAME',(.9,.15,.015)))
 treads[0].data.materials.append(diagnostic_mat('DIAGNOSTIC_CYAN_TREAD_1',(.005,.7,.85)))
 treads[1].data.materials.append(diagnostic_mat('DIAGNOSTIC_MAGENTA_REJECTED_TREAD_2',(.9,.005,.25)))
 def link_obj(name,data):
  o=bpy.data.objects.new(name,data);col.objects.link(o);return o
 def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 cam=link_obj('DIAGNOSTIC_SIDE_CAMERA',bpy.data.cameras.new('DIAGNOSTIC_SIDE_CAMERA'));cam.data.type='ORTHO';cam.data.ortho_scale=3.55;cam.location=(-4.02,5.8,1.24);aim(cam,(-4.02,1.48,1.24));scene.camera=cam
 world=bpy.data.worlds.new('DIAGNOSTIC_STUDIO_ONLY');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.75,.8,.9,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4;scene.world=world
 for name,loc,power,size in [('DIAGNOSTIC_KEY',(-4.5,4.4,4),950,4),('DIAGNOSTIC_FILL',(-1.4,2.8,2.4),500,3)]:
  light=link_obj(name,bpy.data.lights.new(name,'AREA'));light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.location=loc;aim(light,(-3.9,1.5,1.05))
 ink=bpy.data.materials.new('DIAGNOSTIC_LABEL_INK');ink.use_nodes=True;ink.node_tree.nodes.clear();em=ink.node_tree.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.015,.008,.018,1);em.inputs['Strength'].default_value=1;out=ink.node_tree.nodes.new('ShaderNodeOutputMaterial');ink.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
 bpy.context.view_layer.update()
 def label(name,text,xy,size):
  d=bpy.data.curves.new(name,'FONT');d.body=text;d.size=size;d.align_y='TOP_BASELINE';o=link_obj(name,d);o.rotation_euler=cam.rotation_euler;o.location=cam.matrix_world@Vector((xy[0],xy[1],-1));d.materials.append(ink)
 label('DIAGNOSTIC_TITLE','FITTED REJECTED LAYOUT / +Y SIDE',(-1.68,1.15),.075)
 label('DIAGNOSTIC_SUBTITLE','MAGENTA: TREAD 2 ENTERS ORIGINAL FRONT WHEEL',(-1.68,1.03),.043)
 label('DIAGNOSTIC_FRAME_NOTE','ORANGE FRAME: INVALID / DEGENERATE NATIVE RECIPE',(-1.68,-.94),.043)
 label('DIAGNOSTIC_LIMIT','Original parts + old steps retained. Saved closed pose only. All 16 gates OPEN.',(-1.68,-1.05),.036)
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.seed=0
 scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1200;scene.render.resolution_y=840;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1
 png=a.out/'rejected-layout-side.png';scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
 assert all(snapshot(o,dg)['sig']==original_geometry[o.name] for o in original if o.name in original_geometry)
 scene.camera=old_camera;scene.world=old_world;scene.render.engine=old_engine
 for o in original:
  if o.name in bpy.context.view_layer.objects:o.select_set(before[o.name]['select'])
 bpy.context.view_layer.objects.active=active;bpy.context.view_layer.update()
 assert {o.name:simple_state(o) for o in original}==before
 assert sha(a.candidate)==pin['candidate'][1] and sha(pin['original'][0])==pin['original'][1] and sha(__file__)==SCRIPT_SHA
 report.update(status='NATIVE_REJECTED_LAYOUT_RENDER_COMPLETED_NOT_INSTALLATION_ACCEPTANCE',seconds_script=time.monotonic()-START,image={'file':png.name,'bytes':png.stat().st_size,'sha256':sha(png)},engine='CYCLES',device='CPU',threads=2,samples=24,resolution=[1200,840],color_management='AgX / Medium High Contrast / exposure0 / gamma1',original_geometry_signatures_preserved=len(original_geometry),original_object_states_preserved=True,source_sha256_after=sha(pin['original'][0]),candidate_sha256_after=sha(a.candidate),saved_any_model=False,original_materials_changed=False,original_parts_moved_hidden_deleted=False,camera_world_matrix=[list(row) for row in cam.matrix_world],camera_orthographic_scale=cam.data.ortho_scale,limits=['All original objects/visibility/materials retained, temporary diagnostic colors only on new study geometry','No diagram guide supports modeled as solids','Frame geometry is INVALID/degenerate; render does not validate it','Finite saved closed pose only, no clearance, manufacture, strength or whole-vehicle acceptance'])
 write('fit-report.json',report);print('RENDER_RESULT',report['status'],flush=True)
except Exception as exc:
 report.update(status='FAILED_NOT_ACCEPTED',error=str(exc),traceback=traceback.format_exc(),seconds_script=time.monotonic()-START);write('fit-report.json',report);raise
