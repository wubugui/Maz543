"""Conditional frozen-snapshot interval separation, never native clearance.

Uses the separately published finite-pose report without rerunning it. A pair
can remain UNRESOLVED; this is not a collision finding. No source is saved.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from door_interval_bounds import certify_pair
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
INVENTORY=ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
POSES=ROOT/'work/cloud-cab-door-poses-20261001/pose-report.json'
OUT=ROOT/'work/cloud-cab-frozen-intervals-20261001';OUT.mkdir(parents=True,exist_ok=True)
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
scope=json.loads(INVENTORY.read_text());poses=json.loads(POSES.read_text())
assert poses['source_sha256']==EXPECTED and poses['source_sha256_after']==EXPECTED
assert poses['inventory_sha256']==sha(INVENTORY) and poses['status']=='SAMPLED_NATIVE_POSE_REGRESSION_PASS'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def points(o):
 ev=o.evaluated_get(dg);m=ev.to_mesh()
 try:
  assert m and len(m.vertices)
  xyz=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
  w=np.asarray(ev.matrix_world,dtype=np.float64);return xyz@w[:3,:3].T+w[:3,3]
 finally:ev.to_mesh_clear()
padding=2e-5;fixed=[]
for item in scope['fixed_geometry']:
 xyz=points(bpy.data.objects[item['name']]);fixed.append((xyz.min(axis=0)-padding,xyz.max(axis=0)+padding))
report={'status':'CONDITIONAL_FROZEN_SNAPSHOT_INTERVALS_ONLY','source_sha256':EXPECTED,'inventory_sha256':sha(INVENTORY),'pose_report_sha256':sha(POSES),'blender_version':bpy.app.version_string,'padding_m_per_box':padding,'max_depth':6,'max_cells_per_pair':127,'fixed_names':[x['name'] for x in scope['fixed_geometry']],'doors':[],'native_continuous_clearance_accepted':False,'whole_vehicle_acceptance':'16 OPEN','limits':['Only frozen rigid snapshot vertices under stated hinge formula; full evaluated-scene dependency eligibility remains unproven','Analytic Float64 closed-interval extrema plus 20 micrometre padding, not formal floating-point interval arithmetic','Unresolved overlapping boxes are not collisions or passes','Finite native pose regression is separate evidence, not a continuous proof','No other cab or vehicle surfaces included implicitly; no geometry modified or saved']}
for door,side in zip(scope['doors'],[-1,-1,1,1]):
 hinge=bpy.data.objects[door['hinge']];w=np.asarray(hinge.matrix_world,dtype=np.float64);inv=np.linalg.inv(w);lo,hi=sorted((0.,-side*math.radians(99)));rows=[];unresolved=[]
 for moving_index,item in enumerate(door['parts']):
  xyz=points(bpy.data.objects[item['name']]);local=xyz@inv[:3,:3].T+inv[:3,3]
  a=np.column_stack((local[:,0],local[:,1],np.zeros(len(local))))@w[:3,:3].T
  b=np.column_stack((-local[:,1],local[:,0],np.zeros(len(local))))@w[:3,:3].T
  c=np.column_stack((np.zeros(len(local)),np.zeros(len(local)),local[:,2]))@w[:3,:3].T+w[:3,3]
  for fixed_index,box in enumerate(fixed):
   result=certify_pair(a,b,c,box,lo,hi,max_depth=6,max_cells=127,padding=padding)
   certified=result['status'].startswith('CERTIFIED');gaps=[x['padded_gap_m'] for x in result['clear_intervals']]
   rows.append([moving_index,fixed_index,certified,result['cells'],min(gaps) if gaps else None])
   if not certified:unresolved.append({'moving_index':moving_index,'fixed_index':fixed_index,'intervals':result['unresolved_intervals']})
 detail={'hinge':hinge.name,'angle_radians':[lo,hi],'moving_names':[x['name'] for x in door['parts']],'fixed_names':report['fixed_names'],'row_columns':['moving_index','fixed_index','snapshot_separation_certified','cells','minimum_proved_padded_gap_m'],'rows':rows,'unresolved':unresolved}
 path=OUT/(hinge.name+'.json');path.write_text(json.dumps(detail,ensure_ascii=False,separators=(',',':'))+'\n')
 entry={'hinge':hinge.name,'pairs':len(rows),'certified_frozen_pairs':sum(x[2] for x in rows),'unresolved_pairs':len(unresolved),'max_cells':max(x[3] for x in rows),'detail_file':path.name,'detail_sha256':sha(path)};report['doors'].append(entry);print('FROZEN_INTERVAL',entry,flush=True)
report.update({'source_sha256_after':sha(SOURCE),'total_pairs':sum(x['pairs'] for x in report['doors']),'certified_frozen_pairs':sum(x['certified_frozen_pairs'] for x in report['doors']),'unresolved_pairs':sum(x['unresolved_pairs'] for x in report['doors']),'source_saved':False})
assert report['source_sha256_after']==EXPECTED
(OUT/'interval-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('DONE',report['total_pairs'],report['certified_frozen_pairs'],report['unresolved_pairs'],flush=True)
