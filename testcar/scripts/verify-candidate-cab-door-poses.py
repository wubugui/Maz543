"""Read-only sampled pose regression for the published cab dependency scope.

Samples do not prove continuous clearance or absence of all scene dependencies.
The released button is held at its saved value; its FCurve is recorded unchanged.
"""
import bpy, hashlib, json, math
from pathlib import Path
import numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
INVENTORY=ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
OUT=ROOT/'work/cloud-cab-door-poses-20261001';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
assert sha(SOURCE)==EXPECTED
assert bpy.app.version[:3]==(4,5,13)
scope=json.loads(INVENTORY.read_text());assert scope['source_sha256']==EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
def mesh_snapshot(o):
 ev=o.evaluated_get(dg);me=ev.to_mesh()
 try:
  assert me and len(me.vertices),o.name
  xyz=np.empty(len(me.vertices)*3,dtype=np.float64);me.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
  mat=np.asarray(ev.matrix_world,dtype=np.float64);xyz=xyz@mat[:3,:3].T+mat[:3,3]
  me.calc_loop_triangles();tri=np.empty(len(me.loop_triangles)*3,dtype=np.int32);me.loop_triangles.foreach_get('vertices',tri)
  return xyz,tri
 finally:ev.to_mesh_clear()
def difference(a,b):
 same=a[0].shape==b[0].shape
 return {'vertices_equal':np.array_equal(a[0],b[0]),'triangle_indices_equal':np.array_equal(a[1],b[1]),'same_vertex_count':same,'max_vertex_error_m':float(np.max(np.linalg.norm(a[0]-b[0],axis=1))) if same else None}
def scalar_rna(x):
 result={}
 for p in x.bl_rna.properties:
  if p.identifier=='rna_type':continue
  if p.type in {'BOOLEAN','INT','FLOAT','STRING','ENUM'}:
   v=getattr(x,p.identifier)
   result[p.identifier]=list(v) if getattr(p,'is_array',False) else v
 return result
button=bpy.data.objects['VA180 B4 / BUTTON PRESS REVIEW — travel is fitted']
assert button['press_mm']==0
button_before=button.matrix_basis.copy()
curve=button.animation_data.drivers[0]
driver_detail={'path':curve.data_path,'array_index':curve.array_index,'expression':curve.driver.expression,'held_press_mm':button['press_mm'],'fcurve':scalar_rna(curve),'modifiers':[scalar_rna(m) for m in curve.modifiers]}
fixed=[bpy.data.objects[x['name']] for x in scope['fixed_geometry']]
fixed_baseline={o.name:mesh_snapshot(o) for o in fixed}
report={'status':'IN_PROGRESS','source_sha256':EXPECTED,'inventory_sha256':sha(INVENTORY),'blender_version':bpy.app.version_string,'frame':0,'fixed_count':len(fixed),'button':driver_detail,'poses':[],'limits':['Twenty-four sampled native poses only; no continuous-clearance conclusion','Scope inherited exactly from the published dependency inventory; no other vehicle surfaces implied','Button released and held at zero; button travel not tested','Moving geometry compared to rigid analytic formula with 20 micrometre tolerance; fixed geometry and topology compared exactly'],'whole_vehicle_acceptance':'16 OPEN'}
max_error=0.;violations=[]
for door,side in zip(scope['doors'],[-1,-1,1,1]):
 hinge=bpy.data.objects[door['hinge']];base=hinge.matrix_basis.copy();world=np.asarray(hinge.matrix_world,dtype=np.float64);inv=np.linalg.inv(world)
 parts=[bpy.data.objects[x['name']] for x in door['parts']];snapshots={o.name:mesh_snapshot(o) for o in parts};coeff={}
 for o in parts:
  xyz=snapshots[o.name][0];local=xyz@inv[:3,:3].T+inv[:3,3]
  aa=np.column_stack((local[:,0],local[:,1],np.zeros(len(local))))
  bb=np.column_stack((-local[:,1],local[:,0],np.zeros(len(local))))
  cc=np.column_stack((np.zeros(len(local)),np.zeros(len(local)),local[:,2]))
  coeff[o.name]=(aa@world[:3,:3].T,bb@world[:3,:3].T,cc@world[:3,:3].T+world[:3,3])
 try:
  for degrees in [0.,.731,14.37,48.125,83.61,99.]:
   angle=-side*math.radians(degrees);hinge.matrix_basis=base@Matrix.Rotation(angle,4,'Z');bpy.context.view_layer.update()
   changed=[];moving=[]
   for o in fixed:
    delta=difference(fixed_baseline[o.name],mesh_snapshot(o))
    if not delta['vertices_equal'] or not delta['triangle_indices_equal']:changed.append({'name':o.name,**delta})
   for o in parts:
    xyz,tri=mesh_snapshot(o);a,b,c=coeff[o.name];count=xyz.shape==a.shape
    error=float(np.max(np.linalg.norm(xyz-(c+a*math.cos(angle)+b*math.sin(angle)),axis=1))) if count else None
    topology=np.array_equal(tri,snapshots[o.name][1]);max_error=max(max_error,error or 0)
    moving.append({'name':o.name,'same_vertex_count':count,'triangle_indices_equal':topology,'max_rigid_vertex_error_m':error})
    if not count or not topology or error is None or error>=2e-5:violations.append({'hinge':hinge.name,'degrees':degrees,'part':o.name,'error':error})
   held=button['press_mm']==0 and button.matrix_basis==button_before
   report['poses'].append({'hinge':hinge.name,'degrees':degrees,'fixed_checked':len(fixed),'changed_fixed':changed,'moving':moving,'button_held_exact':held})
   if changed or not held:violations.append({'hinge':hinge.name,'degrees':degrees,'fixed_or_button_changed':True})
   print('POSE',hinge.name,degrees,'fixed_changes',len(changed),'button_held',held,flush=True)
 finally:
  hinge.matrix_basis=base;bpy.context.view_layer.update()
restored=[]
for o in fixed:
 d=difference(fixed_baseline[o.name],mesh_snapshot(o))
 if not d['vertices_equal'] or not d['triangle_indices_equal']:restored.append({'name':o.name,**d})
report.update({'status':'SAMPLED_NATIVE_POSE_REGRESSION_PASS' if not violations and not restored else 'SAMPLED_NATIVE_POSE_REGRESSION_FAIL','violations':violations,'fixed_changes_after_restore':restored,'max_rigid_vertex_error_m':max_error,'source_sha256_after':sha(SOURCE),'source_saved':False,'pose_count':len(report['poses'])})
(OUT/'pose-report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
assert report['source_sha256_after']==EXPECTED
assert not violations and not restored
print('POSE_REGRESSION',report['status'],'max_error_m',max_error,flush=True)
