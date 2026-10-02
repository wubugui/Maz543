"""One-station source/neutral-parenting diagnostic; records failures before assert.

Two fresh opens of the same locked source, one actual0.731-radian local-Y spin
per case. All186original spin geometries plus the same drum proxy are retained.
Only per-object worst vertices are emitted, never complete mesh arrays.
"""
import argparse,ast,hashlib,json,math,sys,gc
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',required=True);p.add_argument('--recipe',required=True);p.add_argument('--repository',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);base=Path(a.base);out=Path(a.output);recipe=Path(a.recipe);repo=Path(a.repository)
sha=lambda b:hashlib.sha256(b).hexdigest()
RECIPE_SHA='1001ef7de0418e1107461c6b6b661a0bb7d92ef83dbc55f8dc200e877cd7174e'
assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0'
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert sha(base.read_bytes())==a.sha and sha(recipe.read_bytes())==RECIPE_SHA
assert sha((repo/'testcar/lib/maz543.ts').read_bytes())=='d1fdc631ff369ab4f7af1c85e828bbd3d053ff35a2ec5291d0d475bbc68f7059'
tree=ast.parse(recipe.read_bytes());helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'update','ob','points','geometry_axis','reparent'}]
assert {n.name for n in helpers}=={'update','ob','points','geometry_axis','reparent'}
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(recipe),'exec'),globals())
# Reuse the exact executed neutral mutation loop; do not rewrite its semantics.
loops=[n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [x.id for x in n.target.elts]==['i','carrier','spin','brake','upr','king'] and isinstance(n.body[0],ast.Assign) and isinstance(n.body[0].targets[0],ast.Name) and n.body[0].targets[0].id=='drum']
assert len(loops)==1
mutation=compile(ast.Module(body=loops,type_ignores=[]),str(recipe),'exec')
out.mkdir(parents=True,exist_ok=True)
ANG=.731;TOL=.00002;REST_TOL=.000002

def modifiers(o):
 return [{'name':m.name,'type':m.type,'viewport':m.show_viewport,'target':m.target.name if hasattr(m,'target') and m.target else None} for m in o.modifiers]
