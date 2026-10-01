"""Locate unresolved original-cab scope and sampled surface-overlap candidates.

Bounds overlap is not collision. BVH triangle overlap is a surface-contact
candidate, not penetration depth, factory fit, or a continuous-motion proof.
"""
import bpy,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
from door_interval_bounds import swept_bounds,separation
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
INVENTORY=ROOT/'work/cloud-original-cab-scope-20261001/inventory.json'
DOORS=ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
OUT=ROOT/'work/cloud-original-cab-contact-location-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
scope=json.loads(INVENTORY.read_text());door_scope=json.loads(DOORS.read_text());assert scope['source_sha256']==door_scope['source_sha256']==EXPECTED
selected=[x for x in scope['objects'] if x['prior_scope']=='not_in_prior_pair_scope' and not x['object_hide_render']]
assert len(selected)==145
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def mesh(o):
 ev=o.evaluated_get(dg);m=ev.to_mesh()
 try:
  assert m and len(m.vertices),o.name
  xyz=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
  w=np.asarray(ev.matrix_world,dtype=np.float64);xyz=xyz@w[:3,:3].T+w[:3,3]
  m.calc_loop_triangles();tri=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',tri)
  return xyz,tri.reshape(-1,3)
 finally:ev.to_mesh_clear()
def bvh(snapshot):return BVHTree.FromPolygons(snapshot[0].tolist(),snapshot[1].tolist(),all_triangles=True,epsilon=0.0)
def bounds(snapshot):return snapshot[0].min(axis=0),snapshot[0].max(axis=0)
fixed_objects=[bpy.data.objects[x['name']] for x in selected];fixed={o.name:mesh(o) for o in fixed_objects};fixed_bounds={n:bounds(s) for n,s in fixed.items()};fixed_bvh={n:bvh(s) for n,s in fixed.items()}
padding=2e-5
report={'status':'CONTACT_LOCATION_ONLY_NOT_ACCEPTANCE','source_sha256':EXPECTED,'inventory_sha256':sha(INVENTORY),'door_inventory_sha256':sha(DOORS),'frame':0,'fixed_names':[o.name for o in fixed_objects],'selection':'145 objects outside prior pair scope with object hide_render=false; collection visibility not used to silently exclude geometry','padding_m_per_box':padding,'doors':[],'source_saved':False,'whole_vehicle_acceptance':'16 OPEN','limits':['Only selected cab ancestry, not the 82 self-hidden objects or 24 named objects outside the root','Frozen full-interval AABB separation is conditional on rigid snapshot semantics; overlap remains unresolved','Sampled native BVH surface overlaps are contact candidates, not penetration depth or clearance acceptance; intended hinges/seals can contact','Zero sampled surface overlaps do not certify a pair or exclude containment; unresolved intervals remain unresolved','Other controls fixed at frame zero; no render/web/factory-dimension acceptance']}
for d,side in zip(door_scope['doors'],[-1,-1,1,1]):
 h=bpy.data.objects[d['hinge']];base=h.matrix_basis.copy();w=np.asarray(h.matrix_world,dtype=np.float64);inv=np.linalg.inv(w);parts=[bpy.data.objects[x['name']] for x in d['parts']];pairs=[]
 for part in parts:
  xyz=mesh(part)[0];local=xyz@inv[:3,:3].T+inv[:3,3]
  a=np.column_stack((local[:,0],local[:,1],np.zeros(len(local))))@w[:3,:3].T;b=np.column_stack((-local[:,1],local[:,0],np.zeros(len(local))))@w[:3,:3].T;c=np.column_stack((np.zeros(len(local)),np.zeros(len(local)),local[:,2]))@w[:3,:3].T+w[:3,3]
  lo,hi=sorted((0.,-side*math.radians(99)));swept=swept_bounds(a,b,c,lo,hi,padding)
  for name,box in fixed_bounds.items():
   gap,axis=separation(swept,(box[0]-padding,box[1]+padding));pairs.append({'moving':part.name,'fixed':name,'frozen_interval_separated':gap>0,'padded_axis_gap_m':gap,'axis':axis})
 poses=[]
 try:
  for deg in [0.,15.,45.,75.,99.]:
   h.matrix_basis=base@Matrix.Rotation(-side*math.radians(deg),4,'Z');bpy.context.view_layer.update();changed=[];contacts=[]
   for o in fixed_objects:
    current=mesh(o);old=fixed[o.name]
    if not np.array_equal(current[0],old[0]) or not np.array_equal(current[1],old[1]):changed.append(o.name)
   for part in parts:
    snap=mesh(part);bb=bounds(snap);tree=bvh(snap)
    for name,box in fixed_bounds.items():
     if name in changed:continue
     if separation(bb,box)[0]>0:continue
     hits=tree.overlap(fixed_bvh[name])
     if hits:contacts.append({'moving':part.name,'fixed':name,'triangle_pair_count':len(hits),'first_triangle_pairs':hits[:8]})
   poses.append({'degrees':deg,'fixed_geometry_or_topology_changed':changed,'surface_overlap_candidates':contacts});print('CONTACT_POSE',h.name,deg,'changed',len(changed),'candidate_pairs',len(contacts),flush=True)
 finally:h.matrix_basis=base;bpy.context.view_layer.update()
 detail={'hinge':h.name,'pairs':pairs,'poses':poses};p=OUT/(h.name+'.json');p.write_text(json.dumps(detail,ensure_ascii=False,separators=(',',':'))+'\n')
 report['doors'].append({'hinge':h.name,'pairs':len(pairs),'frozen_interval_separated':sum(x['frozen_interval_separated'] for x in pairs),'unresolved_full_bounds':sum(not x['frozen_interval_separated'] for x in pairs),'sampled_contact_pair_instances':sum(len(x['surface_overlap_candidates']) for x in poses),'detail_file':p.name,'detail_sha256':sha(p)})
report['source_sha256_after']=sha(SOURCE);assert report['source_sha256_after']==EXPECTED
(OUT/'location-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('DONE',report['doors'],flush=True)
