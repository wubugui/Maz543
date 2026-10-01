"""Portable bounded native layout replay. No install, auth, Git or publication."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for key in ['repo','blender','out']:p.add_argument('--'+key,type=Path,required=True)
p.add_argument('--view',choices=['oblique','elevation'],required=True)
a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve();blender=a.blender.resolve()
assert not out.is_relative_to(repo);out.mkdir(parents=True,exist_ok=False)
script=Path(__file__).resolve().with_name('build-step-layout-study.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(script)=='b295070b1d492c0d376ee732586003928bb94f12db503dbfc089dca93d152812'
cmd=[str(blender),'--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',str(script),'--','--repo',str(repo),'--out',str(out/'native'),'--view',a.view]
r={'status':'IN_PROGRESS_NOT_ACCEPTED','command':cmd,'script_sha256_before':sha(script),'timeout_seconds':180,'isolated_performance_claim':False}
f=out/'process.json';f.write_text(json.dumps(r,indent=2)+'\n');t=time.monotonic()
with (out/'native.log').open('wb') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
 try:code=child.wait(timeout=180);timed_out=False
 except subprocess.TimeoutExpired:child.kill();code=child.wait();timed_out=True
r.update({'exit_code':code,'timed_out':timed_out,'elapsed_seconds':time.monotonic()-t,'script_sha256_after':sha(script)})
path=out/'native/layout-report.json'
if path.exists():r['native_report_status']=json.loads(path.read_bytes()).get('status');r['report_sha256']=sha(path)
r['status']='COMPLETED' if code==0 and not timed_out and r['script_sha256_before']==r['script_sha256_after'] else 'FAILED_OR_TIMED_OUT'
f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if r['status']=='COMPLETED' else 1)
