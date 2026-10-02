"""Independently reproduce the recorded component comparison; no Blender used."""
import argparse, hashlib, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--package',type=Path,default=Path(__file__).resolve().parent);args=p.parse_args();root=args.package

def differences(left,right,path=''):
 if type(left)!=type(right):return [{'path':path,'first':left,'second':right}]
 if isinstance(left,dict):return [row for key in sorted(set(left)|set(right)) for row in differences(left.get(key),right.get(key),path+'/'+key)]
 if isinstance(left,list):
  if len(left)!=len(right):return [{'path':path,'first':left,'second':right}]
  return [row for i,(x,y) in enumerate(zip(left,right)) for row in differences(x,y,path+'/'+str(i))]
 return [] if left==right else [{'path':path,'first':left,'second':right}]

expected=json.loads((root/'cross-process-comparison.json').read_bytes());cases=[]
for directory,key in [('appearance-components-01','first_case'),('appearance-components-02','second_case')]:
 raw=(root/directory/'appearance-open-0.json').read_bytes();assert len(raw)==expected[key]['bytes'];assert hashlib.sha256(raw).hexdigest()==expected[key]['sha256'];cases.append(json.loads(raw))
assert len(cases[0]['rows'])==len(cases[1]['rows'])==6
rows=[]
for first,second in zip(cases[0]['rows'],cases[1]['rows']):
 assert first['object']==second['object'];rows.append({'object':first['object'],'role':first['selection_role'],'component_differences':differences(first,second)})
exclude={'rows','elapsed_seconds','load_and_update_seconds'}
metadata=differences({k:v for k,v in cases[0].items() if k not in exclude},{k:v for k,v in cases[1].items() if k not in exclude})
assert rows==expected['objects'];assert metadata==expected['initialization_metadata_differences']
print(json.dumps({'comparison_reproduced':True,'objects':len(rows),'objects_with_differences':sum(bool(r['component_differences']) for r in rows),'objects_with_all_recorded_fields_equal':sum(not r['component_differences'] for r in rows)},indent=2))
