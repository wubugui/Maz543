"""Read-only scope/dependency inventory for the published cab candidate.

This does not move doors, prove rigidity or test clearance. It establishes which
actual objects and dependencies a subsequent bounded sweep must account for.
"""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
OUT=ROOT/'work/cloud-cab-door-dependencies-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED
assert bpy.app.version[:3]==(4,5,13),bpy.app.version
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
hinges=['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007']
roots=['LEFT DISPLAY ROOT — not vehicle datum','RIGHT DISPLAY ROOT — not vehicle datum']
geometry_types={'MESH','CURVE','FONT','SURFACE'}
moving={o.name for name in hinges for o in [bpy.data.objects[name],*bpy.data.objects[name].children_recursive]}
registry={};queue=[]
def enqueue(o):
 if o and o.name not in registry and o not in queue:queue.append(o)

def animation(o):
 ad=o.animation_data
 if not ad:return None
 drivers=[]
 for f in ad.drivers:
  d=f.driver;variables=[]
  for v in d.variables:
   targets=[]
   for t in v.targets:
    row={'id':t.id.name_full if t.id else None,'id_type':t.id_type,'data_path':t.data_path}
    if v.type=='SINGLE_PROP' and t.id==o and t.data_path=='["press_mm"]':row['held_value']=o.get('press_mm')
    if getattr(t,'id',None) and isinstance(t.id,bpy.types.Object):enqueue(t.id)
    targets.append(row)
   variables.append({'name':v.name,'type':v.type,'targets':targets})
  drivers.append({'path':f.data_path,'index':f.array_index,'type':d.type,'expression':d.expression,'variables':variables,'modifiers':[m.type for m in f.modifiers]})
 return {'action':ad.action.name if ad.action else None,'nla_tracks':len(ad.nla_tracks),'drivers':drivers}

collection_paths={}
def visit(layer,path=(),blocked=()):
 reasons=list(blocked)
 for flag,value in [('layer_exclude',layer.exclude),('layer_holdout',layer.holdout),('layer_indirect_only',layer.indirect_only),('collection_hide_render',layer.collection.hide_render)]:
  if value:reasons.append('/'.join((*path,layer.name))+':'+flag)
 here=(*path,layer.name)
 collection_paths.setdefault(layer.collection.name,[]).append({'path':list(here),'blocked':reasons})
 for child in layer.children:visit(child,here,tuple(reasons))
visit(bpy.context.view_layer.layer_collection)
def eligibility(o):
 blocked=[];p=o
 while p:
  if p.hide_render:blocked.append(p.name+':hide_render')
  p=p.parent
 if not o.visible_camera:blocked.append(o.name+':camera_ray_disabled')
 paths=[p for c in o.users_collection for p in collection_paths.get(c.name,[])]
 if not any(not p['blocked'] for p in paths):blocked.append('no_unblocked_active_viewlayer_collection_path')
 return {'camera_eligible':not blocked,'blocked':blocked,'collections':[c.name for c in o.users_collection]}

def geometry(o):
 ev=o.evaluated_get(dg);mesh=ev.to_mesh()
 if not mesh or not len(mesh.vertices):raise ValueError('No evaluated geometry: '+o.name)
 mesh.calc_loop_triangles();points=[ev.matrix_world@v.co for v in mesh.vertices]
 row={'vertices':len(points),'triangles':len(mesh.loop_triangles),'bounds_world':[[min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]]}
 ev.to_mesh_clear();return row

