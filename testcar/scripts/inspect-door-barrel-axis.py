"""Read-only internal consistency check: authored hinge barrels versus pivot.

Geometry-derived axes belong to the fitted model, not factory measurements.
No correction, mesh edit, native save, clearance or mechanical acceptance.
"""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
AUTHOR=ROOT/'scripts/blender-model.py'
OUT=ROOT/'work/cloud-door-barrel-axis-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def world_points(o,evaluated=False):
 e=o.evaluated_get(dg) if evaluated else o;m=e.to_mesh() if evaluated else o.data
 try:
  xyz=np.asarray([list(v.co) for v in m.vertices],dtype=np.float64);w=np.asarray(e.matrix_world,dtype=np.float64);return xyz@w[:3,:3].T+w[:3,3]
 finally:
  if evaluated:e.to_mesh_clear()
def axis_fit(o):
 xyz=world_points(o);center=xyz.mean(0);delta=xyz-center
 values,vectors=np.linalg.eigh(delta.T@delta/len(xyz));axis=vectors[:,-1]
 if axis[2]<0:axis=-axis
 along=delta@axis;low=along.min();high=along.max()
 cap_a=xyz[np.abs(along-low)<1e-6];cap_b=xyz[np.abs(along-high)<1e-6]
 assert len(cap_a)==len(cap_b)==24,(o.name,len(xyz),len(cap_a),len(cap_b))
 residual=np.linalg.norm(delta-np.outer(along,axis),axis=1)
 rings=[]
 for key in sorted(set(np.round(along,6))):
  mask=np.round(along,6)==key;ring=xyz[mask];r=residual[mask];ring_center=ring.mean(0);v=ring_center-center
  off=float(np.linalg.norm(v-np.dot(v,axis)*axis))
  assert len(ring)==24 and r.max()-r.min()<1e-6 and off<1e-6,(o.name,'noncircular/noncoaxial ring',len(ring),off)
  rings.append({'axial_coordinate_m':float(along[mask].mean()),'vertices':len(ring),'radius_min_max_m':[float(r.min()),float(r.max())],'axis_center_error_m':off})
 eval_center=world_points(o,True).mean(0)
 return {'name':o.name,'raw_vertices':len(xyz),'rings':rings,'cap_vertices':[len(cap_a),len(cap_b)],'axis':axis.tolist(),'center':center.tolist(),'end_centers':[cap_a.mean(0).tolist(),cap_b.mean(0).tolist()],'length_m':float(high-low),'radius_min_max_m':[float(residual.min()),float(residual.max())],'evaluated_centroid':eval_center.tolist(),'raw_eval_centroid_difference_m':float(np.linalg.norm(center-eval_center))}
report={'status':'FITTED_MODEL_AXIS_CONSISTENCY_DIAGNOSTIC','source_sha256':EXPECTED,'authoring_script_sha256':sha(AUTHOR),'authoring_reference':'blender-model.py cylinder loop: start+0.018, side*1.548, heights1.47/1.94/2.38; C maps browser Y to native Z','blender_version':bpy.app.version_string,'frame':0,'doors':[],'whole_vehicle_acceptance':'16 OPEN','limits':['Axes fitted to actual existing mesh rings, not manufacturer hinge coordinates','Cylinders are authored simplified hinge barrels; pin/leaf construction and mounting remain unverified','Axis offset and orbit diagnose model internal consistency, not penetration or a validated correction','No body/door geometry edited, no native asset saved']}
for hinge_name,side,index in [('cab_pivot_002',-1,0),('cab_pivot_003',-1,1),('cab_pivot_006',1,0),('cab_pivot_007',1,1)]:
 h=bpy.data.objects[hinge_name];base=h.matrix_basis.copy();origin=np.asarray(h.matrix_world.translation,dtype=np.float64);pivot_axis=np.asarray(h.matrix_world,dtype=np.float64)[:3,2];pivot_axis/=np.linalg.norm(pivot_axis)
 barrels=[bpy.data.objects[f'BL_Door_{side}_{index}_hinge_{height}'] for height in [1.47,1.94,2.38]]
 fits=[axis_fit(o) for o in barrels];centers=[np.asarray(x['center']) for x in fits];axis=np.asarray(fits[0]['axis'])
 offsets=[float(np.linalg.norm((c-origin)-np.dot(c-origin,pivot_axis)*pivot_axis)) for c in centers]
 coax=max(float(np.linalg.norm((c-centers[0])-np.dot(c-centers[0],axis)*axis)) for c in centers)
 trials=[]
 try:
  for deg in [0.,15.,45.,75.,99.]:
   h.matrix_basis=base@Matrix.Rotation(-side*math.radians(deg),4,'Z');bpy.context.view_layer.update()
   drift=[]
   for o,c in zip(barrels,centers):
    actual=world_points(o).mean(0);drift.append({'barrel':o.name,'center':actual.tolist(),'center_displacement_from_closed_m':float(np.linalg.norm(actual-c))})
   trials.append({'degrees':deg,'barrels':drift})
 finally:h.matrix_basis=base;bpy.context.view_layer.update()
 report['doors'].append({'hinge':hinge_name,'pivot_origin':origin.tolist(),'pivot_axis':pivot_axis.tolist(),'barrels':fits,'barrel_axes_mutual_offset_m':coax,'pivot_to_barrel_axis_offsets_m':offsets,'barrel_axis_dot_pivot_axis':[float(np.dot(np.asarray(x['axis']),pivot_axis)) for x in fits],'poses':trials})
report['source_sha256_after']=sha(SOURCE);assert report['source_sha256_after']==EXPECTED
(OUT/'axis-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('BARREL_AXIS',[(d['hinge'],d['pivot_to_barrel_axis_offsets_m'],d['barrel_axes_mutual_offset_m']) for d in report['doors']],flush=True)
