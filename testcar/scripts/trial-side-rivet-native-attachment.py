"""Replay a limited native attachment correction on a pinned, read-only master.

Only complete numerically covered planar base octagons qualify. Existing head
vertices are translated with Blender's native edit-mode transform; no geometry
is constructed, deleted, hidden, reparented or saved. Run leaves the evaluated
trial in memory for an optional subsequent native inspection render.
"""
import bpy, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from convex_coverage import assess_coverage, InvalidGeometry
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
OUT=ROOT/'work/cloud-side-rivet-attachment-20261001'
INPUTS={
 'components':ROOT/'work/cloud-closed-door-contact-components-20261001/component-report.json',
 'planarity':ROOT/'work/cloud-side-rivet-support-20261001/planarity-summary.json',
 'scope':ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json',
 'reference':ROOT/'reference/cab-sill-step-rivet-source-20261001.json',
}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED_INPUTS={
 'components':'41cf1e4c58ce14973f728f352250d92c2e5c7ff49f188881a380f9ee630758d3',
 'planarity':'9a72b0db422a56a6fce1fcf6bdf714424d20a3820a57e1fcd223e5fc9f349f05',
 'scope':'40e771f244ef6a49f90699f3e60c0e01c6a7885baaea77852fac7d75c891a570',
 'reference':'4da2f23f89058937ddfeecda030c7e51d46f096ca8d9a275b7e49fd94674ade1'}
EXPECTED_HELPER='a7e000b97ab5ee6ae393d4250529bc21f81e3bf705704dd864cf3983c2aa852b'

def array(collection,field,width,dtype):
 a=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(field,a)
 return a.reshape(-1,width) if width>1 else a

