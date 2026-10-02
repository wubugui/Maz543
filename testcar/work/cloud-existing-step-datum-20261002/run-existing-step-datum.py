#!/usr/bin/env python3
"""Explicit-path replay; freeze scripts, CPU1, hard 120-second native process bound."""
import argparse,hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser()
for n in ('blender','script','candidate','original','inventory','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
runner=a.out/'executed-runner.py';script=a.out/'executed-script.py'
shutil.copyfile(__file__,runner);shutil.copyfile(a.script,script)
cmd=[str(a.blender),'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','17','--python',str(script),'--']
for n in ('candidate','original','inventory'):cmd+=['--'+n,str(getattr(a,n))]
cmd+=['--out',str(a.out/'native')]
meta={'status':'IN_PROGRESS','command':cmd,'timeout_seconds':120,'threads':1,
 'script_sha256_start':sha(script),'runner_sha256_start':sha(runner),
 'input_sha256_start':{n:sha(getattr(a,n)) for n in ('candidate','original','inventory')},
 'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
def write():(a.out/'process.json').write_text(json.dumps(meta,indent=2)+'\n')
write();start=time.monotonic();env=dict(os.environ)
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (a.out/'native.log').open('w') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);meta['pid']=child.pid;write()
 try:code=child.wait(timeout=120);timed=False
 except subprocess.TimeoutExpired:child.kill();code=child.wait();timed=True
meta.update(status='PROCESS_COMPLETED' if code==0 and not timed else 'PROCESS_FAILED',exit_code=code,timed_out=timed,
 elapsed_seconds=time.monotonic()-start,peak_children_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
 script_sha256_end=sha(script),runner_sha256_end=sha(runner),log_sha256=sha(a.out/'native.log'),
 input_sha256_end={n:sha(getattr(a,n)) for n in ('candidate','original','inventory')},
 end_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
rp=a.out/'native/datum-report.json'
if rp.exists():
 r=json.loads(rp.read_text());meta.update(report_sha256=sha(rp),native_report_status=r['status'])
 if r['status']!='BOUNDED_ORIGINAL_STEP_DATUM_DIAGNOSTIC_COMPLETE':meta['status']='PROCESS_FAILED_EVIDENCE_INVALID'
else:meta['status']='PROCESS_FAILED_MISSING_REPORT'
if meta['script_sha256_start']!=meta['script_sha256_end'] or meta['runner_sha256_start']!=meta['runner_sha256_end'] or meta['input_sha256_start']!=meta['input_sha256_end']:meta['status']='PROCESS_FAILED_HASH_CHANGED'
write()
if meta['status']!='PROCESS_COMPLETED':(a.out/'FAILURE.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2));raise SystemExit(0 if meta['status']=='PROCESS_COMPLETED' else 1)
