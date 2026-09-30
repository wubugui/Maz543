from pathlib import Path
import json,hashlib,struct,mmap
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
paths=[Path(r'C:\Users\weiruanrinima\Downloads\MAZ543-reference-current-pose (1).glb'),ROOT/'outputs/render-worker-evidence/whole-current-pose.glb']
def read_meta(path):
 with path.open('rb') as f:
  header=f.read(20);size=struct.unpack_from('<I',header,12)[0];doc=json.loads(f.read(size));length,kind=struct.unpack('<II',f.read(8));assert kind==0x004e4942
  return doc,28+size,length
old,old_offset,old_len=read_meta(paths[0]);new,new_offset,new_len=read_meta(paths[1]);assert old_len==new_len
changes=[]
def compare(a,b,path=''):
 if type(a)!=type(b):changes.append({'path':path,'before':a,'after':b});return
 if isinstance(a,dict):
  for key in sorted(set(a)|set(b)):
   if key not in a or key not in b:changes.append({'path':path+'/'+key,'before':a.get(key),'after':b.get(key)})
   else:compare(a[key],b[key],path+'/'+key)
 elif isinstance(a,list):
  if len(a)!=len(b):changes.append({'path':path+'/length','before':len(a),'after':len(b)})
  for index,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(index))
 elif a!=b:changes.append({'path':path,'before':a,'after':b})
compare(old,new)
count=0;hashes=[hashlib.sha256(),hashlib.sha256()]
with paths[0].open('rb') as a,paths[1].open('rb') as b:
 a.seek(old_offset);b.seek(new_offset)
 for offset in range(0,old_len,1024*1024):
  x=a.read(min(1024*1024,old_len-offset));y=b.read(len(x));hashes[0].update(x);hashes[1].update(y);count+=int(np.count_nonzero(np.frombuffer(x,dtype=np.uint8)!=np.frombuffer(y,dtype=np.uint8)))
report={'baseline':str(paths[0]),'candidate':str(paths[1]),'bytes':[p.stat().st_size for p in paths],'binaryBytes':old_len,'binarySha256':[h.hexdigest() for h in hashes],'binaryDifferentBytes':count,'jsonChanges':changes,'nodes':[len(old['nodes']),len(new['nodes'])],'meshes':[len(old['meshes']),len(new['meshes'])],'images':[len(old.get('images',[])),len(new.get('images',[]))],'limits':'Exports were made at different mechanical times. Report every JSON difference; do not assume identical snapshots.'}
(ROOT/'outputs/render-worker-evidence/whole-export-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['jsonChanges']},indent=2));print('JSON changed values:',len(changes));print(json.dumps(changes[:12],indent=2))
