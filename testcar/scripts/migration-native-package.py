"""Fast native ZIP64 packing with parallel source hashes and full readback."""
import concurrent.futures,datetime,hashlib,importlib.util,json,mmap,os,re,shutil,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=Path('D:/testcar');OUT=ROOT/'MIGRATION_20260906';STAGE=OUT/'support';ZIP=OUT/'MAZ543_COMPLETE_20260906.zip'
spec=importlib.util.spec_from_file_location('migration',ROOT/'scripts/migration-package.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def progress(phase,**kw):
 m.dump(OUT/'progress.json',dict(phase=phase,time=m.now(),**kw));print(phase,kw,flush=True)
def inventory(roots):
 files=[];dirs=[]
 for root,prefix in roots:
  if root.is_file():
   st=root.stat();files.append((str(root),prefix,st.st_size,st.st_mtime_ns));continue
  dirs.append(prefix+'/');stack=[(root,prefix)]
  while stack:
   folder,arc=stack.pop()
   with os.scandir(folder) as it:
    for e in it:
     if folder==ROOT and e.name=='MIGRATION_20260906':continue
     st=e.stat(follow_symlinks=False)
     if getattr(st,'st_file_attributes',0)&1024:raise RuntimeError('Reparse path: '+e.path)
     name=arc+'/'+e.name
     if e.is_dir(follow_symlinks=False):dirs.append(name+'/');stack.append((Path(e.path),name))
     else:files.append((e.path,name,st.st_size,st.st_mtime_ns))
 return sorted(files,key=lambda r:r[1]),sorted(dirs)
def hash_source(r):
 p,name,size,mtime=r;h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 st=os.stat(p)
 if (st.st_size,st.st_mtime_ns)!=(size,mtime):raise RuntimeError('Changed source '+p)
 return dict(path=name,source=p,size=size,mtime_ns=mtime,sha256=h.hexdigest())
def main():
 roots=[r for r in m.source_roots() if r[0].name not in ['MANIFEST.json','COVERAGE.json']]
 progress('inventory');files,dirs=inventory(roots);total=sum(r[2] for r in files)
 progress('hashing_sources',files=len(files),bytes=total)
 manifest=[];cached={}
 if '--resume' in sys.argv and (OUT/'MANIFEST.json').exists():
  cached={e['path']:e for e in json.loads((OUT/'MANIFEST.json').read_text(encoding='utf-8'))}
 def hash_or_reuse(r):
  old=cached.get(r[1])
  if old and (old['source'],old['size'],old['mtime_ns'])==(r[0],r[2],r[3]):return old
  return hash_source(r)
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
  for i,e in enumerate(pool.map(hash_or_reuse,files),1):
   manifest.append(e)
   if i%10000==0:progress('hashing_sources',done=i,files=len(files))
 coverage=dict(created_utc=m.now(),files=len(files),directories=len(dirs),bytes=total,source_roots=[dict(source=str(p),archive_prefix=n) for p,n in roots],excluded=['D:/testcar/MIGRATION_20260906 (self archive excluded; support explicitly included at conversation/ and migration/)'],errors=[])
 m.dump(STAGE/'MANIFEST.json',manifest);m.dump(STAGE/'COVERAGE.json',coverage)
 m.dump(OUT/'MANIFEST.json',manifest);m.dump(OUT/'COVERAGE.json',coverage)
 native_roots=roots+[(STAGE/'MANIFEST.json','migration/MANIFEST.json'),(STAGE/'COVERAGE.json','migration/COVERAGE.json')]
 # This Windows bsdtar lacks -s. Use a temporary explicit junction layout;
 # -h follows only these known roots, and excludes the recursive output folder.
 tree=OUT/'archive-tree';tree.mkdir(exist_ok=True);junctions=[]
 for p,prefix in native_roots:
  target=tree/prefix;target.parent.mkdir(parents=True,exist_ok=True)
  if p.is_dir():
   if target.exists():raise RuntimeError('Temporary target already exists '+str(target))
   ps="New-Item -ItemType Junction -Path '"+str(target).replace("'","''")+"' -Target '"+str(p).replace("'","''")+"' | Out-Null"
   subprocess.run([str(m.RUNTIME/'native/powershell/pwsh.exe'),'-NoProfile','-Command',ps],check=True)
   junctions.append(dict(link=str(target),target=str(p.resolve())))
  else:shutil.copy2(p,target)
 m.dump(OUT/'temporary-junctions.json',junctions)
 args=['C:/Windows/System32/tar.exe','--format','zip','--options','zip:compression=deflate,zip:compression-level=1','-chf',str(ZIP),'--exclude','testcar/MIGRATION_20260906','-C',str(tree),'testcar','external','conversation','migration']
 m.dump(OUT/'native-command.json',args);progress('native_zip',files=len(files),bytes=total)
 with (OUT/'native-archive.log').open('wb') as log:
  subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
 progress('checking_source_stability',archive_bytes=ZIP.stat().st_size)
 again,again_dirs=inventory(roots)
 if files!=again or dirs!=again_dirs:raise RuntimeError('Source inventory/size/mtime changed during packing')
 progress('verifying_archive_members',files=len(manifest))
 class MappedReader:
  def __init__(self,mm):self.mm=mm
  def read(self,n=-1):return self.mm.read(n)
  def seek(self,*a):return self.mm.seek(*a)
  def tell(self):return self.mm.tell()
  def seekable(self):return True
 with ZIP.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as mm,zipfile.ZipFile(MappedReader(mm)) as z:
  actual={i.filename for i in z.infolist() if not i.is_dir()};expected={e['path'] for e in manifest}|{'migration/MANIFEST.json','migration/COVERAGE.json'}
  if actual!=expected:
   m.dump(OUT/'name-errors.json',dict(missing=sorted(expected-actual),extra=sorted(actual-expected)));raise RuntimeError('Archive file name mismatch')
  for i,e in enumerate(manifest,1):
   h=hashlib.sha256();size=0
   with z.open(e['path']) as f:
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
   if h.hexdigest()!=e['sha256'] or size!=e['size']:raise RuntimeError('Archive content mismatch '+e['path'])
   if i%10000==0:progress('verifying_archive_members',done=i,files=len(manifest))
  if json.loads(z.read('migration/MANIFEST.json'))!=manifest:raise RuntimeError('Manifest mismatch')
  if json.loads(z.read('migration/COVERAGE.json'))!=coverage:raise RuntimeError('Coverage mismatch')
 progress('hashing_complete_archive');sha=m.digest(ZIP)
 (OUT/(ZIP.name+'.sha256')).write_text(sha+'  '+ZIP.name+'\n',encoding='ascii')
 report=dict(verified_utc=m.now(),archive=ZIP.name,archive_bytes=ZIP.stat().st_size,archive_sha256=sha,verified_files=len(manifest),verified_uncompressed_bytes=total,method='Native ZIP64; every member read with CRC32 and SHA-256 compared against independently hashed source; source inventory/size/mtime stable; manifest and coverage read back',failures=[],passed=True)
 m.dump(OUT/'VERIFIED.json',report);progress('complete',**report)
if __name__=='__main__':main()
