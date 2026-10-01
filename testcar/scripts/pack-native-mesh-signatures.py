"""Lossless ordinary-JSON packaging of mesh SIGNATURE metadata, not mesh assets.

pack: python pack-mesh-signatures.py pack --out DIR ORIGINAL.json [SAME.json ...]
restore: python pack-mesh-signatures.py restore --index DIR/index.json --out DIR

Only the recognized canonical JSON structure is supported. Restore verifies every
shard, reconstructs canonical source bytes, verifies original byte count and SHA,
then writes the explicitly mapped original filenames. Existing files are refused.
"""
import argparse, hashlib, json
from pathlib import Path
FORMAT='maz-mesh-signature-columns-v1'
COLUMNS=['mesh_name','signature_sha256','field_schema_index','counts']
MAX_BYTES=140000

def digest(b):return hashlib.sha256(b).hexdigest()
def encode(data):return (json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('utf-8')
def check(condition,message):
 if not condition:raise ValueError(message)
def leaf(name):
 check(type(name) is str and Path(name).name==name and name not in {'.','..'} and '/' not in name and '\\' not in name,'Unsafe filename')
 return name

def save_new(path,data):
 check(not path.exists(),'Refusing overwrite: '+str(path))
 with path.open('xb') as f:f.write(data)
 return {'file':path.name,'bytes':len(data),'sha256':digest(data)}

def pack(paths,out):
 check(bool(paths),'No source manifests');inputs=[Path(p).resolve() for p in paths];raw=inputs[0].read_bytes()
 check(all(p.read_bytes()==raw for p in inputs),'Inputs are not identical source bytes')
 obj=json.loads(raw);check(set(obj)=={'field_schemas','meshes'},'Unknown manifest fields');check(encode(obj)==raw,'Source JSON is not supported byte-exact canonical encoding')
 schemas=obj['field_schemas'];meshes=obj['meshes'];schema_ids=sorted(schemas)
 check(all(set(r)=={'sha256','field_schema','counts'} and r['field_schema'] in schemas for r in meshes.values()),'Unsupported mesh record')
 check(len({p.name for p in inputs})==len(inputs),'Duplicate original filenames')
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);check(not any(out.iterdir()),'Pack directory must be empty')
 schema_record=save_new(out/'field-schemas.json',encode({'format':FORMAT,'schema_ids':schema_ids,'field_schemas':[schemas[s] for s in schema_ids]}))
 check(schema_record['bytes']<MAX_BYTES,'Schema dictionary exceeds shard budget')
 rows=[(name,meshes[name]['sha256'],schema_ids.index(meshes[name]['field_schema']),meshes[name]['counts']) for name in sorted(meshes)]
 shards=[]
 def write_batch(batch):
  payload={'format':FORMAT,'columns':{col:[r[i] for r in batch] for i,col in enumerate(COLUMNS)}};content=encode(payload)
  if len(content)>=MAX_BYTES:
   check(len(batch)>1,'Single row exceeds shard budget');half=len(batch)//2;write_batch(batch[:half]);write_batch(batch[half:]);return
  r=save_new(out/f'mesh-signatures-{len(shards):03d}.json',content);r.update(rows=len(batch),first_mesh=batch[0][0],last_mesh=batch[-1][0]);shards.append(r)
 for start in range(0,len(rows),800):write_batch(rows[start:start+800])
 index={'format':FORMAT,'scope':'Only names, counts, field inventories and SHA-256 signatures. No vertex/triangle/model payloads.',
  'source_encoding':{'utf8':True,'ensure_ascii':True,'sort_keys':True,'separators':[',',':'],'trailing_lf':True},
  'original_files':[{'file':leaf(p.name),'bytes':len(raw),'sha256':digest(raw),'dataset':'preserved-mesh-signatures'} for p in inputs],
  'dataset':'preserved-mesh-signatures','mesh_count':len(rows),'schema_count':len(schema_ids),'schema_file':schema_record,'shards':shards,'max_shard_bytes_exclusive':MAX_BYTES}
 save_new(out/'index.json',encode(index));return index

def restore(index_path,out):
 index_path=Path(index_path).resolve();base=index_path.parent;index=json.loads(index_path.read_bytes())
 check(index['format']==FORMAT,'Unsupported pack version')
 check(index['source_encoding']=={'utf8':True,'ensure_ascii':True,'sort_keys':True,'separators':[',',':'],'trailing_lf':True},'Unsupported source byte encoding')
 def read_checked(record):
  path=base/leaf(record['file']);raw=path.read_bytes();check(len(raw)==record['bytes'] and digest(raw)==record['sha256'],'Shard hash/size failure: '+path.name);return json.loads(raw)
 sd=read_checked(index['schema_file']);check(sd['format']==FORMAT,'Schema version differs');ids=sd['schema_ids'];fields=sd['field_schemas']
 check(len(ids)==len(fields)==index['schema_count'] and len(set(ids))==len(ids),'Schema inventory differs')
 schemas=dict(zip(ids,fields));meshes={};ordered=[]
 for record in index['shards']:
  shard=read_checked(record);check(shard['format']==FORMAT and set(shard['columns'])==set(COLUMNS),'Invalid column schema')
  cols=shard['columns'];check(all(len(cols[c])==record['rows'] for c in COLUMNS),'Column lengths differ')
  check(cols['mesh_name'][0]==record['first_mesh'] and cols['mesh_name'][-1]==record['last_mesh'],'Shard name range differs')
  for name,sha,schema_index,counts in zip(*(cols[c] for c in COLUMNS)):
   check(type(name) is str and name not in meshes and type(schema_index) is int and 0<=schema_index<len(ids),'Duplicate/invalid row')
   check(type(sha) is str and len(sha)==64 and all(c in '0123456789abcdef' for c in sha),'Invalid signature')
   check(len(counts)==4 and all(type(n) is int and n>=0 for n in counts),'Invalid counts')
   ordered.append(name);meshes[name]={'sha256':sha,'field_schema':ids[schema_index],'counts':counts}
 check(len(meshes)==index['mesh_count'] and ordered==sorted(meshes),'Row inventory/order differs')
 raw=encode({'field_schemas':schemas,'meshes':meshes});originals=index['original_files']
 check(bool(originals) and len({leaf(r['file']) for r in originals})==len(originals),'Invalid original file map')
 check(all(len(raw)==r['bytes'] and digest(raw)==r['sha256'] for r in originals),'Reconstructed original bytes/SHA differ')
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 check(all(not (out/r['file']).exists() for r in originals),'Refusing overwrite of original/restored file')
 restored=[save_new(out/r['file'],raw) for r in originals]
 return {'format':FORMAT,'status':'RESTORED_EXACT_ORIGINAL_BYTES','index_sha256':digest(index_path.read_bytes()),'mesh_count':len(meshes),'restored_files':restored}

if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('pack');a.add_argument('--out',required=True);a.add_argument('originals',nargs='+')
 a=sub.add_parser('restore');a.add_argument('--out',required=True);a.add_argument('--index',required=True)
 args=p.parse_args();result=pack(args.originals,args.out) if args.command=='pack' else restore(args.index,args.out);print(json.dumps(result,indent=2))
