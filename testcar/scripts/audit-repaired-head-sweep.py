"""Before/after conditional frozen sweep for the exact published 140-head repair.

Run with Blender 4.5.13, --python-exit-code 1, -- --repo REPO --out OUTSIDE_REPO.
No native door motion, saved blend, rendering, export, or repo write occurs.
"""
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
import bpy
import numpy as np

args = argparse.ArgumentParser()
args.add_argument('--repo', type=Path, required=True)
args.add_argument('--out', type=Path, required=True)
a = args.parse_args(sys.argv[sys.argv.index('--') + 1:])
REPO, OUT = a.repo.resolve(), a.out.resolve()
assert not OUT.is_relative_to(REPO), 'Evidence must stay outside the repository'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT/'sweep-report.json'
REPORT.write_text(json.dumps({'status':'IN_PROGRESS_NOT_ACCEPTED','source_saved':False})+'\n')
ROOT = REPO/'testcar'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE = ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
EXPECTED_SOURCE = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
PINNED = {
 'repair':('scripts/trial-side-rivet-native-attachment.py','ec3237350de3f7443048993f56e8945b6a1b51e3a1d9285fae10d15dd2b4ec01'),
 'bounds':('scripts/door_interval_bounds.py','b62f1fa79ba988a3874370c0d64565c3c0f023b2c6ba6fb197bb686cd3c41d16'),
 'doors':('work/cloud-cab-door-dependencies-20261001/inventory.json','40e771f244ef6a49f90699f3e60c0e01c6a7885baaea77852fac7d75c891a570'),
 'components':('work/cloud-closed-door-contact-components-20261001/component-report.json','41cf1e4c58ce14973f728f352250d92c2e5c7ff49f188881a380f9ee630758d3'),
 'axis':('work/cloud-door-barrel-axis-20261001/axis-report.json','523f0a0936a30042411db574a9a507b505bd0b5b85770d39f6618095895dcd27'),
 'trial':('work/cloud-door-barrel-motion-trial-20261001/trial-report.json','ce03060e60a7cb0749c18452bb623311383a896b6923ec5941724d3387bc4dd9'),
 'published_repair_report':('work/cloud-side-rivet-attachment-20261001/attachment-report.json','1b1ec3f3e8c8a0a03fdfef16888644b511d73812be0c7d27e26e4d073f7a5131'),
}
assert bpy.app.version[:3] == (4,5,13) and sha(SOURCE) == EXPECTED_SOURCE
for key,(path,digest) in PINNED.items():
 assert sha(ROOT/path) == digest, (key,'Input changed')
data = {k:json.loads((ROOT/p).read_bytes()) for k,(p,h) in PINNED.items() if p.endswith('.json')}
assert all(d['source_sha256'] == EXPECTED_SOURCE for d in data.values())
assert data['trial']['source_sha256_after'] == EXPECTED_SOURCE
assert data['trial']['axis_report_sha256'] == PINNED['axis'][1]
assert not data['trial']['violations'] and data['trial']['all_44_closed_parts_restored_exact']
assert data['trial']['all_stationary_matrices_restored_exact']
assert data['published_repair_report']['status'] == 'FITTED_NATIVE_HEAD_ATTACHMENT_TRIAL_PASS'
sys.dont_write_bytecode = True
sys.path.insert(0,str(ROOT/'scripts'))
from door_interval_bounds import certify_pair, swept_bounds, separation, controls
spec = importlib.util.spec_from_file_location('published_attachment_replay', ROOT/PINNED['repair'][0])
repair = importlib.util.module_from_spec(spec); spec.loader.exec_module(repair)
PADDING = 2e-5
SIDES = {'cab_pivot_002':-1,'cab_pivot_003':-1,'cab_pivot_006':1,'cab_pivot_007':1}
assert [d['hinge'] for d in data['doors']['doors']] == list(SIDES)
assert [d['hinge'] for d in data['trial']['doors']] == list(SIDES)
DOOR_NAMES = [p['name'] for d in data['doors']['doors'] for p in d['parts']]
assert len(DOOR_NAMES) == len(set(DOOR_NAMES)) == 44
for d in data['doors']['doors']:
 assert len(d['parts']) == 11
 assert all(p['name'].startswith(f"BL_Door_{SIDES[d['hinge']]}_") for p in d['parts'])
