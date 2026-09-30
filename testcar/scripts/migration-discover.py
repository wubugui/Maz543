"""Read-only discovery of project conversation and referenced external artifacts."""
import json,os,re,sqlite3,collections
from pathlib import Path
ROOT=Path('D:/testcar'); OUT=ROOT/'MIGRATION_20260906'; OUT.mkdir(exist_ok=True)
HOME=Path('C:/Users/wubugui/.codex'); TID='01a06f8d-9cc1-7f81-a2a0-70ff399252b9'
con=sqlite3.connect('file:'+str(HOME/'state_5.sqlite')+'?mode=ro',uri=True); con.row_factory=sqlite3.Row
threads=[dict(r) for r in con.execute('select * from threads')]
selected={t['id'] for t in threads if 'testcar' in t['cwd'].lower()}
selected.add(TID)
edges=[dict(r) for r in con.execute('select * from thread_spawn_edges')]
for _ in range(20):
 old=selected.copy()
 for e in edges:
  if e['parent_thread_id'] in selected:selected.add(e['child_thread_id'])
 if old==selected:break
rows=[t for t in threads if t['id'] in selected]
paths=set();stats=[]
pattern=re.compile(r'[A-Za-z]:[/\\][^\s\x00\"\'<>|`\[\]{};]+')
def visit(x):
 if isinstance(x,str):
  for m in pattern.finditer(x):
   p=m.group().rstrip('),:')
   p=re.sub(r'\\+', '/',p)
   if len(p)<1500:paths.add(p)
 elif isinstance(x,dict):
  for v in x.values():visit(v)
 elif isinstance(x,list):
  for v in x:visit(v)
for row in rows:
 p=Path(row['rollout_path']);counts=collections.Counter();first=last=None;errors=[]
 with p.open(encoding='utf-8') as f:
  for i,line in enumerate(f):
   try:r=json.loads(line)
   except Exception as e:errors.append([i+1,str(e)]);continue
   counts[r.get('type')]+=1;first=first or r.get('timestamp');last=r.get('timestamp');visit(r)
 stats.append(dict(id=row['id'],path=str(p),bytes=p.stat().st_size,records=sum(counts.values()),counts=dict(counts),first=first,last=last,parse_errors=errors))
existing=[];missing=[]
for s in sorted(paths):
 try:
  p=Path(s)
  if p.exists():existing.append(dict(path=s,is_dir=p.is_dir(),bytes=p.stat().st_size if p.is_file() else None))
  else:missing.append(s)
 except OSError:missing.append(s)
result=dict(thread_ids=sorted(selected),threads=rows,edges=[e for e in edges if e['parent_thread_id'] in selected],rollouts=stats,existing_paths=existing,unresolved_path_tokens=missing)
(OUT/'discovery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'threads':stats,'external_existing':[p for p in existing if not p['path'].lower().startswith(('d:/testcar','d:/maz543-references'))]},ensure_ascii=False,indent=2))