def measure_case(label,repair):
 global station,rows,detached,new
 bpy.ops.wm.open_mainfile(filepath=str(base));bpy.context.scene.frame_set(0);update();assert bpy.context.evaluated_depsgraph_get().mode=='VIEWPORT'
 i=0;carrier=ob('wheels_pivot_001');spin=ob('wheels_pivot_002');brake=ob('brakes_pivot_001');upr=ob('S543_0_upright');king=ob('S543_0_steering_kingpin');drum=ob('brakes_0003')
 station=[(i,carrier,spin,brake,upr,king)];rows=[];detached=[];new=[]
 if repair:exec(mutation,globals())
 assert spin.rotation_mode=='QUATERNION'
 moving={o.name for o in spin.children_recursive if o.type in {'MESH','CURVE','FONT'}}
 names=sorted(moving|{drum.name});assert len(names)==187 and len(moving)==(187 if repair else 186)
 fixednames=['brakes_0004','brakes_0005','brakes_0006']
 baseline={name:points(ob(name)) for name in names+fixednames};m0=spin.matrix_world.copy();basis=spin.matrix_basis.copy();original_action=spin.animation_data.action;spin.animation_data.action=None
 outside={o.name:o.matrix_world.copy() for o in bpy.data.objects if o.name not in moving and o!=spin}
 expected_delta=m0@Matrix.Rotation(ANG,4,'Y')@m0.inverted();ideal=np.asarray(expected_delta,dtype=float)
 control_violations=[];observations=[];fixed=[];external_changes=[];angle=None;matrix_error=None;actual_delta=Matrix.Identity(4);runtime_error=None
 try:
  spin.matrix_basis=basis@Matrix.Rotation(ANG,4,'Y');update();actual_delta=spin.matrix_world@m0.inverted();actual=np.asarray(actual_delta,dtype=float);angle=actual_delta.to_quaternion().angle;matrix_error=float(np.max(np.abs(actual-ideal)))
  if abs(angle-ANG)>=2e-6 or matrix_error>=2e-6:control_violations.append('Requested matrix rotation was not realized within the fixed tolerance')
  axis=np.asarray((m0.to_3x3()@Vector((0,1,0))).normalized(),dtype=float);centre=np.asarray(m0.translation,dtype=float)
  observations=[]
  for name in names:
   o=ob(name);before,old_tri=baseline[name];after,tri=points(o);member=name in moving;topology=before.shape==after.shape and np.array_equal(tri,old_tri)
   row={'name':name,'type':o.type,'parent':o.parent.name if o.parent else None,'spin_member':member,'vertices_before':len(before),'vertices_after':len(after),'triangle_indices_equal':topology,'modifiers':modifiers(o)}
   if topology:
    proposed=before@actual[:3,:3].T+actual[:3,3];expected=proposed if member else before;errors=np.linalg.norm(after-expected,axis=1);worst=int(np.argmax(errors));displacements=np.linalg.norm(after-before,axis=1);rv=before-centre;rv-=np.outer(rv@axis,axis);radii=np.linalg.norm(rv,axis=1);chord=2*radii*abs(math.sin(ANG/2));trajectory=np.abs(displacements-(chord if member else 0))
    row.update(max_rigid_vertex_error_m=float(errors.max()),vertices_at_or_above20um=int(np.count_nonzero(errors>=TOL)),max_actual_vertex_displacement_m=float(displacements.max()),max_expected_radius_chord_m=float(chord.max()) if member else 0.,max_radius_trajectory_error_m=float(trajectory.max()),hypothetical_spin_max_vertex_error_m=float(np.max(np.linalg.norm(after-proposed,axis=1))),max_ideal_matrix_vertex_error_m=float(np.max(np.linalg.norm(after-(before@ideal[:3,:3].T+ideal[:3,3] if member else before),axis=1))),worst_vertex={'index':worst,'before_world_m':before[worst].tolist(),'after_world_m':after[worst].tolist(),'expected_world_m':expected[worst].tolist(),'error_vector_m':(after[worst]-expected[worst]).tolist(),'radius_m':float(radii[worst]),'actual_displacement_m':float(displacements[worst]),'expected_chord_m':float(chord[worst]) if member else 0.})
   observations.append(row)
  fixed=[]
  for name in fixednames:
   after,t=points(ob(name));before,ot=baseline[name];same=after.shape==before.shape and np.array_equal(t,ot);fixed.append({'name':name,'same_topology':same,'max_vertex_displacement_m':float(np.max(np.linalg.norm(after-before,axis=1))) if same else None})
  if any(not r['same_topology'] or r['max_vertex_displacement_m']>=REST_TOL for r in fixed):control_violations.append('Stationary brake geometry exceeded the fixed2micrometre gate')
  external_changes=[]
  for name,m in outside.items():
   delta=max(abs(ob(name).matrix_world[r][c]-m[r][c]) for r in range(4) for c in range(4))
   if delta>1e-9:external_changes.append({'name':name,'world_matrix_error':delta})
  if external_changes:control_violations.append('Outside-scope object world matrices changed')
 except Exception as exc:
  runtime_error=type(exc).__name__+': '+str(exc);control_violations.append('Measurement interrupted: '+runtime_error)
 finally:
  try:spin.matrix_basis=basis;spin.animation_data.action=original_action;update()
  except Exception as exc:control_violations.append('Restoration assignment/update failed: '+type(exc).__name__+': '+str(exc))
 restore=[]
 for name in names+fixednames:
  try:
   v,t=points(ob(name));old,ot=baseline[name];same=v.shape==old.shape and np.array_equal(t,ot);restore.append({'name':name,'same_topology':same,'max_vertex_error_m':float(np.max(np.linalg.norm(v-old,axis=1))) if same else None})
  except Exception as exc:
   error=type(exc).__name__+': '+str(exc);restore.append({'name':name,'same_topology':False,'max_vertex_error_m':None,'measurement_error':error});control_violations.append('Restoration measurement failed for '+name+': '+error)
 try:restore_matrix_error=max(abs(spin.matrix_world[r][c]-m0[r][c]) for r in range(4) for c in range(4));action_restored=spin.animation_data.action==original_action
 except Exception as exc:
  restore_matrix_error=None;action_restored=False;control_violations.append('Restoration matrix/action read failed: '+type(exc).__name__+': '+str(exc))
 if not all(r['same_topology'] for r in restore):control_violations.append('Restoration changed evaluated topology')
 if any(r['max_vertex_error_m'] is not None and r['max_vertex_error_m']>=REST_TOL for r in restore):control_violations.append('Restoration exceeded the fixed2micrometre vertex gate')
 if restore_matrix_error is None or restore_matrix_error>=1e-9 or not action_restored:control_violations.append('Original spin matrix or action was not restored')
 fails=[r for r in observations if not r['triangle_indices_equal'] or r.get('max_rigid_vertex_error_m',0)>=TOL or r.get('max_radius_trajectory_error_m',0)>=TOL]
 result={'case':label,'fresh_open_source_sha256':a.sha,'requested_radians':ANG,'observed_radians':angle,'matrix_to_requested_transform_max_error':matrix_error,'realized_world_delta':[list(x) for x in actual_delta],'expected_world_delta':[list(x) for x in expected_delta],'spin_rotation_mode':spin.rotation_mode,'observed_objects':len(observations),'spin_geometry_objects':len(moving),'observations':observations,'over_tolerance_names':[r['name'] for r in fails],'max_rigid_vertex_error_m':max((r.get('max_rigid_vertex_error_m',0) for r in observations),default=0.),'max_radius_trajectory_error_m':max((r.get('max_radius_trajectory_error_m',0) for r in observations),default=0.),'stationary_brake':fixed,'external_world_changes':external_changes,'outside_world_matrices_checked':len(outside),'restoration':{'original_action_restored':action_restored,'world_matrix_error':restore_matrix_error,'objects':restore,'max_vertex_error_m':max(r['max_vertex_error_m'] or 0 for r in restore)},'neutral_mutation_rows':rows if repair else []}
 result['control_violations']=control_violations;result['runtime_error']=runtime_error;result['complete_object_measurements']=len(observations)==len(names)
 result['restoration']['max_vertex_error_m']=None if not all(r['same_topology'] for r in restore) else max(r['max_vertex_error_m'] for r in restore)
 (out/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'case':label,'objects':len(observations),'failures':len(fails),'control_violations':control_violations,'max_error_m':result['max_rigid_vertex_error_m']}),flush=True)
 del baseline;gc.collect();return result

