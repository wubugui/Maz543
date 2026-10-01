"""Compare three in-memory steering poses without selecting a factory angle.

The original tube/axis disagreement is measured from actual native geometry.
Both coaxial alternatives retain the legacy pitch magnitude and bottom height;
neither establishes original installation dimensions or operating mechanics.
"""
import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-cab-panel-fit-20261001/iteration-02/MAZ543A_Master.blend'
OUT=ROOT/'outputs/cloud-steering-axis-probe-20261001';OUT.mkdir(exist_ok=True)
assert not (OUT/'axis-probe.json').exists()
sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert sha=='637eb679d3e86ac0d2e44b166b24b528cc7262c449d967d5635a3faedca0ae02'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
wheel=bpy.data.objects['cab_pivot_004'];column=bpy.data.objects['BL_Left_driver_steering_column_retained']
old_wheel=wheel.matrix_world.copy();old_column=column.matrix_world.copy()
moving=[column]+[o for o in wheel.children_recursive if o.type=='MESH'];names={o.name for o in moving};assert len(moving)==4
def points(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=[e.matrix_world@p.co for p in m.vertices];e.to_mesh_clear();return v
ring=np.array(points(bpy.data.objects['cab_0029']))
eigenvalues,eigenvectors=np.linalg.eigh(np.cov(ring.T));axis=Vector(eigenvectors[:,0]);axis*=1 if axis.z>0 else -1
assert eigenvalues[0]<eigenvalues[1]*.02
cp=points(column);bottom=min(v.z for v in cp);top=max(v.z for v in cp);old_length=top-bottom
old_center=Vector(tuple((min(v[k] for v in cp)+max(v[k] for v in cp))/2 for k in range(3)))
ev,vec=np.linalg.eigh(np.cov(np.array(cp).T));column_axis=Vector(vec[:,-1]);column_axis*=1 if column_axis.z>0 else -1
assert (column_axis-Vector((0,0,1))).length<1e-5
centre=old_wheel.translation.copy();original_angle=math.degrees(axis.angle(column_axis))
old_top=old_center+column_axis*old_length/2;d=old_top-centre;original_offset=(d-axis*d.dot(axis)).length
back_axis=Vector((-axis.x,axis.y,axis.z)).normalized()
def bounds(vs):return [[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]
def near(a,b):return all(a[k][0]<=b[k][1] and b[k][0]<=a[k][1] for k in range(3))
def tree(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();vs=[e.matrix_world@v.co for v in m.vertices];ts=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear()
 return BVHTree.FromPolygons(vs,ts,all_triangles=True),bounds(vs)
results=[]
for label,target_axis in [('legacy',None),('coaxial_legacy_lean',axis),('coaxial_opposite_lean',back_axis)]:
 wheel.matrix_world=old_wheel;column.matrix_world=old_column
 if target_axis is not None:
  r=axis.rotation_difference(target_axis).to_matrix().to_4x4()
  wheel.matrix_world=Matrix.Translation(centre)@r@Matrix.Translation(-centre)@old_wheel
  # Retain the old bottom Z and nominal 20 mm hub-to-tube-end offset as FITTED.
  end=centre-target_axis*.020;start=centre+target_axis*((bottom-centre.z)/target_axis.z)
  new_length=(end-start).length;new_center=(end+start)/2
  rotation=column_axis.rotation_difference(target_axis).to_matrix().to_4x4()
  scale=Matrix.Diagonal((1,1,new_length/old_length,1))
  column.matrix_world=Matrix.Translation(new_center)@rotation@scale@Matrix.Translation(-old_center)@old_column
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();trees={o.name:tree(o,dg) for o in moving};hits=[];tested=0
 for fixed in bpy.context.scene.objects:
  if fixed.type!='MESH' or fixed.hide_render or fixed.name in names:continue
  e=fixed.evaluated_get(dg);box=bounds([e.matrix_world@Vector(v) for v in e.bound_box]);candidates=[n for n,(_,b) in trees.items() if near(b,box)]
  if not candidates:continue
  ft,_=tree(fixed,dg)
  for n in candidates:
   tested+=1;pairs=trees[n][0].overlap(ft)
   if pairs:hits.append({'moving':n,'fixed':fixed.name,'triangle_pairs':len(pairs)})
 row={'pose':label,'wheel_matrix':[list(r) for r in wheel.matrix_world],'column_matrix':[list(r) for r in column.matrix_world],'target_axis':list(target_axis) if target_axis is not None else None,'narrow_phase_pairs':tested,'surface_intersections':hits}
 results.append(row);print('STEERING_AXIS_PROBE',label,'pairs',tested,'intersections',len(hits),flush=True)
 (OUT/'axis-probe-progress.json').write_text(json.dumps(results,indent=2)+'\n')
wheel.matrix_world=old_wheel;column.matrix_world=old_column;bpy.context.view_layer.update()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==sha
report={'source_sha256':sha,'native_ring_axis':list(axis),'native_column_axis':list(column_axis),'legacy_axis_disagreement_degrees':original_angle,'legacy_top_offset_from_ring_axis_m':original_offset,'source_saved_or_modified':False,'poses':results,'limits':['Both coaxial hypotheses inherit uncalibrated angle magnitude, bottom Z, tube radius and end offset','Opposite lean is a qualitative photo hypothesis, not a confirmed MAZ543A factory datum','Rest surface intersections only; no containment or continuous sweep','Steering gearbox, internal shaft, mounting and actual connection remain unresolved'],'all16VehicleGates':'OPEN'}
(OUT/'axis-probe.json').write_text(json.dumps(report,indent=2)+'\n')