def snapshot(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh()
 try:
  xyz=array(m.vertices,'co',3,np.float64);w=np.asarray(e.matrix_world,dtype=np.float64)
  xyz=xyz@w[:3,:3].T+w[:3,3];m.calc_loop_triangles()
  return xyz,array(m.loop_triangles,'vertices',3,np.int32)
 finally:e.to_mesh_clear()

def mesh_signature(m,positions=True):
 # All native meshes: indexed topology, material slots/indices, UVs and positions.
 # Computed normals and editor selection are not identity fields.
 h=hashlib.sha256()
 fields=[(m.edges,'vertices',2,np.int32),(m.loops,'vertex_index',1,np.int32),
         (m.polygons,'loop_start',1,np.int32),(m.polygons,'loop_total',1,np.int32),
         (m.polygons,'material_index',1,np.int32),(m.polygons,'use_smooth',1,np.bool_)]
 if positions:fields.insert(0,(m.vertices,'co',3,np.float32))
 for c,f,w,t in fields:h.update(f.encode());h.update(array(c,f,w,t).tobytes())
 h.update(json.dumps([x.name if x else None for x in m.materials]).encode())
 for uv in m.uv_layers:
  h.update(uv.name.encode());h.update(array(uv.data,'uv',2,np.float32).tobytes())
 return h.hexdigest()

def object_state(o):
 return {'basis':[list(r) for r in o.matrix_basis], 'world':[list(r) for r in o.matrix_world],
         'parent':o.parent.name if o.parent else None,'data':o.data.name if o.data else None,
         'hide_viewport':o.hide_viewport,'hide_render':o.hide_render,'hide_local':o.hide_get()}

def overlaps(a,b):
 if np.any(a[0].max(0)<b[0].min(0)) or np.any(b[0].max(0)<a[0].min(0)):return []
 av=BVHTree.FromPolygons(a[0].tolist(),a[1].tolist(),all_triangles=True,epsilon=0.)
 bv=BVHTree.FromPolygons(b[0].tolist(),b[1].tolist(),all_triangles=True,epsilon=0.)
 return sorted([list(x) for x in av.overlap(bv)])

def run(out=OUT):
 out.mkdir(parents=True,exist_ok=True)
 # Invalidate a previous success before any operation that may fail.
 (out/'attachment-report.json').write_text(json.dumps({'status':'IN_PROGRESS_NOT_ACCEPTED','source_saved':False})+'\n')
 assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
 assert {k:sha(p) for k,p in INPUTS.items()}==EXPECTED_INPUTS
 assert sha(ROOT/'scripts/convex_coverage.py')==EXPECTED_HELPER
 data={k:json.loads(p.read_bytes()) for k,p in INPUTS.items()}
 assert data['components']['source_sha256']==data['scope']['source_sha256']==EXPECTED
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get();assert dg.mode=='VIEWPORT'
 assert bpy.context.object is None or bpy.context.object.mode=='OBJECT'
 states={o.name:object_state(o) for o in bpy.data.objects}
 targets=[f'BL_Cab_{s}_side_rivets' for s in [-1,1]]
 target_data={bpy.data.objects[n].data.name for n in targets}
 original_meshes={m.name:mesh_signature(m) for m in bpy.data.meshes}
 static_ids=set(original_meshes)-target_data
 source_signatures={n:mesh_signature(bpy.data.objects[n].data,False) for n in targets}
 selected_before=[o.name for o in bpy.context.selected_objects]
 active_before=bpy.context.view_layer.objects.active
 door_names=[p['name'] for d in data['scope']['doors'] for p in d['parts']]
 assert len(door_names)==44
 door_before={n:snapshot(bpy.data.objects[n],dg) for n in door_names}
 closed_before={(n,t):overlaps(door_before[n],snapshot(bpy.data.objects[t],dg)) for n in door_names for t in targets}
 retained_before={}
 for c in data['components']['contacts']:
  key=(c['moving'],c['fixed']);v=overlaps(snapshot(bpy.data.objects[key[0]],dg),snapshot(bpy.data.objects[key[1]],dg))
  assert len(v)==c['triangle_pair_count'];retained_before[key]=v
 report={'status':'IN_PROGRESS','source_sha256':EXPECTED,'input_sha256':{k:sha(p) for k,p in INPUTS.items()},
  'helper_sha256':sha(ROOT/'scripts/convex_coverage.py'),'blender_version':bpy.app.version_string,
  'frame':0,'depsgraph_mode':dg.mode,'source_saved':False,'native_asset_published':False,
  'native_operation':'bpy.ops.transform.translate in EDIT mode, GLOBAL Y, selected complete existing head components',
  'area_tolerance_m2':1e-14,'plane_coplanarity_tolerance_m':1e-9,'post_transform_tolerance_m':5e-7,
  'whole_vehicle_acceptance':'16 OPEN','sides':[],
  'limits':['An in-memory fitted attachment correction, not a saved/published native asset or runtime change',
   'Full octagonal footprint coverage is binary64 numerical polygon subtraction, not a formal roundoff proof',
   'Existing fastener head form/count/spacing is retained; shank, holes, strength, manufacturer dimensions and target batch remain unverified',
   'Four bevel-crossing heads and six heads over rear door openings stay unchanged; known closed contacts are retained',
   'No door sweep clearance, all-body collision, render or browser acceptance follows from this trial']}
 # Evaluate both sides and write coverage BEFORE mutating any model data.
 prepared=[]
 for side in [-1,1]:
  name=f'BL_Cab_{side}_side_rivets';skin_name=f'BL_Cab_{side}_side_monocoque';o=bpy.data.objects[name]
  assert not o.modifiers and not o.constraints and o.data.users==1 and not o.data.shape_keys
  xyz,tri=snapshot(o,dg);skin=snapshot(bpy.data.objects[skin_name],dg);outward=-side
  local=array(o.data.vertices,'co',3,np.float64);w=np.asarray(o.matrix_world,dtype=np.float64)
  assert np.array_equal(local@w[:3,:3].T+w[:3,3],xyz)
  groups=data['components']['fixed_objects'][name]['exact_coordinate_components']
  assert len(groups)==75 and len(xyz)==1800 and len(tri)==2850
  assert sorted(v for g in groups for v in g['vertices'])==list(range(1800))
  axis=outward*skin[0][:,1];plane=float(axis.max());skin_tri=skin[0][skin[1]]
  planar=np.max(np.abs(outward*skin_tri[:,:,1]-plane),axis=1)<=1e-9
  indices=np.flatnonzero(planar);projected=skin_tri[indices][:,:,[0,2]]
  assert len(indices)>0
  prior=next(s for s in data['planarity']['sides'] if s['side']==side)
  candidates=set(prior['flat_plane_nine_sample_candidates']);assert len(candidates)==70
  rows=[];qualify=[]
  for group in groups:
   component=group['component'];ids=group['vertices'];assert len(ids)==24 and len(group['triangles'])==38
   points=xyz[ids];head_axis=outward*points[:,1];base=points[np.abs(head_axis-head_axis.min())<1e-7]
   assert len(base)==8
   fp=base[:,[0,2]];center=fp.mean(0);angles=np.arctan2(fp[:,1]-center[1],fp[:,0]-center[0]);fp=fp[np.argsort(angles)]
   # Broad-phase keeps the exact full skin triangle IDs. It cannot fill a hole.
   near=(projected.max(1)>=fp.min(0)).all(1)&(projected.min(1)<=fp.max(0)).all(1)
   ids_near=indices[near];result=None;error=None
   assert len(ids_near)<=64, 'Local triangle budget exceeded; no partial acceptance'
   try:result=assess_coverage(fp.tolist(),projected[near].tolist(),area_tolerance=1e-14,max_triangles=64,max_fragments=4096)
   except InvalidGeometry as exc:error=str(exc)
   passed=component in candidates and result is not None and result['numerical_coverage_pass'] is True
   row={'component':component,'prior_flat_candidate':component in candidates,'base_octagon_xz_m':fp.tolist(),
    'source_skin_triangle_indices':ids_near.tolist(),'coverage':result,'invalid_geometry':error,
    'qualifies_for_native_translation':passed,'signed_outward_base_m':float(head_axis.min()),
    'target_outward_plane_m':plane,'inward_translation_m':float(head_axis.min()-plane) if passed else None}
   rows.append(row)
   if passed:qualify.extend(ids)
  coverage={'side':side,'object':name,'skin_object':skin_name,'outer_plane_m':plane,
   'total_outer_plane_triangles':len(indices),'rows':rows}
  (out/f'coverage_{side}.json').write_text(json.dumps(coverage,ensure_ascii=False,separators=(',',':'))+'\n')
  ready=[r for r in rows if r['qualifies_for_native_translation']]
  # This limited replay requires the diagnosed set exactly; no silent partial repair.
  assert len(ready)==70 and {r['component'] for r in ready}==candidates, 'Coverage differs; leave all geometry unchanged'
  deltas={r['inward_translation_m'] for r in ready};assert len(deltas)==1
  distance=deltas.pop();assert 0.0119<distance<0.0121
  prepared.append({'side':side,'object':o,'xyz':xyz,'tri':tri,'groups':groups,'selected':set(qualify),
                   'distance':distance,'plane':plane,'outward':outward,'ready':ready,'rows':rows})
 print('COVERAGE_READY',[(p['side'],len(p['ready'])) for p in prepared],flush=True)
 for p in prepared:
  o=p['object'];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  assert not o.hide_get() and not o.hide_viewport
  selected=p['selected'];m=o.data
  for v in m.vertices:v.select=v.index in selected
  for e in m.edges:e.select=all(v in selected for v in e.vertices)
  for f in m.polygons:f.select=all(v in selected for v in f.vertices)
  bpy.context.tool_settings.mesh_select_mode=(True,False,False)
  bpy.ops.object.mode_set(mode='EDIT')
  try:
   result=bpy.ops.transform.translate(value=(0.,-p['outward']*p['distance'],0.),orient_type='GLOBAL',
    constraint_axis=(False,True,False),use_proportional_edit=False,mirror=False)
   assert result=={'FINISHED'}
  finally:bpy.ops.object.mode_set(mode='OBJECT')
  bpy.context.view_layer.update();after=snapshot(o,dg)
  assert np.array_equal(after[1],p['tri']) and mesh_signature(m,False)==source_signatures[o.name]
  ids=sorted(selected);skipped=sorted(set(range(len(after[0])))-selected)
  assert np.array_equal(after[0][skipped],p['xyz'][skipped]), 'Unselected original head changed'
  expected=p['xyz'][ids]+[0.,-p['outward']*p['distance'],0.]
  err=float(np.max(np.linalg.norm(after[0][ids]-expected,axis=1)));assert err<5e-7
  base_errors=[];min_offsets=[]
  for r in p['ready']:
   g=p['groups'][r['component']];before=p['xyz'][g['vertices']];now=after[0][g['vertices']]
   base=np.abs(p['outward']*before[:,1]-r['signed_outward_base_m'])<1e-7
   base_errors.extend((p['outward']*now[base,1]-p['plane']).tolist())
   min_offsets.append(float((p['outward']*now[:,1]-p['plane']).min()))
  assert max(map(abs,base_errors))<5e-7 and min(min_offsets)>-5e-7
  report['sides'].append({'side':p['side'],'object':o.name,'moved_components':[r['component'] for r in p['ready']],
   'unchanged_components':[r['component'] for r in p['rows'] if not r['qualifies_for_native_translation']],
   'moved_vertices':len(ids),'unchanged_vertices':len(skipped),'inward_translation_m':p['distance'],
   'maximum_native_translation_error_m':err,'maximum_base_plane_absolute_error_m':max(map(abs,base_errors)),
   'minimum_outward_vertex_offset_m':min(min_offsets),'topology_uv_material_signature_exact':True,
   'coverage_file':f"coverage_{p['side']}.json",'coverage_sha256':sha(out/f"coverage_{p['side']}.json")})
  print('NATIVE_ATTACHMENT',p['side'],len(p['ready']),'inward',p['distance'],'base_error',max(map(abs,base_errors)),flush=True)
 bpy.ops.object.select_all(action='DESELECT')
 for name in selected_before:bpy.data.objects[name].select_set(True)
 bpy.context.view_layer.objects.active=active_before
 bpy.context.view_layer.update()
 assert set(original_meshes)=={m.name for m in bpy.data.meshes}
 unchanged_meshes=[n for n in static_ids if mesh_signature(bpy.data.meshes[n])==original_meshes[n]]
 assert len(unchanged_meshes)==len(static_ids),'Unrelated native mesh changed'
 assert states=={o.name:object_state(o) for o in bpy.data.objects},'Object identity/transform/visibility changed'
 for n,before in door_before.items():
  after=snapshot(bpy.data.objects[n],dg);assert all(np.array_equal(a,b) for a,b in zip(before,after)),n
 closed_after={(n,t):overlaps(snapshot(bpy.data.objects[n],dg),snapshot(bpy.data.objects[t],dg)) for n in door_names for t in targets}
 assert closed_after==closed_before,'Door contact set changed; investigate, do not call zero clearance'
 for key,hits in retained_before.items():assert overlaps(snapshot(bpy.data.objects[key[0]],dg),snapshot(bpy.data.objects[key[1]],dg))==hits
 report.update({'status':'FITTED_NATIVE_HEAD_ATTACHMENT_TRIAL_PASS','geometry_modified_in_memory':True,
  'native_object_states_exact':len(states),'unmodified_native_mesh_signatures_exact':len(unchanged_meshes),
  'closed_door_evaluated_meshes_exact':44,'retained_closed_surface_pairs':len(retained_before),
  'retained_closed_triangle_pairs':sum(len(h) for h in retained_before.values()),
  'door_vs_target_object_pairs_checked':len(closed_before),'door_vs_target_triangle_pairs_exact':sum(len(h) for h in closed_before.values()),
  'source_sha256_after':sha(SOURCE)})
 assert report['source_sha256_after']==EXPECTED and report['retained_closed_surface_pairs']==6
 (out/'attachment-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('ATTACHMENT_FINISHED',report['status'],'unmodified_native_meshes',len(unchanged_meshes),'objects',len(states),'retained_contacts',len(retained_before),flush=True)
 return report

if __name__=='__main__':run()