source=measure_case('original-source',False)
candidate=measure_case('after-neutral-parenting',True)
by={r['name']:r for r in source['observations']};comparison=[]
for row in candidate['observations']:
 old=by.get(row['name']);
 if old is None:comparison.append({'name':row['name'],'classification':'SOURCE_MEASUREMENT_MISSING'});continue
 old_fail=old['name'] in source['over_tolerance_names'];new_fail=row['name'] in candidate['over_tolerance_names']
 comparison.append({'name':row['name'],'source_spin_member':old['spin_member'],'candidate_spin_member':row['spin_member'],'source_max_rigid_error_m':old.get('max_rigid_vertex_error_m'),'candidate_max_rigid_error_m':row.get('max_rigid_vertex_error_m'),'classification':'FAIL_BOTH_CONFIGURATIONS' if old_fail and new_fail else 'AFTER_PARENTING_ONLY' if new_fail else 'SOURCE_ONLY' if old_fail else 'WITHIN_LIMIT_BOTH','source_actual_displacement_m':old.get('max_actual_vertex_displacement_m'),'candidate_actual_displacement_m':row.get('max_actual_vertex_displacement_m')})
assert sha(base.read_bytes())==a.sha
report={'status':'SPIN_DIAGNOSTIC_FAILURES_RECORDED' if candidate['over_tolerance_names'] else 'SPIN_DIAGNOSTIC_NO_FAILURE_AT_SINGLE_CASE','source_sha256_before':a.sha,'source_sha256_after':sha(base.read_bytes()),'frozen_mutation_recipe_sha256':RECIPE_SHA,'frame':0,'station':0,'radians':ANG,'rigid_and_radius_tolerance_m':TOL,'restoration_tolerance_m':REST_TOL,'comparisons':comparison,'source_failing_names':source['over_tolerance_names'],'candidate_failing_names':candidate['over_tolerance_names'],'no_blend_glb_saved':True,'limits':['Only first wheel at one actual spin angle, source and same neutral-parent recipe after fresh opens.','Failing source and candidate profiles distinguish inheritance from a new regression; they do not certify contact, tyre physics or all other poses.','No objects excluded to reduce failure count, no numerical gate loosened.','The diagnostic reuses the pinned candidate02 mutation recipe and its previously established source-scoped qualification; it does not repeat or broaden a complete dependency certification.','Current0degree camber and full native timeline/exporter/CV/steering/whole-vehicle issues remain open.'],'all16VehicleGates':'OPEN'}
report['source_control_violations']=source['control_violations'];report['candidate_control_violations']=candidate['control_violations']
if source['over_tolerance_names'] and not candidate['over_tolerance_names']:report['status']='SOURCE_FAILURES_NOT_REPRODUCED_AFTER_PARENTING_AT_ONE_POSE'
if source['control_violations'] or candidate['control_violations']:report['status']='SPIN_DIAGNOSTIC_CONTROL_FAILURES_RECORDED'
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
assert not source['control_violations'] and not candidate['control_violations'],'Control/restoration failures recorded before gate assertion'
assert not candidate['over_tolerance_names'],'Diagnostic saved complete per-object evidence before this original20micrometre gate failure'
