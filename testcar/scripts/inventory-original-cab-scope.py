"""Read-only missing-scope inventory; no clearance or identity acceptance."""
import bpy, hashlib, json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
PRIOR=ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
OUT=ROOT/'work/cloud-original-cab-scope-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
prior=json.loads(PRIOR.read_text());covered={x['name'] for x in prior['fixed_geometry']};doors={x['name'] for d in prior['doors'] for x in d['parts']}
root=bpy.data.objects['cab'];desc=list(root.children_recursive);desc_names={x.name for x in desc}
geometry={'MESH','CURVE','FONT','SURFACE'}
rows=[]
for o in sorted(desc,key=lambda x:x.name):
 if o.type not in geometry:continue
 ancestry=[];p=o.parent
 while p:ancestry.append(p.name);p=p.parent
 ev=o.evaluated_get(dg);m=ev.to_mesh();bounds=None;counts=None
 try:
  if m and len(m.vertices):
   m.calc_loop_triangles();pts=[ev.matrix_world@v.co for v in m.vertices]
   bounds=[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]];counts={'vertices':len(m.vertices),'triangles':len(m.loop_triangles)}
 finally:ev.to_mesh_clear()
 rows.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'ancestors':ancestry,'prior_scope':'fixed_cab_261' if o.name in covered else 'moving_door_44' if o.name in doors else 'not_in_prior_pair_scope','object_hide_render':o.hide_render,'camera_ray_enabled':o.visible_camera,'collections':[c.name for c in o.users_collection],'collection_hide_render':[c.name for c in o.users_collection if c.hide_render],'materials':[s.material.name if s.material else None for s in o.material_slots],'geometry':counts,'bounds_world':bounds,'has_animation_data':bool(o.animation_data),'constraints':[c.type for c in o.constraints],'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in o.modifiers]})
external=[{'name':o.name,'parent':o.parent.name if o.parent else None,'type':o.type} for o in bpy.data.objects if o.type in geometry and o.name not in desc_names and (o.name.startswith('cab_') or o.name.startswith('BL_Front_') or o.name.startswith('BL_Door_'))]
report={'status':'ORIGINAL_CAB_SCOPE_INVENTORY_ONLY','source_sha256':EXPECTED,'source_sha256_after':sha(SOURCE),'blender_version':bpy.app.version_string,'frame':0,'root':root.name,'root_matrix_world':[list(r) for r in root.matrix_world],'descendant_objects':len(desc),'geometry_objects':len(rows),'scope_counts':dict(Counter(x['prior_scope'] for x in rows)),'objects':rows,'cab_named_geometry_outside_root':external,'source_saved':False,'whole_vehicle_acceptance':'16 OPEN','limits':['Names and ancestry are inventory, not verified factory component identity','Object/collection render flags are recorded separately, not treated as physical absence or actual image visibility','No automatic collision exclusions or clearance conclusion','Other vehicle surfaces can exist outside this cab ancestry and naming query']}
assert report['source_sha256_after']==EXPECTED
(OUT/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n');print('ORIGINAL_CAB_SCOPE',report['descendant_objects'],report['geometry_objects'],report['scope_counts'],'external',len(external),flush=True)
