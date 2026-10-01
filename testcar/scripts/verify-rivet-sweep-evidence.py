"""Read-back coverage and integrity audit; no Blender or model changes."""
from pathlib import Path
import collections,hashlib,json,math
import argparse
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--evidence',type=Path,required=True)
p.add_argument('--audit-script',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
OUT=a.evidence.resolve()
AUDIT_SCRIPT=a.audit_script.resolve()
READBACK=a.out.resolve()
assert not READBACK.exists(), 'Do not overwrite an earlier readback'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((OUT/'sweep-report.json').read_bytes())
p=json.loads((OUT/'process.json').read_bytes())
assert p['status']=='COMPLETED' and p['returncode']==0 and not p['timed_out']
assert p['source_unchanged'] and p['script_unchanged']
assert p['script_sha256_before']==r['script_sha256']==r['script_sha256_after']==sha(AUDIT_SCRIPT)
for path,info in p['artifacts'].items():
 f=OUT/path;assert f.stat().st_size==info['bytes'] and sha(f)==info['sha256'],path
assert len(r['modified_heads'])==140
assert collections.Counter(h['side'] for h in r['modified_heads'])=={-1:70,1:70}
assert all(h['head_index']==i for i,h in enumerate(r['modified_heads']))
assert len({(h['object'],h['component']) for h in r['modified_heads']})==140
assert r['native_replay_equals_published_report']
assert sha(OUT/r['native_replay_report'])==r['native_replay_report_sha256']==r['inputs']['published_repair_report']['sha256']
assert r['padding_m_per_moving_and_fixed_box']==2e-5 and r['max_depth']==6 and r['max_cells_per_pair']==127
expected_hinges={'cab_pivot_002':-1,'cab_pivot_003':-1,'cab_pivot_006':1,'cab_pivot_007':1}
assert [d['hinge'] for d in r['doors']]==list(expected_hinges)
keys=set(); signs={}; totals=collections.Counter(); axes=collections.Counter(); deltas=[]
minimum={label:(math.inf,None) for label in ['before','after']}
for d in r['doors']:
 f=OUT/d['detail_file'];assert sha(f)==d['detail_sha256']
 x=json.loads(f.read_bytes());side=expected_hinges[x['hinge']]
 assert side==x['side']
 end=-side*math.radians(99);lo,hi=sorted((0.,end))
 assert x['signed_angle_radians_at_99_degrees']==end and x['closed_angle_radians']==[lo,hi]
 signs[x['hinge']]=[lo,hi]
 assert len(x['moving_names'])==len(set(x['moving_names']))==11
 expected={(i,j) for i in range(11) for j in range(140)}
 assert len(x['pairs'])==1540
 assert {(a['moving_index'],a['head_index']) for a in x['pairs']}==expected
 assert all(r['snapshot_hashes'][n]['before']==r['snapshot_hashes'][n]['after'] for n in x['moving_names'])
 for row in x['pairs']:
  n=x['moving_names'][row['moving_index']];h=r['modified_heads'][row['head_index']]
  key=(n,h['object'],h['component']);assert key not in keys;keys.add(key)
  totals['same_side_pairs' if side==h['side'] else 'opposite_side_pairs']+=1
  assert not row['newly_unresolved']
  for label in ['before','after']:
   q=row[label]
   assert q['status']=='CERTIFIED_RIGID_SNAPSHOT_BOX_SEPARATION'
   assert q['cells']==1 and not q['unresolved_intervals'] and len(q['clear_intervals'])==1
   interval=q['clear_intervals'][0]
   assert [interval['lo'],interval['hi']]==[lo,hi]
   gap=interval['padded_gap_m'];assert math.isfinite(gap) and gap>0
   assert interval['axis'] in [0,1,2];axes[(label,interval['axis'])]+=1
   if gap<minimum[label][0]:minimum[label]=(gap,list(key))
   totals[label+'_separated']+=1
  deltas.append(row['after']['clear_intervals'][0]['padded_gap_m']-row['before']['clear_intervals'][0]['padded_gap_m'])
assert len(keys)==6160
assert totals['same_side_pairs']==totals['opposite_side_pairs']==3080
assert totals['before_separated']==totals['after_separated']==6160
assert r['before_unresolved']==r['after_unresolved']==r['newly_unresolved']==0
assert not r['unresolved_pair_transitions']
result={'status':'READBACK_HASH_COVERAGE_AND_INTERVAL_SEMANTICS_PASS','unique_pairs':len(keys),
 'totals':dict(totals),'signed_angle_intervals_radians':signs,
 'minimum_padded_axis_gap':{k:{'m':v[0],'pair':v[1]} for k,v in minimum.items()},
 'chosen_separation_axes':{f'{label}_{"xyz"[axis]}':n for (label,axis),n in axes.items()},
 'pair_padded_gap_changes':{'greater':sum(d>0 for d in deltas),'equal':sum(d==0 for d in deltas),'smaller':sum(d<0 for d in deltas),'minimum_delta_m':min(deltas),'maximum_delta_m':max(deltas)},
 'note':'Readback checks saved conditional results and their identities/coverage; it is not a second native evaluation or floating error proof',
 'process_sha256':sha(OUT/'process.json'),'report_sha256':sha(OUT/'sweep-report.json')}
READBACK.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
