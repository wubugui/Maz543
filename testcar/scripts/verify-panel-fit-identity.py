"""Saved-file identity and primary-camera eligibility, not appearance acceptance."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/cloud-left-driver-side-20261001/MAZ543A_Master.blend'
STUDY=ROOT/'outputs/cloud-cab-panel-study-20261001/study.blend'
NEW=ROOT/'outputs/cloud-cab-panel-fit-20261001/iteration-03/MAZ543A_Master.blend'
OUT=NEW.with_suffix('.identity.json');assert not OUT.exists()
source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OLD,STUDY,NEW]}
build=json.loads(NEW.with_suffix('.build.json').read_text());assert source_hashes[str(NEW)]==build['candidate_sha256'] and source_hashes[str(OLD)]==build['source_sha256'] and source_hashes[str(STUDY)]==build['study_sha256']
roots=['LEFT DISPLAY ROOT — not vehicle datum','RIGHT DISPLAY ROOT — not vehicle datum']
manifest=json.loads((STUDY.parent/'build-manifest.json').read_text())
def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def value(v):
 if v is None or isinstance(v,(bool,int,float,str)):return v
 if isinstance(v,bpy.types.ID):return {'id_type':v.bl_rna.identifier,'name':v.name}
 if hasattr(v,'to_list'):return value(v.to_list())
 if hasattr(v,'to_dict'):return {k:value(x) for k,x in v.to_dict().items()}
 return [value(x) for x in v]
def modifiers(o):
 result=[]
 for m in o.modifiers:
  r={'type':m.type,'name':m.name}
  for p in m.bl_rna.properties:
   if p.is_readonly or p.identifier in {'rna_type','is_expanded'} or p.type=='COLLECTION':continue
   r[p.identifier]=value(getattr(m,p.identifier))
  result.append(r)
 return result
def geometry(o):
 h=hashlib.sha256();m=o.data
 if o.type=='MESH':
  for seq,prop,n,dtype in [(m.vertices,'co',3,np.float32),(m.loops,'vertex_index',1,np.int32),(m.polygons,'loop_start',1,np.int32),(m.polygons,'loop_total',1,np.int32),(m.polygons,'material_index',1,np.int32)]:
   a=np.empty(len(seq)*n,dtype=dtype);seq.foreach_get(prop,a);h.update(a.tobytes())
  for uv in m.uv_layers:
   h.update(uv.name.encode());a=np.empty(len(uv.uv)*2,dtype=np.float32);uv.uv.foreach_get('vector',a);h.update(a.tobytes())
 elif o.type=='CURVE':
  h.update(json.dumps([(s.type,s.use_cyclic_u,[list(p.co) for p in s.points],[(list(p.co),list(p.handle_left),list(p.handle_right),p.handle_left_type,p.handle_right_type) for p in s.bezier_points]) for s in m.splines]).encode())
 return h.hexdigest()
def snapshot(o):
 return {'type':o.type,'geometry_uv':geometry(o),'local':[list(r) for r in o.matrix_local],'world':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'collections':sorted(c.name for c in o.users_collection),'material_slots':[s.material.name if s.material else None for s in o.material_slots],'modifiers':modifiers(o)}
def open_file(p):
 bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
open_file(OLD);old={o.name:snapshot(o) for o in bpy.data.objects if o.type=='MESH'}
open_file(STUDY);module={};ownership={};source_roots={}
for name in roots:
 root=bpy.data.objects[name];source_roots[name]=np.array(root.matrix_world)
 for o in root.children_recursive:
  module[o.name]=snapshot(o);ownership[o.name]=name
open_file(NEW);fail=[];unrelated=0
for name,s in old.items():
 o=bpy.data.objects.get(name)
 if o is None:fail.append({'object':name,'reason':'original mesh missing'});continue
 now=snapshot(o)
 if name=='cab_0064':
  keys=['world','parent','hide_render','collections','material_slots','modifiers']
 elif name in {'cab_0066','cab_0067','cab_0068'}:
  keys=['type','geometry_uv','local','world','parent','material_slots','modifiers']
 else:keys=list(s);unrelated+=1
 for k in keys:
  if now[k]!=s[k]:fail.append({'object':name,'reason':'old saved-file field differs','field':k})
placements={r['root']:np.array(r['world_matrix']) for r in build['placements']}
for name in roots:
 actual=np.array(bpy.data.objects[name].matrix_world)
 if np.max(np.abs(actual-placements[name]))>1e-6:fail.append({'object':name,'reason':'saved root differs from declared FITTED placement'})
module_results=[]
for name,s in module.items():
 o=bpy.data.objects.get(name)
 if o is None:fail.append({'object':name,'reason':'source-study descendant missing'});continue
 now=snapshot(o);different=[]
 for k in ['type','geometry_uv','parent','hide_render','material_slots','modifiers']:
  if now[k]!=s[k]:different.append(k)
 local_error=float(np.max(np.abs(np.array(now['local'])-np.array(s['local']))))
 expected_world=placements[ownership[name]]@np.linalg.inv(source_roots[ownership[name]])@np.array(s['world'])
 world_error=float(np.max(np.abs(np.array(now['world'])-expected_world)))
 if local_error>1e-6 or world_error>1e-6:different.append('relative/world transform')
 if different:fail.append({'object':name,'reason':'source-study identity or placement differs','fields':different})
 module_results.append({'name':name,'root':ownership[name],'source_authored_geometry_uv_sha256':s['geometry_uv'],'local_matrix_max_error':local_error,'expected_fitted_world_matrix_max_error':world_error,'identity_pass':not different})

# Eligibility is not a guarantee of unoccluded/opaque pixels. Inspect all enabled
# render ViewLayers and their collection paths, not merely Collection.hide_render.
layer_paths={}
for layer in bpy.context.scene.view_layers:
 if not layer.use:continue
 paths_for_layer={}
 def walk(lc,parent_reasons=(),path=()):
  reasons=list(parent_reasons)
  for prop in ('exclude','holdout','indirect_only'):
   if not hasattr(lc,prop):raise RuntimeError('Missing LayerCollection API '+prop)
   if getattr(lc,prop):reasons.append(prop+':'+lc.name)
  if lc.collection.hide_render:reasons.append('collection.hide_render:'+lc.name)
  path=path+(lc.name,)
  for o in lc.collection.objects:paths_for_layer.setdefault(o.name,[]).append({'path':list(path),'blocked_by':reasons})
  for child in lc.children:walk(child,reasons,path)
 walk(layer.layer_collection);layer_paths[layer.name]=paths_for_layer
eligibility=[]
for name in ['cab_0064']+manifest['claimed_closed_solids']:
 o=bpy.data.objects[name];camera=getattr(o,'visible_camera',None);object_holdout=getattr(o,'is_holdout',None);layers=[]
 for layer in bpy.context.scene.view_layers:
  if not layer.use:continue
  paths=layer_paths[layer.name].get(name,[]);in_layer=name in layer.objects
  holdout=o.holdout_get(view_layer=layer) if in_layer and hasattr(o,'holdout_get') else None
  indirect=o.indirect_only_get(view_layer=layer) if in_layer and hasattr(o,'indirect_only_get') else None
  eligible=in_layer and not o.hide_render and camera is True and object_holdout is False and holdout is False and indirect is False and any(not p['blocked_by'] for p in paths)
  layers.append({'view_layer':layer.name,'in_layer':in_layer,'holdout':holdout,'indirect_only':indirect,'paths':paths,'primary_camera_eligible':eligible})
 ok=any(r['primary_camera_eligible'] for r in layers)
 if not ok:fail.append({'object':name,'reason':'not proven primary-camera eligible'})
 eligibility.append({'object':name,'hide_render':o.hide_render,'visible_camera':camera,'object_is_holdout':object_holdout,'layers':layers,'primary_camera_eligible':ok})
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in source_hashes.items())
report={'source_sha256':source_hashes,'old_unrelated_meshes_post_save_checked':unrelated,'old_field_scope':['authored vertices/topology/UV','world/local transform and parent','material-slot names','writable modifier parameters excluding UI state','object render flag and collection membership'],'source_study_descendants':module_results,'render_eligibility':eligibility,'failures':fail,'status':'PASS_SCOPED_IDENTITY_AND_ELIGIBILITY' if not fail else 'FAIL','limitations':['Fitted roots match the declared implementation, not factory datums','Material shader-node contents, custom normal data and other unlisted attributes not certified unchanged','Eligibility does not guarantee unoccluded or opaque pixels; actual comparison images are separate evidence','No contact, containment, sweep or whole-vehicle acceptance follows'],'all16VehicleGates':'OPEN'}
OUT.write_text(json.dumps(report,indent=2)+'\n');print('PANEL_IDENTITY',unrelated,len(module_results),len(eligibility),'failures',len(fail),flush=True)
if fail:raise SystemExit(1)
