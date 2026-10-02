"""Fetch only published Git blobs into a new empty bare repository, then verify bytes.

This is read-only Git transport. All remote writes are performed by the GitHub
plugin separately. No source checkout objects or alternates may satisfy reads.
"""
import argparse, hashlib, json, os, subprocess, tempfile, time
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
inventory=json.loads(a.inventory.read_text())
assert inventory['public_url']=='https://github.com/wubugui/Maz543.git'
assert len(inventory['commit'])==40 and len(inventory['tree'])==40
rows=inventory['files'];assert rows and len({r['path'] for r in rows})==len(rows)
for r in rows:
    rel=Path(r['path']);assert not rel.is_absolute() and '..' not in rel.parts and str(rel)==r['path']
    assert len(r['git_blob_sha1'])==40 and len(r['sha256'])==64
a.root.mkdir(parents=True,exist_ok=False)
bare=a.root/'bare';bare.mkdir();files=a.root/'files';files.mkdir()
env=dict(os.environ);env['GIT_TERMINAL_PROMPT']='0'
for key in ('GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR'):
    env.pop(key,None)
def run(args,limit=300):
    return subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=limit)
prefix=['git','--no-lazy-fetch','-C',str(bare),'-c','credential.helper=']
init=run(prefix+['init','--bare'],30);assert init.returncode==0,init.stderr.decode(errors='replace')
assert not (bare/'objects/info/alternates').exists()
unique=sorted({r['git_blob_sha1'] for r in rows})
absent=[]
for oid in unique:
    check=run(prefix+['cat-file','-e',oid],30)
    assert check.returncode!=0,('object unexpectedly existed',oid)
    absent.append(oid)
ref='refs/heads/development/cloud-maz543a-20260930'
before=run(['git','-c','credential.helper=','ls-remote',inventory['public_url'],ref],60)
assert before.returncode==0 and before.stdout.decode().split()[0]==inventory['commit']
start=time.monotonic()
fetch=run(prefix+['fetch','--no-tags','--depth=1',inventory['public_url'],*unique],300)
(a.root/'fetch.stdout').write_bytes(fetch.stdout);(a.root/'fetch.stderr').write_bytes(fetch.stderr)
assert fetch.returncode==0,fetch.stderr.decode(errors='replace')
verified=[]
for row in rows:
    read=run(prefix+['cat-file','blob',row['git_blob_sha1']],30)
    assert read.returncode==0
    raw=read.stdout
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
    target=files/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(raw)
    verified.append(row)
after=run(['git','-c','credential.helper=','ls-remote',inventory['public_url'],ref],60)
assert after.returncode==0 and after.stdout.decode().split()[0]==inventory['commit']
report={'status':'PUBLISHED_REMOTE_BYTES_EXACT','commit':inventory['commit'],'tree':inventory['tree'],
        'public_url':inventory['public_url'],'files':verified,'file_count':len(verified),
        'unique_blobs':len(unique),'bytes':sum(x['bytes'] for x in rows),
        'fresh_bare_objects_all_absent_before_fetch':len(absent),
        'no_git_alternates':True,'no_local_object_source':True,'ref_unchanged_before_after':True,
        'elapsed_seconds':time.monotonic()-start,'finished_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(a.root/'remote-bytes-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
