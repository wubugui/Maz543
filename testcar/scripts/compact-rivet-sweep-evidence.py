"""Lossless portable JSON evidence codec. Original bytes/SHA survive restoration.

pack --source NATIVE_DIR --bundle NEW_BUNDLE_DIR
unpack --bundle BUNDLE_DIR --out NEW_RESTORE_DIR
Every pair and every clear/unresolved interval is retained; repeated structures
are interned. Native names/hashes refer only to reconstructed original bytes.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
minij=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()+b'\n'

def intern(table,memo,value):
 key=json.dumps(value,ensure_ascii=False,separators=(',',':'))
 if key not in memo:memo[key]=len(table);table.append(value)
 return memo[key]

def pack_pairs(data):
 meta={k:v for k,v in data.items() if k!='pairs'}
 out={'format':'maz-head-sweep-pair-table-v1','native_top_key_order':list(data),'native_metadata':meta,
      'statuses':[],'domains':[],'clear_intervals':[],'unresolved_intervals':[],'results':[],'pairs':[]}
 memos={k:{} for k in ['statuses','domains','clear_intervals','unresolved_intervals','results']}
 def put(k,x):return intern(out[k],memos[k],x)
 for row in data['pairs']:
  assert list(row)==['moving_index','head_index','before','after','newly_unresolved']
  results=[]
  for state in ['before','after']:
   r=row[state];assert list(r)==['status','cells','clear_intervals','unresolved_intervals']
   ci=[];ui=[]
   for x in r['clear_intervals']:
    assert list(x)==['lo','hi','axis','padded_gap_m']
    ci.append(put('clear_intervals',[put('domains',[x['lo'],x['hi']]),x['axis'],x['padded_gap_m']]))
   for x in r['unresolved_intervals']:
    assert list(x)==['lo','hi','reason']
    ui.append(put('unresolved_intervals',[put('domains',[x['lo'],x['hi']]),x['reason']]))
   results.append(put('results',[put('statuses',r['status']),r['cells'],ci,ui]))
  out['pairs'].append([row['moving_index'],row['head_index'],results[0],results[1],row['newly_unresolved']])
 return out

def unpack_pairs(data):
 assert data['format']=='maz-head-sweep-pair-table-v1'
 def result(index):
  status,cells,ci,ui=data['results'][index]
  clear=[];unresolved=[]
  for index in ci:
   di,axis,gap=data['clear_intervals'][index];lo,hi=data['domains'][di]
   clear.append({'lo':lo,'hi':hi,'axis':axis,'padded_gap_m':gap})
  for index in ui:
   di,reason=data['unresolved_intervals'][index];lo,hi=data['domains'][di]
   unresolved.append({'lo':lo,'hi':hi,'reason':reason})
  return {'status':data['statuses'][status],'cells':cells,'clear_intervals':clear,'unresolved_intervals':unresolved}
 rows=[{'moving_index':mi,'head_index':hi,'before':result(bi),'after':result(ai),'newly_unresolved':flag}
       for mi,hi,bi,ai,flag in data['pairs']]
 return {key:rows if key=='pairs' else data['native_metadata'][key] for key in data['native_top_key_order']}

def native_bytes(data,serialization):
 if serialization=='minified-ensure-ascii-false-newline':return minij(data)
 if serialization=='indent2-ensure-ascii-false-newline':return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
 if serialization=='indent2-ensure-ascii-true-newline':return (json.dumps(data,indent=2)+'\n').encode()
 raise ValueError(serialization)

def pack(source,bundle):
 bundle.mkdir(parents=True,exist_ok=False)
 manifest={'format':'maz-lossless-native-evidence-bundle-v1',
  'note':'Native hashes identify exact reconstructed original files; compact hashes identify differently named transport files. Restore before consuming native detail_file/detail_sha256 references.',
  'files':[]}
 for path in sorted(p for p in source.rglob('*') if p.is_file()):
  raw=path.read_bytes();rel=path.relative_to(source).as_posix()
  if path.suffix=='.json':
   data=json.loads(raw);serial=None
   for candidate in ['minified-ensure-ascii-false-newline','indent2-ensure-ascii-false-newline','indent2-ensure-ascii-true-newline']:
    if native_bytes(data,candidate)==raw:serial=candidate;break
   assert serial is not None,('Unrecognized serialization',rel)
   if path.name.startswith('cab_pivot_'):
    packed=pack_pairs(data);decoded=unpack_pairs(packed);format='maz-head-sweep-pair-table-v1'
   else:
    packed={'format':'native-json-data-v1','data':data};decoded=packed['data'];format='native-json-data-v1'
   assert decoded==data and native_bytes(decoded,serial)==raw
   wrapped={'native_filename':rel,'native_sha256':sha(raw),'native_serialization':serial,'encoding':packed}
   compact=minij(wrapped);compact_name=rel+'.compact.json'
  else:
   compact=raw;compact_name=rel;format='raw';serial=None
  dest=bundle/compact_name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(compact)
  # Reparse the actual saved transport bytes before accepting.
  if format!='raw':
   reread=json.loads(dest.read_bytes());enc=reread['encoding']
   decoded=unpack_pairs(enc) if enc['format']=='maz-head-sweep-pair-table-v1' else enc['data']
   assert decoded==data and native_bytes(decoded,reread['native_serialization'])==raw
  manifest['files'].append({'native_filename':rel,'native_bytes':len(raw),'native_sha256':sha(raw),
    'compact_filename':compact_name,'compact_bytes':len(compact),'compact_sha256':sha(compact),'encoding':format,
    'parsed_data_equal':True,'exact_original_byte_restore_verified':True})
 (bundle/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 return manifest

def unpack(bundle,out):
 manifest=json.loads((bundle/'delivery-manifest.json').read_bytes())
 assert manifest['format']=='maz-lossless-native-evidence-bundle-v1'
 out.mkdir(parents=True,exist_ok=False)
 for entry in manifest['files']:
  raw=(bundle/entry['compact_filename']).read_bytes()
  assert len(raw)==entry['compact_bytes'] and sha(raw)==entry['compact_sha256']
  if entry['encoding']!='raw':
   wrapped=json.loads(raw);enc=wrapped['encoding']
   assert wrapped['native_filename']==entry['native_filename'] and wrapped['native_sha256']==entry['native_sha256']
   data=unpack_pairs(enc) if enc['format']=='maz-head-sweep-pair-table-v1' else enc['data']
   raw=native_bytes(data,wrapped['native_serialization'])
  assert len(raw)==entry['native_bytes'] and sha(raw)==entry['native_sha256']
  rel=Path(entry['native_filename']);assert not rel.is_absolute() and '..' not in rel.parts
  dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 return manifest

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 sub=p.add_subparsers(dest='action',required=True)
 q=sub.add_parser('pack');q.add_argument('--source',type=Path,required=True);q.add_argument('--bundle',type=Path,required=True)
 q=sub.add_parser('unpack');q.add_argument('--bundle',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 manifest=pack(a.source,a.bundle) if a.action=='pack' else unpack(a.bundle,a.out)
 print(json.dumps({'action':a.action,'files':len(manifest['files']),
  'native_total_bytes':sum(x['native_bytes'] for x in manifest['files']),
  'compact_total_bytes':sum(x['compact_bytes'] for x in manifest['files']),
  'file_sizes':{x['native_filename']:[x['native_bytes'],x['compact_bytes']] for x in manifest['files']}},indent=2))