TARGETS = ['BL_Cab_-1_side_rivets','BL_Cab_1_side_rivets']


def digest_snapshot(s):
 h = hashlib.sha256()
 for v in s: h.update(str(v.shape).encode()); h.update(str(v.dtype).encode()); h.update(v.tobytes())
 return h.hexdigest()


def load_closed():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
 dg = bpy.context.evaluated_depsgraph_get(); assert dg.mode == 'VIEWPORT'
 return dg


def snapshot_named(names,dg):
 return {n:repair.snapshot(bpy.data.objects[n],dg) for n in names}


def check_partition(result,lo,hi):
 intervals = result['clear_intervals'] + result['unresolved_intervals']
 intervals = sorted(intervals,key=lambda x:(x['lo'],x['hi']))
 assert intervals and intervals[0]['lo'] == lo and intervals[-1]['hi'] == hi
 assert all(x['lo'] < x['hi'] for x in intervals)
 assert all(x['hi'] == y['lo'] for x,y in zip(intervals,intervals[1:]))
 assert all(x['padded_gap_m'] > 0 for x in result['clear_intervals'])
 assert result['cells'] <= 127
 assert (result['status'] == 'UNRESOLVED') == bool(result['unresolved_intervals'])


def check_pair_set(rows,expected):
 keys = [(r['moving_index'],r['head_index']) for r in rows]
 assert len(keys) == len(expected) and len(set(keys)) == len(keys) and set(keys) == expected


def expect_rejection(f):
 try: f()
 except AssertionError: return True
 raise AssertionError('Negative control was accepted')


synthetic = controls()
# The exact production budget must also retain deliberately overlapping boxes.
ca=np.array([[1.,0.,0.]])
cb=np.array([[0.,1.,0.]])
cc=np.zeros((1,3))
fixed=(np.array([-.1,-.1,-.1]),np.array([1.1,1.1,.1]))
r=certify_pair(ca,cb,cc,fixed,0.,math.pi/2,max_depth=6,max_cells=127,padding=PADDING)
check_partition(r,0.,math.pi/2)
assert r['status']=='UNRESOLVED' and r['cells']==127 and len(r['unresolved_intervals'])==64
synthetic['exact_budget_overlapping_bounds_retained']={'cells':r['cells'],'unresolved_intervals':len(r['unresolved_intervals'])}
# Demonstrate that count alone cannot admit incomplete or duplicated cross-side coverage.
e={(i,j) for i in range(11) for j in range(140)}
control_rows=[{'moving_index':i,'head_index':j} for i,j in sorted(e)]
check_pair_set(control_rows,e)
synthetic['missing_pair_rejected']=expect_rejection(lambda:check_pair_set(control_rows[:-1],e))
synthetic['duplicate_replacing_pair_rejected']=expect_rejection(lambda:check_pair_set(control_rows[:-1]+[control_rows[0]],e))
synthetic['opposite_side_omission_rejected']=expect_rejection(lambda:check_pair_set([r for r in control_rows if r['head_index']<70],e))

# Capture the actual original closed snapshot independently, before invoking the unmodified replay.
dg=load_closed()
before=snapshot_named(DOOR_NAMES+TARGETS,dg)
worlds={n:np.asarray(bpy.data.objects[n].matrix_world,dtype=np.float64).copy() for n in SIDES}
bases={n:np.asarray(bpy.data.objects[n].matrix_basis,dtype=np.float64).copy() for n in SIDES}
for d in data['doors']['doors']:
 assert np.array_equal(bases[d['hinge']],np.asarray(d['matrix_basis']))
