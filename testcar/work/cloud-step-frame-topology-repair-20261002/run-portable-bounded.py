"""Portable explicit-path entry; CPU1/120s, frozen evidence and disabled autoexec."""
import argparse,hashlib,json,os,subprocess,time,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for name in ('blender','script','repo','original-script','original-layout-report','out'):
 p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
run=a.out.resolve();repo=a.repo.resolve()
assert not run.is_relative_to(repo),'Output directory must remain outside repository'
run.mkdir(parents=True,exist_ok=False)
frozen=run/'executed-script.py';shutil.copy2(a.script.resolve(),frozen);shutil.copy2(__file__,run/'executed-runner.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cmd=[str(a.blender.resolve()),'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','1','--python',str(frozen),'--','--repo',str(repo),'--original-script',str(a.original_script.resolve()),'--original-layout-report',str(a.original_layout_report.resolve()),'--out',str(run/'native')]
r={'status':'IN_PROGRESS','command':cmd,'timeout_seconds':120,'threads':1,'disable_autoexec_cli':True,'script_sha256_start':sha(frozen),'runner_sha256':sha(run/'executed-runner.py'),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};pp=run/'process.json';pp.write_text(json.dumps(r,indent=2)+'\n')
t=time.monotonic();env=dict(os.environ);env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
with open(run/'native.log','w') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);r['pid']=child.pid
 try:code=child.wait(timeout=120);timeout=False
 except subprocess.TimeoutExpired:
  child.terminate()
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:child.kill();child.wait()
  code=child.returncode;timeout=True
r.update(status='COMPLETED' if code==0 and not timeout else 'FAILED',exit_code=code,timed_out=timeout,elapsed_seconds=time.monotonic()-t,end_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),script_sha256_end=sha(frozen),log_sha256=sha(run/'native.log'))
for file in (run/'native').glob('*.json'):r.setdefault('evidence_sha256',{})[file.name]=sha(file)
pp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if code==0 and not timeout else 1)
