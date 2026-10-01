#!/usr/bin/env python3
"""Bound each native render process to 180s and retain logs and actual exits."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('view',choices=['oblique','elevation']);p.add_argument('--run-name',required=True);a=p.parse_args()
root=Path(__file__).resolve().parent
script=root/'build-step-layout-study.py'
repo=root.parent/'Maz543'
blender=root.parent/'maz543-tools/blender-4.5.13-linux-x64/blender'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runroot=root/a.run_name;runroot.mkdir(exist_ok=False)
cmd=[str(blender),'--background','--factory-startup','--threads','2','--python-exit-code','1','--python',str(script),'--','--repo',str(repo),'--out',str(runroot/'native'),'--view',a.view]
process={'status':'IN_PROGRESS','command':cmd,'timeout_seconds':180,'threads':2,'script_sha256_start':sha(script),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
proc_path=runroot/'process.json';proc_path.write_text(json.dumps(process,indent=2)+'\n')
t0=time.monotonic()
env=dict(os.environ);env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with open(runroot/'native.log','w') as log:
    child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    process['pid']=child.pid
    try:
        code=child.wait(timeout=180);timed_out=False
    except subprocess.TimeoutExpired:
        child.terminate()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()
        code=child.returncode;timed_out=True
process.update(status='PROCESS_COMPLETED' if code==0 and not timed_out else 'PROCESS_FAILED',exit_code=code,timed_out=timed_out,elapsed_seconds=time.monotonic()-t0,script_sha256_end=sha(script),end_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),log_sha256=sha(runroot/'native.log'))
rep=runroot/'native/layout-report.json'
if rep.exists():process['report_sha256']=sha(rep);process['native_report_status']=json.loads(rep.read_text())['status']
proc_path.write_text(json.dumps(process,indent=2)+'\n')
print(json.dumps(process,indent=2))
raise SystemExit(0 if code==0 and not timed_out else 1)