print('BEFORE_CLOSED_SNAPSHOT',len(DOOR_NAMES),'door_parts',flush=True)
replay=repair.run(out=OUT/'native-repair-replay')
assert replay == data['published_repair_report'], 'Exact published repair evidence differs'
dg=bpy.context.evaluated_depsgraph_get(); assert dg.mode=='VIEWPORT'
after=snapshot_named(DOOR_NAMES+TARGETS,dg)
assert all(all(np.array_equal(x,y) for x,y in zip(before[n],after[n])) for n in DOOR_NAMES)
assert all(np.array_equal(worlds[n],np.asarray(bpy.data.objects[n].matrix_world)) for n in SIDES)
assert all(np.array_equal(bases[n],np.asarray(bpy.data.objects[n].matrix_basis)) for n in SIDES)

# Component identifiers come from the pinned exact-coordinate component report.
# The moved set comes from the actual replay and equals its published result.
heads=[]
for side_report in replay['sides']:
 name=side_report['object']; side=side_report['side']
 groups=data['components']['fixed_objects'][name]['exact_coordinate_components']
 assert len(groups)==75 and len(side_report['moved_components'])==70
 assert sorted(v for g in groups for v in g['vertices'])==list(range(1800))
 assert sorted(t for g in groups for t in g['triangles'])==list(range(2850))
 assert np.array_equal(before[name][1],after[name][1])
 for g in groups:
  component=g['component']; ids=g['vertices']; tids=g['triangles']
  assert len(ids)==len(set(ids))==24 and len(tids)==len(set(tids))==38
  assert set(before[name][1][tids].ravel())==set(ids)
  moved=component in side_report['moved_components']
  if not moved:
   assert np.array_equal(before[name][0][ids],after[name][0][ids])
   continue
  assert not np.array_equal(before[name][0][ids],after[name][0][ids])
  row={'head_index':len(heads),'object':name,'side':side,'component':component,
       'vertex_indices':ids,'triangle_indices':tids,'bounds':{}}
  for label,snap in [('before',before),('after',after)]:
   pts=snap[name][0][ids]; box=(pts.min(0)-PADDING,pts.max(0)+PADDING)
   assert (pts>=box[0]).all() and (pts<=box[1]).all()
   row['bounds'][label]=[box[0].tolist(),box[1].tolist()]
  heads.append(row)
assert len(heads)==140 and len({(r['object'],r['component']) for r in heads})==140
assert [sum(r['side']==s for r in heads) for s in [-1,1]]==[70,70]

