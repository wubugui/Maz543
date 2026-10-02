import argparse,hashlib,json,os,subprocess,time,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('script');p.add_argument('run');a=p.parse_args()
root=Path(__file__).resolve().parent;run=root/a.run;run.mkdir(exist_ok=False)
src=root/a.script;frozen=run/'executed-script.py';shutil.copy2(src,frozen);shutil.copy2(__file__,run/'executed-runner.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cmd=[str(root.parent/'maz543-tools/blender-4.5.13-linux-x64/blender'),'--background','--factory-startup','--threads','1','--python-exit-code','1','--python',str(frozen),'--',str(run/'native')]
r={'status':'IN_PROGRESS','command':cmd,'timeout_seconds':120,'threads':1,'script_sha256_start':sha(frozen),'runner_sha256':sha(run/'executed-runner.py'),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};pp=run/'process.json';pp.write_text(json.dumps(r,indent=2)+'\n')
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
