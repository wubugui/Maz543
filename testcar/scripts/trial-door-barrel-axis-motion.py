"""In-memory kinematic trial about measured existing barrel axes.

Never saves a native asset. Keeps the closed pose and fixed vehicle transforms;
compares actual sampled surface contacts with the already published old-axis run.
"""
import bpy,json,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
AXIS=ROOT/'work/cloud-door-barrel-axis-20261001/axis-report.json'
ORIGINAL=ROOT/'work/cloud-original-cab-contact-location-20261001/location-report.json'
DOORS=ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
OUT=ROOT/'work/cloud-door-barrel-motion-trial-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
axis=json.loads(AXIS.read_text());original=json.loads(ORIGINAL.read_text());doors=json.loads(DOORS.read_text())
assert axis['source_sha256']==original['source_sha256']==doors['source_sha256']==EXPECTED
old_details={d['hinge']:json.loads((ORIGINAL.parent/d['detail_file']).read_text()) for d in original['doors']}
for d in original['doors']:assert sha(ORIGINAL.parent/d['detail_file'])==d['detail_sha256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def mesh(o):
 ev=o.evaluated_get(dg);m=ev.to_mesh()
 try:
  xyz=np.asarray([list(v.co) for v in m.vertices],dtype=np.float64);w=np.asarray(ev.matrix_world,dtype=np.float64);xyz=xyz@w[:3,:3].T+w[:3,3]
  m.calc_loop_triangles();tri=np.asarray([list(t.vertices) for t in m.loop_triangles],dtype=np.int32);return xyz,tri
 finally:ev.to_mesh_clear()
def box(s):return s[0].min(0),s[0].max(0)
def separated(a,b):return bool(np.any(np.maximum(b[0]-a[1],a[0]-b[1])>0))
def tree(s):return BVHTree.FromPolygons(s[0].tolist(),s[1].tolist(),all_triangles=True,epsilon=0.)
def same(a,b):return np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1])
fixed_objects=[bpy.data.objects[n] for n in original['fixed_names']];assert len(fixed_objects)==145
fixed={o.name:mesh(o) for o in fixed_objects};boxes={n:box(s) for n,s in fixed.items()};trees={n:tree(s) for n,s in fixed.items()}
all_door_parts=[bpy.data.objects[p['name']] for d in doors['doors'] for p in d['parts']];closed={o.name:mesh(o) for o in all_door_parts}
all_moving={o.name for d in doors['doors'] for o in [bpy.data.objects[d['hinge']],*bpy.data.objects[d['hinge']].children_recursive]}
stationary=[o for o in bpy.data.objects if o.name not in all_moving];matrices={o.name:np.asarray(o.matrix_world,dtype=np.float64) for o in stationary}
report={'status':'IN_MEMORY_BARREL_AXIS_TRIAL_NOT_PROMOTED','source_sha256':EXPECTED,'axis_report_sha256':sha(AXIS),'original_location_report_sha256':sha(ORIGINAL),'frame':0,'fixed_geometry_count':145,'stationary_object_matrix_count':len(stationary),'formula':'basis = original_basis @ Translation((I-Rz)*axis_in_original_hinge_space) @ Rz; closed basis copied exactly','factory_axis_claim':False,'source_saved':False,'doors':[],'whole_vehicle_acceptance':'16 OPEN','limits':['Trial uses fitted existing barrel geometry, not factory coordinates or a reconstructed hinge mechanism','Only five actual angles per door; no continuous collision proof','BVH surface overlaps are candidates, not penetration depth; zero samples do not exclude containment','145 original-cab objects only; 261 previously checked parts have not been re-certified for this different motion, nor other doors/hidden/out-of-root geometry','No runtime website or native saved asset replacement']}
violations=[]
for d,side in zip(doors['doors'],[-1,-1,1,1]):
 h=bpy.data.objects[d['hinge']];base=h.matrix_basis.copy();world=np.asarray(h.matrix_world,dtype=np.float64);inv=np.linalg.inv(world);measured=next(x for x in axis['doors'] if x['hinge']==h.name)
 center=np.mean([x['center'] for x in measured['barrels']],axis=0);local=inv[:3,:3]@center+inv[:3,3];local[2]=0
 assert measured['barrel_axes_mutual_offset_m']<1e-6 and all(abs(x-1)<1e-8 for x in measured['barrel_axis_dot_pivot_axis'])
 parts=[bpy.data.objects[x['name']] for x in d['parts']];barrels=[bpy.data.objects[x['name']] for x in measured['barrels']];barrel_centers={o.name:mesh(o)[0].mean(0) for o in barrels};poses=[]
 try:
  for deg in [0.,15.,45.,75.,99.]:
   angle=-side*math.radians(deg);rot=Matrix.Rotation(angle,4,'Z');delta=Vector(local.tolist())-rot.to_3x3()@Vector(local.tolist())
   h.matrix_basis=base.copy() if deg==0 else base@Matrix.Translation(delta)@rot;bpy.context.view_layer.update()
   changed_fixed=[o.name for o in fixed_objects if not same(mesh(o),fixed[o.name])]
   changed_matrices=[o.name for o in stationary if not np.array_equal(np.asarray(o.matrix_world,dtype=np.float64),matrices[o.name])]
   contacts=[];moving_errors=[]
   for o in parts:
    actual=mesh(o);bb=box(actual);bt=tree(actual)
    r=np.asarray(rot,dtype=np.float64)[:3,:3];cw=world[:3,:3]@local+world[:3,3];rw=world[:3,:3]@r@np.linalg.inv(world[:3,:3]);pred=(closed[o.name][0]-cw)@rw.T+cw
    count=actual[0].shape==pred.shape;err=float(np.max(np.linalg.norm(actual[0]-pred,axis=1))) if count else None
    if not count or not np.array_equal(actual[1],closed[o.name][1]) or err is None or err>=2e-5:moving_errors.append({'name':o.name,'error_m':err})
    for name,b in boxes.items():
     if name in changed_fixed or separated(bb,b):continue
     hits=bt.overlap(trees[name])
     if hits:contacts.append({'moving':o.name,'fixed':name,'triangle_pair_count':len(hits),'first_triangle_pairs':hits[:8]})
   drift=[{'name':o.name,'evaluated_center_drift_m':float(np.linalg.norm(mesh(o)[0].mean(0)-barrel_centers[o.name]))} for o in barrels]
   closed_exact=all(same(mesh(o),closed[o.name]) for o in parts) if deg==0 else None
   prior=next(x for x in old_details[h.name]['poses'] if x['degrees']==deg)
   row={'degrees':deg,'closed_geometry_exact':closed_exact,'changed_fixed_geometry':changed_fixed,'changed_stationary_matrices':changed_matrices,'moving_rigid_regression_failures':moving_errors,'barrel_centers':drift,'old_surface_pair_instances':len(prior['surface_overlap_candidates']),'trial_surface_overlap_candidates':contacts};poses.append(row)
   if changed_fixed or changed_matrices or moving_errors or (deg==0 and not closed_exact) or max(x['evaluated_center_drift_m'] for x in drift)>=2e-6:violations.append({'hinge':h.name,'degrees':deg})
   print('BARREL_TRIAL',h.name,deg,'old',len(prior['surface_overlap_candidates']),'new',len(contacts),'fixed_changes',len(changed_fixed),'other_matrix_changes',len(changed_matrices),flush=True)
 finally:h.matrix_basis=base;bpy.context.view_layer.update()
 report['doors'].append({'hinge':h.name,'measured_local_axis_point':local.tolist(),'poses':poses})
report['all_44_closed_parts_restored_exact']=all(same(mesh(o),closed[o.name]) for o in all_door_parts)
report['all_stationary_matrices_restored_exact']=all(np.array_equal(np.asarray(o.matrix_world,dtype=np.float64),matrices[o.name]) for o in stationary)
report['violations']=violations;report['source_sha256_after']=sha(SOURCE)
assert report['source_sha256_after']==EXPECTED
(OUT/'trial-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert not violations and report['all_44_closed_parts_restored_exact'] and report['all_stationary_matrices_restored_exact']
print('TRIAL_FINISHED',sum(x['old_surface_pair_instances'] for d in report['doors'] for x in d['poses']),sum(len(x['trial_surface_overlap_candidates']) for d in report['doors'] for x in d['poses']),flush=True)