report={'status':'IN_PROGRESS_NOT_ACCEPTED','source_sha256':EXPECTED_SOURCE,
 'script_sha256':sha(Path(__file__)),
 'inputs':{k:{'path':'testcar/'+p,'sha256':h} for k,(p,h) in PINNED.items()},
 'blender_version':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),
 'frame':0,'depsgraph_mode':dg.mode,'source_saved':False,'native_doors_rotated':False,
 'motion_formula':'world @ (p + Rz(theta) @ (local-p)); theta=-side*radians(degrees), degrees in [0,99]',
 'coefficient_formula':'rel=local-p; A=W3@(rel.x,rel.y,0); B=W3@(-rel.y,rel.x,0); C=W3@(p.x,p.y,local.z)+W.translation',
 'motion_axis_source':'Exact measured_local_axis_point from pinned published trial-report.json, independently recomputed from its pinned barrel-axis report',
 'bounds_method':'Float64 endpoint values plus included sine/cosine critical angles for every vertex coordinate; triangle interiors are convex combinations at a common angle',
 'padding_m_per_moving_and_fixed_box':PADDING,'max_depth':6,'max_cells_per_pair':127,
 'doors_unchanged_closed_snapshot_and_triangles':44,'hinge_closed_world_and_basis_matrices_unchanged':4,
 'native_replay_report':'native-repair-replay/attachment-report.json',
 'native_replay_report_sha256':sha(OUT/'native-repair-replay/attachment-report.json'),
 'native_replay_equals_published_report':True,
 'snapshot_hashes':{n:{'before':digest_snapshot(before[n]),'after':digest_snapshot(after[n])} for n in DOOR_NAMES+TARGETS},
 'modified_heads':heads,'synthetic_controls':synthetic,'doors':[],
 'whole_vehicle_acceptance':'16 OPEN',
 'limits':[
  'Only 44 selected door parts versus 140 actually repaired fixed head components, including every cross-side combination; 6160 pairs per snapshot',
  'Frozen frame-zero evaluated meshes under the measured barrel-axis trial formula; not stored old-pivot motion',
  '20 micrometre padding is an adopted numerical safeguard, not a proved whole-angle Blender floating-point error bound',
  'No native continuous dependency or actual pose regression is newly established by this snapshot calculation',
  'Overlapping swept bounds remain unresolved, not collisions, including budget exhaustion; separation gaps are sufficient axis-aligned bounds, not shortest surface distances',
  'Ten untouched heads and six retained closed contact object pairs remain outside this comparison; replay preserves their existing state',
  'No claim for web/Draco, all-vehicle collision, other moving doors, factory geometry, native saved asset, or acceptance'
 ]}
