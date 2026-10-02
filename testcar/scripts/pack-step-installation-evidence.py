"""Lossless ordinary JSON field dictionaries + array shards for textual diagnostic evidence only.
No model, texture, mesh asset or asset substitute is encoded. Native original bytes are restored/hashed.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def inventory_pack(data):
 rows=data['objects'];keys=sorted({k for r in rows for k in r});out={'format':'geometry-inventory-field-table-v1','metadata':{k:v for k,v in data.items() if k!='objects'},'row_count':len(rows),'columns':[]}
 for key in keys:
  present=[i for i,r in enumerate(rows) if key in r];values=[rows[i][key] for i in present];transform=None
  if key=='physical_pair_axis_gaps_m':
   transform={'dict_keys':sorted(values[0])};assert all(sorted(x)==transform['dict_keys'] for x in values);values=[[x[k] for k in transform['dict_keys']] for x in values]
  unique=[];memo={};indices=[]
  for value in values:
   tag=enc(value)
   if tag not in memo:memo[tag]=len(unique);unique.append(value)
   indices.append(memo[tag])
  direct={'values':values};dictionary={'dictionary':unique,'indices':indices}
  column={'key':key,'present_row_indices':present,'transform':transform,**(dictionary if len(enc(dictionary))<len(enc(direct)) else direct)};out['columns'].append(column)
 return out
def inventory_unpack(data):
 rows=[{} for _ in range(data['row_count'])]
 for c in data['columns']:
  values=c.get('values')
  if values is None:values=[c['dictionary'][i] for i in c['indices']]
  if c['transform']:values=[dict(zip(c['transform']['dict_keys'],v)) for v in values]
  for i,v in zip(c['present_row_indices'],values):rows[i][c['key']]=v
 return dict(data['metadata'],objects=rows)
def shard(value,out):
 if len(enc(value))<=145000:return {'value':value}
 if isinstance(value,dict):
  entries=[{'key':k,'node':shard(v,out)} for k,v in value.items()];parts=[];chunk=[];size=2
  for item in entries:
   n=len(enc(item))
   if chunk and size+n>145000:parts.append(store(chunk,out));chunk=[];size=2
   chunk.append(item);size+=n
  if chunk:parts.append(store(chunk,out))
  return {'dict_field_shards':parts}
 assert isinstance(value,list),'Oversize primitive'
 chunks=[];group=[];size=2
 for item in value:
  n=len(enc(item))
  if n>144000:
   if group:chunks.append(store(group,out));group=[];size=2
   chunks.append({'one_recursive_item':shard(item,out)});continue
  if group and size+n>145000:chunks.append(store(group,out));group=[];size=2
  group.append(item);size+=n
 if group:chunks.append(store(group,out))
 return {'array_shards':chunks}
def store(value,out):
 raw=enc(value);name='shard-'+sha(raw)[:24]+'.json';path=out/name
 if path.exists():assert path.read_bytes()==raw
 else:path.write_bytes(raw)
 return {'file':name,'sha256':sha(raw),'bytes':len(raw),'count':len(value)}
def unshard(node,folder):
 if 'value' in node:return node['value']
 if 'dict_field_shards' in node:
  result={}
  for part in node['dict_field_shards']:
   raw=(folder/part['file']).read_bytes();assert len(raw)==part['bytes'] and sha(raw)==part['sha256'];entries=json.loads(raw);assert len(entries)==part['count']
   for entry in entries:result[entry['key']]=unshard(entry['node'],folder)
  return result
 out=[]
 for c in node['array_shards']:
  if 'one_recursive_item' in c:out.append(unshard(c['one_recursive_item'],folder));continue
  raw=(folder/c['file']).read_bytes();assert sha(raw)==c['sha256'] and len(raw)==c['bytes'];items=json.loads(raw);assert len(items)==c['count'];out.extend(items)
 return out
def pack(root,out,files):
 out.mkdir(exist_ok=False);entries=[]
 for rel in files:
  raw=(root/rel).read_bytes();r={'original_path':rel,'original_bytes':len(raw),'original_sha256':sha(raw)}
  if len(raw)<150000:
   dst=out/'raw'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);r.update(raw_file='raw/'+rel)
  else:
   data=json.loads(raw);assert enc(data)==raw,(rel,'not canonical native JSON')
   packed=inventory_pack(data) if Path(rel).name=='all-geometry-inventory.json' else data
   node=shard(packed,out);nodefile='record-'+sha(rel.encode())[:20]+'.json';(out/nodefile).write_bytes(enc(node));assert (out/nodefile).stat().st_size<200000
   r.update(node_file=nodefile,format='inventory_field_table' if packed is not data else 'ordinary_json')
   restored=unshard(json.loads((out/nodefile).read_bytes()),out)
   if r['format']=='inventory_field_table':restored=inventory_unpack(restored)
   assert enc(restored)==raw
  entries.append(r)
 manifest={'format':'maz-step-fit-text-evidence-v1','native_serialization':'json.dumps(sort_keys=True,ensure_ascii=False,separators=(comma,colon),allow_nan=False)+newline','records':entries}
 (out/'index.json').write_bytes(enc(manifest))
 return manifest
def restore(bundle,out):
 out.mkdir(exist_ok=False);m=json.loads((bundle/'index.json').read_bytes())
 for r in m['records']:
  if 'raw_file' in r:raw=(bundle/r['raw_file']).read_bytes()
  else:
   data=unshard(json.loads((bundle/r['node_file']).read_bytes()),bundle)
   if r['format']=='inventory_field_table':data=inventory_unpack(data)
   raw=enc(data)
  assert len(raw)==r['original_bytes'] and sha(raw)==r['original_sha256'];rel=Path(r['original_path']);assert not rel.is_absolute() and '..' not in rel.parts
  dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['pack','restore']);p.add_argument('--root',type=Path);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--file-list',type=Path);a=p.parse_args()
 m=pack(a.root,a.bundle,json.loads(a.file_list.read_text())) if a.mode=='pack' else restore(a.bundle,a.out)
 print(json.dumps({'mode':a.mode,'records':len(m['records']),'original_bytes':sum(x['original_bytes'] for x in m['records'])},indent=2))
