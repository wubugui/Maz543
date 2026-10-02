#!/usr/bin/env python3
"""Freeze exact script, CPU1 and 240-second hard subprocess bound; never accept stale report."""
import argparse,hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run-name',required=True);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);a=p.parse_args()
root=a.root;folder=Path(__file__).resolve().parent;run=folder/a.run_name;run.mkdir(exist_ok=False)
script=run/'executed-script.py';shutil.copyfile(folder/'check-installation-fit.py',script);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cmd=[str(root/'maz543-tools/blender-4.5.13-linux-x64/blender'),'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','17','--python',str(script),'--','--repo',str(root/'Maz543'),'--candidate',str(root/'maz-native-axis-controls-20261001/MAZ543A_Native_Barrel_Axis_Controls.blend'),'--layout-report',str(root/'maz-step-layout-study-20261001/iteration-02-elevation/native/layout-report.json'),'--out',str(run/'native')]
meta={'status':'IN_PROGRESS','command':cmd,'timeout_seconds':240,'threads':1,'script_sha256_start':sha(script),'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
def write(): (run/'process.json').write_text(json.dumps(meta,indent=2)+'\n')
write();t=time.monotonic();env=dict(os.environ);env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with open(run/'native.log','w') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);meta['pid']=child.pid;write()
 try:code=child.wait(timeout=240);timeout=False
 except subprocess.TimeoutExpired:child.kill();code=child.wait();timeout=True
meta.update(status='PROCESS_COMPLETED' if code==0 and not timeout else 'PROCESS_FAILED',exit_code=code,timed_out=timeout,elapsed_seconds=time.monotonic()-t,peak_children_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,script_sha256_end=sha(script),end_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),log_sha256=sha(run/'native.log'))
r=run/'native/fit-report.json'
if r.exists():meta.update(report_sha256=sha(r),native_report_status=json.loads(r.read_text())['status'])
else:meta['native_report_status']='NO_REPORT'
if meta['status']!='PROCESS_COMPLETED':(run/'FAILURE.json').write_text(json.dumps({'status':'FAILED_OR_TIMED_OUT_NOT_ACCEPTED','process':meta},indent=2)+'\n')
write();print(json.dumps(meta,indent=2));raise SystemExit(0 if meta['status']=='PROCESS_COMPLETED' else 1)