all_transitions=[]
for door in data['doors']['doors']:
 name=door['hinge']; side=SIDES[name]; w=worlds[name]; inv=np.linalg.inv(w)
 trial=next(d for d in data['trial']['doors'] if d['hinge']==name)
 measured=next(d for d in data['axis']['doors'] if d['hinge']==name)
 center=np.mean([x['center'] for x in measured['barrels']],axis=0)
 derived=inv[:3,:3]@center+inv[:3,3]; derived[2]=0.
 p=np.asarray(trial['measured_local_axis_point'],dtype=np.float64)
 assert np.array_equal(p,derived)
 assert measured['barrel_axes_mutual_offset_m']<1e-6
 assert all(abs(x-1)<1e-8 for x in measured['barrel_axis_dot_pivot_axis'])
 assert np.array_equal(p[2:],np.zeros(1)) and np.linalg.norm(p[:2])>.01
 signed_end=-side*math.radians(99.); lo,hi=sorted((0.,signed_end))
 part_names=[x['name'] for x in door['parts']]
 rows=[]; closed_error=0.; direct_error=0.; count_before=count_after=0
 for mi,n in enumerate(part_names):
  xyz=before[n][0]
  assert len(xyz)==door['parts'][mi]['vertices']
  assert len(before[n][1])==door['parts'][mi]['triangles']
  local=xyz@inv[:3,:3].T+inv[:3,3]; rel=local-p
  aa=np.column_stack((rel[:,0],rel[:,1],np.zeros(len(rel))))@w[:3,:3].T
  bb=np.column_stack((-rel[:,1],rel[:,0],np.zeros(len(rel))))@w[:3,:3].T
  cc=np.column_stack((np.full(len(rel),p[0]),np.full(len(rel),p[1]),local[:,2]))@w[:3,:3].T+w[:3,3]
  closed_error=max(closed_error,float(np.max(np.linalg.norm(aa+cc-xyz,axis=1))))
  for deg in [0.,.731,14.37,48.125,83.61,99.]:
   theta=-side*math.radians(deg); co,si=math.cos(theta),math.sin(theta)
   rz=np.array([[co,-si,0.],[si,co,0.],[0.,0.,1.]])
   direct=(p+(local-p)@rz.T)@w[:3,:3].T+w[:3,3]
   poly=cc+aa*co+bb*si
   direct_error=max(direct_error,float(np.max(np.linalg.norm(poly-direct,axis=1))))
  for head in heads:
   row={'moving_index':mi,'head_index':head['head_index']}
   for label in ['before','after']:
    fixed=tuple(np.asarray(x,dtype=np.float64) for x in head['bounds'][label])
    result=certify_pair(aa,bb,cc,fixed,lo,hi,max_depth=6,max_cells=127,padding=PADDING)
    check_partition(result,lo,hi)
    row[label]=result
   old=bool(row['before']['unresolved_intervals']); new=bool(row['after']['unresolved_intervals'])
   count_before+=old; count_after+=new
   row['newly_unresolved']=not old and new
   if old or new:
    all_transitions.append({'hinge':name,'moving':n,'head_object':head['object'],'head_component':head['component'],'before_unresolved':old,'after_unresolved':new,'newly_unresolved':not old and new})
   rows.append(row)
 assert closed_error<1e-12 and direct_error<1e-12
 check_pair_set(rows,e)
 detail={'hinge':name,'side':side,'angle_degrees':[0.,99.],'signed_angle_radians_at_99_degrees':signed_end,
  'closed_angle_radians':[lo,hi],'measured_local_axis_point':p.tolist(),'closed_hinge_world_matrix':w.tolist(),
  'moving_names':part_names,'head_identity_table':'sweep-report.json modified_heads',
  'pairs':rows,'coverage':{'moving_parts':11,'fixed_modified_heads':140,'cartesian_pairs':1540,'same_side_pairs':770,'opposite_side_pairs':770},
  'closed_coefficient_max_error_m':closed_error,'coefficient_vs_direct_formula_max_error_m':direct_error,
  'formula_samples_are_implementation_controls_not_continuous_native_validation':True}
 path=OUT/(name+'.json'); path.write_text(json.dumps(detail,separators=(',',':'))+'\n')
 entry={'hinge':name,'pairs':len(rows),'before_separated':len(rows)-count_before,'before_unresolved':count_before,
  'after_separated':len(rows)-count_after,'after_unresolved':count_after,
  'newly_unresolved':sum(r['newly_unresolved'] for r in rows),
  'max_cells_before':max(r['before']['cells'] for r in rows),'max_cells_after':max(r['after']['cells'] for r in rows),
  'minimum_proved_padded_gap_before_m':min((x['padded_gap_m'] for r in rows for x in r['before']['clear_intervals']),default=None),
  'minimum_proved_padded_gap_after_m':min((x['padded_gap_m'] for r in rows for x in r['after']['clear_intervals']),default=None),
  'detail_file':path.name,'detail_sha256':sha(path)}
 report['doors'].append(entry)
 print('HEAD_SWEEP_DOOR',json.dumps(entry),flush=True)
for key in ['pairs','before_separated','before_unresolved','after_separated','after_unresolved','newly_unresolved']:
 report[key]=sum(d[key] for d in report['doors'])
assert report['pairs']==6160 and report['before_separated']+report['before_unresolved']==6160
assert report['after_separated']+report['after_unresolved']==6160
report['unresolved_pair_transitions']=all_transitions
report['status']='CONDITIONAL_FROZEN_MEASURED_AXIS_REPAIRED_HEAD_COMPARISON_COMPLETE'
report['scoped_result']='ALL_6160_PAIRS_SEPARATED_BEFORE_AND_AFTER' if not report['before_unresolved'] and not report['after_unresolved'] else 'UNRESOLVED_PAIRS_RETAINED'
report['source_sha256_after']=sha(SOURCE); assert report['source_sha256_after']==EXPECTED_SOURCE
report['script_sha256_after']=sha(Path(__file__)); assert report['script_sha256_after']==report['script_sha256']
assert all(sha(ROOT/p)==h for p,h in PINNED.values())
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print('HEAD_SWEEP_FINISHED',report['scoped_result'],'pairs',report['pairs'],'newly_unresolved',report['newly_unresolved'],flush=True)
