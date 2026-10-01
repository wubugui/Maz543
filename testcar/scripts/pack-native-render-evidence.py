"""Lossless ordinary JSON array sharding for bounded evidence publication, never model transport."""
import argparse,json,hashlib
from pathlib import Path
P=argparse.ArgumentParser();P.add_argument('mode',choices=['pack','restore']);P.add_argument('--out',required=True);P.add_argument('--index');P.add_argument('files',nargs='*');a=P.parse_args();out=Path(a.out);out.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda x:(json.dumps(x,ensure_ascii=True,separators=(',',':'))+'\n').encode()
if a.mode=='pack':
 assert not (out/'index.json').exists();records=[]
 for filename in a.files:
  p=Path(filename);raw=p.read_bytes();j=json.loads(raw);assert (json.dumps(j,indent=2)+'\n').encode()==raw
  entries=[]
  for key,value in j.items():
   if isinstance(value,list) and len(encode(value))>70000:
    parts=[];chunk=[]
    for item in value:
     if chunk and len(encode(chunk+[item]))>70000:
      b=encode(chunk);name='array-'+sha(b)[:20]+'.json';dst=out/name
      if dst.exists():assert dst.read_bytes()==b
      else:dst.write_bytes(b)
      parts.append({'file':name,'sha256':sha(b),'bytes':len(b),'count':len(chunk)});chunk=[]
     chunk.append(item)
    if chunk:
     b=encode(chunk);name='array-'+sha(b)[:20]+'.json';dst=out/name
     if dst.exists():assert dst.read_bytes()==b
     else:dst.write_bytes(b)
     parts.append({'file':name,'sha256':sha(b),'bytes':len(b),'count':len(chunk)})
    entries.append({'key':key,'array_shards':parts})
   else:entries.append({'key':key,'value':value})
  records.append({'original_name':p.name,'original_bytes':len(raw),'original_sha256':sha(raw),'entries_in_original_key_order':entries})
 index={'format':'ordinary-json-array-shards-v1','original_serialization':'json.dumps(value, indent=2) + newline; ensure_ascii=True','scope':'Native inspection reports only, no blend/mesh asset or texture transport','records':records};(out/'index.json').write_bytes(encode(index));print('PACKED',len(records),'records',sum(p.stat().st_size for p in out.iterdir() if p.is_file()),'bytes')
else:
 index_path=Path(a.index);index=json.loads(index_path.read_text());results=[]
 for r in index['records']:
  j={}
  for e in r['entries_in_original_key_order']:
   if 'value' in e:j[e['key']]=e['value']
   else:
    value=[]
    for part in e['array_shards']:
     b=(index_path.parent/part['file']).read_bytes();assert len(b)==part['bytes'] and sha(b)==part['sha256'];items=json.loads(b);assert len(items)==part['count'];value.extend(items)
    j[e['key']]=value
  b=(json.dumps(j,indent=2)+'\n').encode();assert len(b)==r['original_bytes'] and sha(b)==r['original_sha256'];dest=out/r['original_name'];assert not dest.exists();dest.write_bytes(b);results.append({'file':dest.name,'bytes':len(b),'sha256':sha(b)})
 print(json.dumps(results,indent=2))
