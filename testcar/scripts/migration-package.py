"""Create a local, source-verified ZIP64 migration snapshot. No source deletion."""
import argparse,collections,datetime,hashlib,json,os,shutil,sqlite3,subprocess,time,zipfile
from pathlib import Path
ROOT=Path('D:/testcar'); OUT=ROOT/'MIGRATION_20260906'; STAGE=OUT/'support'
CODEX=Path('C:/Users/wubugui/.codex'); TID='01a06f8d-9cc1-7f81-a2a0-70ff399252b9'
RUNTIME=Path('C:/Users/wubugui/.cache/codex-runtimes/codex-primary-runtime/dependencies')
ZIP=OUT/'MAZ543_COMPLETE_20260906.zip'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dbopen(name):
 c=sqlite3.connect('file:'+str(CODEX/name)+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('BEGIN');return c
def capture():
 STAGE.mkdir(parents=True,exist_ok=True);conv=STAGE/'conversation';conv.mkdir(exist_ok=True)
 c=dbopen('state_5.sqlite');threads=[dict(r) for r in c.execute('select * from threads')]
 ids={t['id'] for t in threads if 'testcar' in t['cwd'].lower()}|{TID};edges=[dict(r) for r in c.execute('select * from thread_spawn_edges')]
 for _ in range(30):
  old=ids.copy()
  for e in edges:
   if e['parent_thread_id'] in ids:ids.add(e['child_thread_id'])
  if old==ids:break
 rows=[t for t in threads if t['id'] in ids];reports=[]
 for t in rows:
  p=Path(t['rollout_path']);dest=conv/'raw'/p.name;dest.parent.mkdir(exist_ok=True)
  # Read an immutable prefix; bytes after this capture belong to a later snapshot.
  size=p.stat().st_size
  with p.open('rb') as src,dest.open('wb') as dst:
   remaining=size
   while remaining:
    b=src.read(min(4*1024*1024,remaining))
    if not b:raise RuntimeError('Short session read '+str(p))
    dst.write(b);remaining-=len(b)
  counts=collections.Counter();messages=[];completed_ids=set();first=last=None;errors=[];ordinals=[]
  with dest.open(encoding='utf-8') as f:
   for lineno,line in enumerate(f,1):
    try:r=json.loads(line)
    except Exception as e:errors.append({'line':lineno,'error':str(e)});continue
    first=first or r.get('timestamp');last=r.get('timestamp');counts[r.get('type')]+=1
    if 'ordinal'in r:ordinals.append(r['ordinal'])
    v=r.get('payload',{});item=None
    if r.get('type')=='event_msg' and v.get('type')=='item_completed':
     it=v.get('item',{})
     if it.get('type') in ['UserMessage','AgentMessage']:
      item=it;completed_ids.add(it.get('id'))
    if item:messages.append((r.get('timestamp'),item,True,lineno))
    elif r.get('type')=='response_item' and v.get('type') in ['message','agent_message']:
     if v.get('role') in ['user','assistant'] or v.get('type')=='agent_message':messages.append((r.get('timestamp'),v,False,lineno))
  # Human readable messages; all event/tool/compaction bytes are preserved in raw/.
  rendered=[]
  for timestamp,item,canonical,lineno in messages:
   if not canonical and item.get('id') and item['id'] in completed_ids:continue
   if item.get('channel')=='analysis':continue
   role='用户' if item.get('type')=='UserMessage' or item.get('role')=='user' else '助手'
   content=item.get('content',[]);texts=[]
   if isinstance(content,str):texts=[content]
   elif isinstance(content,list):
    for v in content:
     if isinstance(v,dict) and isinstance(v.get('text'),str):texts.append(v['text'])
   if not texts and isinstance(item.get('text'),str):texts=[item['text']]
   if texts:rendered.append(f'## {timestamp} · {role} · 原始行 {lineno}\n\n'+ '\n\n'.join(texts))
  (conv/(t['id']+'.md')).write_text('# 对话文本导出\n\n原始记录含完整工具调用、输出与压缩事件；此文件仅便于阅读消息。\n\n'+'\n\n---\n\n'.join(rendered),encoding='utf-8')
  gaps=[(a,b) for a,b in zip(ordinals,ordinals[1:]) if b!=a+1]
  reports.append(dict(thread_id=t['id'],source=str(p),file='raw/'+p.name,snapshot_utc=now(),bytes=size,sha256=digest(dest),records=sum(counts.values()),counts=dict(counts),first_timestamp=first,last_timestamp=last,ordinal_gaps=gaps,parse_errors=errors,human_messages=len(rendered)))
  if errors:raise RuntimeError('Session JSONL parse failure; retry capture after current write finishes')
 dump(conv/'history-index.json',reports);dump(conv/'threads.json',rows)
 # Filtered SQLite snapshots preserve actual table schemas and all task records.
 for db in ['state_5.sqlite','thread_history_1.sqlite','goals_1.sqlite']:
  src=c if db=='state_5.sqlite' else dbopen(db);target=conv/db
  if target.exists():target.unlink()  # Generated snapshot only, never the live DB.
  dst=sqlite3.connect(target);dst.execute('PRAGMA foreign_keys=OFF')
  table_counts={};schemas={}
  for tab in src.execute("select name,sql from sqlite_master where type='table' and name not like 'sqlite_%'"):
   name,sql=tab['name'],tab['sql'];schemas[name]=sql;cols=[r['name'] for r in src.execute('PRAGMA table_info("'+name+'")')]
   where=None;args=tuple(ids);marks=','.join('?' for _ in ids)
   if 'thread_id'in cols:where='thread_id IN ('+marks+')'
   elif name=='threads':where='id IN ('+marks+')'
   elif name=='thread_spawn_edges':where='parent_thread_id IN ('+marks+')'
   if where is None:continue
   dst.execute(sql);n=0
   for r in src.execute('SELECT * FROM "'+name+'" WHERE '+where,args):
    dst.execute('INSERT INTO "'+name+'" VALUES ('+','.join('?' for _ in cols)+')',tuple(r));n+=1
   table_counts[name]=n
  dst.commit();ok=dst.execute('PRAGMA integrity_check').fetchone()[0];dst.close()
  dump(conv/(db+'.schema.json'),schemas);dump(conv/(db+'.export.json'),dict(snapshot_utc=now(),tables=table_counts,integrity_check=ok))
  if db!='state_5.sqlite':src.close()
 c.close()
 g=sqlite3.connect(conv/'goals_1.sqlite');g.row_factory=sqlite3.Row;dump(conv/'current-goal.json',[dict(r) for r in g.execute('select * from thread_goals')]);g.close()
 # Git metadata, including ignored/untracked artifacts, for next-agent orientation.
 for name,args in [('git-status.txt',['status','--short','--branch']),('git-head.txt',['log','-1','--format=fuller']),('git-remotes.txt',['remote','-v'])]:
  r=subprocess.run(['git',*args],cwd=ROOT,capture_output=True);(STAGE/name).write_bytes(r.stdout+r.stderr)
 dump(STAGE/'capture.json',dict(captured_utc=now(),thread_ids=sorted(ids),root=str(ROOT),history_boundary='Per-file exact byte snapshot; later packaging tool messages and final delivery are outside this cutoff.'))
 print('HISTORY_CAPTURED',json.dumps(reports,ensure_ascii=False),flush=True)
def source_roots():
 sources=[(ROOT,'testcar'),(STAGE/'conversation','conversation'),
 (Path('D:/maz543-references'),'external/maz543-references'),
 (Path('C:/Program Files/nodejs'),'external/nodejs'),(RUNTIME,'external/codex-dependencies'),
 (Path('C:/Users/wubugui/AppData/Local/Programs/Python/Python310'),'external/python310'),
 (Path('C:/Users/wubugui/AppData/Local/Temp/browser-use/assets/6bfab5ec-12f6-4b9a-b020-dd5570b837f8'),'external/browser-reference-downloads'),
 (CODEX/'visualizations/2026/09/05'/TID,'external/thread-visualizations')]
 for name in ['maz543-interior.jpg','maz543-reference.html','maz543-reference.txt']:sources.append((Path('D:/')/name,'external/early-reference-files/'+name))
 for p in STAGE.iterdir():
  if p.name!='conversation':sources.append((p,'migration/'+p.name))
 return sources
def scan(sources):
 files=[];dirs=[];links=[]
 for root,prefix in sources:
  if not root.exists():raise FileNotFoundError(root)
  if root.is_file():files.append((root,prefix));continue
  dirs.append(prefix+'/')
  for d,ds,fs in os.walk(root,followlinks=False):
   base=Path(d)
   ds[:]=sorted(n for n in ds if not (root==ROOT and (base/n).resolve().is_relative_to(OUT.resolve())))
   for n in ds+fs:
    p=base/n
    if p.is_symlink() or p.is_junction():links.append(str(p))
   for n in ds:dirs.append(prefix+'/'+(base/n).relative_to(root).as_posix()+'/')
   for n in sorted(fs):
    p=base/n;files.append((p,prefix+'/'+p.relative_to(root).as_posix()))
 if links:raise RuntimeError('Unexpected reparse links requiring explicit handling: '+str(links))
 names=[n for _,n in files]
 if len(set(names))!=len(names):raise RuntimeError('Duplicate archive names')
 return files,dirs
def package():
 sources=source_roots();files,dirs=scan(sources);total=sum(p.stat().st_size for p,_ in files)
 dump(OUT/'source-roots.json',[dict(source=str(p),archive_prefix=n) for p,n in sources])
 print('PACKAGE_START',len(files),total,flush=True)
 manifest=[];processed=0;start=time.monotonic()
 with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True,strict_timestamps=False) as z:
  for name in dirs:z.writestr(name,b'')
  for i,(p,name) in enumerate(files,1):
   before=p.stat();h=hashlib.sha256();length=0
   info=zipfile.ZipInfo.from_file(p,name,strict_timestamps=False);info.compress_type=zipfile.ZIP_DEFLATED;info._compresslevel=1
   with p.open('rb') as src,z.open(info,'w',force_zip64=True) as dst:
    for b in iter(lambda:src.read(1024*1024),b''):dst.write(b);h.update(b);length+=len(b)
   after=p.stat()
   if before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns or length!=before.st_size:raise RuntimeError('Source changed while packing: '+str(p))
   manifest.append(dict(path=name,source=str(p),size=length,sha256=h.hexdigest(),mtime_ns=before.st_mtime_ns));processed+=length
   if i%2000==0:print('PACK',i,'/',len(files),'bytes',processed,'seconds',round(time.monotonic()-start),flush=True)
  # Check the full directory inventory again to catch concurrent additions/removals.
  after_files,_=scan(sources)
  if {n for _,n in after_files}!={n for _,n in files}:raise RuntimeError('Source inventory changed during packing')
  for entry in manifest:
   st=Path(entry['source']).stat()
   if st.st_size!=entry['size'] or st.st_mtime_ns!=entry['mtime_ns']:raise RuntimeError('Source changed since archive read '+entry['source'])
  coverage=dict(created_utc=now(),files=len(files),directories=len(dirs),bytes=total,source_roots=[dict(source=str(p),archive_prefix=n) for p,n in sources],excluded=['D:/testcar/MIGRATION_20260906 (archive/support stored at explicit prefixes; prevents recursive self-inclusion)'],errors=[])
  z.writestr('migration/MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2));z.writestr('migration/COVERAGE.json',json.dumps(coverage,ensure_ascii=False,indent=2))
 dump(OUT/'MANIFEST.json',manifest);dump(OUT/'COVERAGE.json',coverage)
 print('PACKAGE_WRITTEN',ZIP.stat().st_size,flush=True)
def verify():
 manifest=json.loads((OUT/'MANIFEST.json').read_text(encoding='utf-8'));failures=[];done=0
 with zipfile.ZipFile(ZIP) as z:
  for i,e in enumerate(manifest,1):
   h=hashlib.sha256();size=0
   with z.open(e['path']) as f:
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
   if h.hexdigest()!=e['sha256'] or size!=e['size']:failures.append(e['path'])
   done+=size
   if i%5000==0:print('VERIFY',i,'/',len(manifest),'bytes',done,flush=True)
  names={e['path'] for e in manifest}|{'migration/MANIFEST.json','migration/COVERAGE.json'}
  actual={i.filename for i in z.infolist() if not i.is_dir()}
  if names!=actual:failures.append('Archive name mismatch')
  z.read('migration/MANIFEST.json');z.read('migration/COVERAGE.json')
 sha=digest(ZIP);(OUT/(ZIP.name+'.sha256')).write_text(sha+'  '+ZIP.name+'\n',encoding='ascii')
 report=dict(verified_utc=now(),archive=ZIP.name,archive_bytes=ZIP.stat().st_size,archive_sha256=sha,verified_files=len(manifest),verified_uncompressed_bytes=done,method='Read every archive member; CRC32 + SHA-256 against bytes read from source; source inventory and size/mtime stable through archive close',failures=failures,passed=not failures)
 dump(OUT/'VERIFIED.json',report);print('VERIFIED',json.dumps(report),flush=True)
 if failures:raise RuntimeError('Verification failed')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['capture','package','verify']);a=ap.parse_args()
 {'capture':capture,'package':package,'verify':verify}[a.action]()