def object_record(o):
 enqueue(o.parent);mods=[]
 for m in o.modifiers:
  row={'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render}
  if m.type=='BOOLEAN':
   operands=([m.object] if m.operand_type=='OBJECT' and m.object else list(m.collection.all_objects) if m.operand_type=='COLLECTION' and m.collection else [])
   row.update({'operand_type':m.operand_type,'operation':m.operation,'operands':[x.name for x in operands],'moving_door_operands':[x.name for x in operands if x.name in moving]})
   for x in operands:enqueue(x)
  elif m.type=='NODES' and m.node_group:
   row.update({'group':m.node_group.name,'node_types':sorted(set(n.bl_idname for n in m.node_group.nodes)),'group_animation':bool(m.node_group.animation_data),'interface_types':sorted(set(i.socket_type for i in m.node_group.interface.items_tree if i.item_type=='SOCKET'))})
  mods.append(row)
 constraints=[]
 for c in o.constraints:
  t=getattr(c,'target',None);enqueue(t);constraints.append({'name':c.name,'type':c.type,'target':t.name if t else None})
 return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'linked_library':bool(o.library),'modifiers':mods,'constraints':constraints,'animation':animation(o),'data_animation':bool(o.data and getattr(o.data,'animation_data',None)),'shape_keys':bool(o.data and getattr(o.data,'shape_keys',None))}

doors=[]
for name in hinges:
 h=bpy.data.objects[name];enqueue(h);parts=[]
 for o in sorted(h.children_recursive,key=lambda o:o.name):
  enqueue(o)
  if o.type in geometry_types:parts.append({'name':o.name,'visibility':eligibility(o),**geometry(o)})
 doors.append({'hinge':name,'matrix_basis':[list(r) for r in h.matrix_basis],'parts':parts})
assert sum(len(d['parts']) for d in doors)==44
candidates={o.name:o for name in roots for o in bpy.data.objects[name].children_recursive if o.type in geometry_types}
for name in ['cab_0064','cab_0029','cab_0030','cab_0031','BL_Left_driver_steering_column_retained']:candidates[name]=bpy.data.objects[name]
fixed=[];excluded=[]
for o in sorted(candidates.values(),key=lambda o:o.name):
 enqueue(o);v=eligibility(o)
 row={'name':o.name,'visibility':v}
 if v['camera_eligible']:fixed.append({**row,**geometry(o)})
 else:excluded.append(row)
assert any(o['name']=='VA180 B4 / BUTTON — movable cap' for o in fixed)
while queue:
 o=queue.pop(0)
 if o.name in registry:continue
 # Install a placeholder before traversing references to retain cycles as data.
 registry[o.name]={};registry[o.name]=object_record(o)
assert sha(SOURCE)==EXPECTED
button=registry['VA180 B4 / BUTTON PRESS REVIEW — travel is fitted']
cross=[{'object':o['name'],'modifier':m['name'],'moving_operands':m['moving_door_operands']} for o in registry.values() for m in o['modifiers'] if m.get('moving_door_operands')]
report={'status':'SCOPED_DEPENDENCY_INVENTORY_ONLY_NOT_CLEARANCE','source_sha256':EXPECTED,'blender_version':bpy.app.version_string,'frame':0,'source_saved':False,'doors_moved':False,'door_geometry_count':44,'fixed_camera_eligible_count':len(fixed),'excluded_geometry_count':len(excluded),'doors':doors,'fixed_geometry':fixed,'excluded_geometry':excluded,'dependency_objects':registry,'viewlayer_collection_paths':collection_paths,'boolean_dependencies_on_door_hierarchy':cross,'button_animation':button['animation'],'limits':['Camera eligibility is not actual image visibility or proof against occlusion','Only a frame-zero dependency inventory, no rigid/continuous-clearance acceptance','Boolean collection and constant-property driver eligibility still require explicit review and actual-pose regression','Other vehicle/cab surfaces are not included by implication'],'whole_vehicle_acceptance':'16 OPEN'}
(OUT/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
print('CAB_DOOR_DEPENDENCY_INVENTORY',{'moving':44,'fixed':len(fixed),'excluded':len(excluded),'dependency_objects':len(registry),'door_dependent_booleans':len(cross),'report_bytes':(OUT/'inventory.json').stat().st_size},flush=True)
