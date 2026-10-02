"""One unchanged-pose source view, CPU2, bounded child with real progress logs."""
import hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'view-01'
assert len(sys.argv)==2 and sys.argv[1].strip()
sha=lambda b:hashlib.sha256(b).hexdigest();source=Path('/workspace/scratch/a29d03198654/maz-textured-front-wheel-fixed-20261002/fixed-01/MAZ543A_Textured_Front_Wheel_Parent_Study.blend');expected='48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea'
assert source.stat().st_size==100052636 and sha(source.read_bytes())==expected
fresh=json.loads((source.parents[1]/'fresh-01/native-report.json').read_text());assert fresh['status']=='FIXED_FRAME_SAVED_ARTIFACT_FRESH_OPEN_PASS' and fresh['artifact_sha256']==expected
tool=Path('/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/blender');assert sha(tool.read_bytes())=='e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe'
script=root/'render-saved-view.py';compile(script.read_text(),str(script),'exec');prep=json.loads((root/'PREPARATION.json').read_text())
assert sha(script.read_bytes())==prep['script_sha256'] and sha(Path(__file__).read_bytes())==prep['runner_sha256']
out.mkdir(exist_ok=False);(out/script.name).write_bytes(script.read_bytes());(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes());(out/'PREPARATION.json').write_bytes((root/'PREPARATION.json').read_bytes())
cpus=sorted(os.sched_getaffinity(0))[:2];cmd=['taskset','-c',','.join(map(str,cpus)),str(tool),'--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',str(out/script.name),'--',str(out)]
record={'status':'RUNNING','command':cmd,'handoff_note':sys.argv[1],'source_sha256_before':expected,'script_sha256':sha(script.read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),'cpu_affinity':cpus,'child_execution_budget_seconds':240,'cleanup_budget_seconds':3,'budget_scope':'Own child wall time and cleanup; input hashing/final report I/O are outside this bound.','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};(out/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
env=dict(os.environ);env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',HIP_VISIBLE_DEVICES='',ROCR_VISIBLE_DEVICES='',ONEAPI_DEVICE_SELECTOR='*:cpu',PYTHONDONTWRITEBYTECODE='1')
proc=None;start=time.monotonic()
try:
 with (out/'run.log').open('xb') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
  while True:
   remaining=240-(time.monotonic()-start)
   if remaining<=0:raise subprocess.TimeoutExpired(cmd,240)
   try:proc.wait(timeout=min(12,remaining));break
   except subprocess.TimeoutExpired:
    logdata=(out/'run.log').read_bytes()[-4096:].decode(errors='replace').splitlines()
    h={'elapsed_seconds':time.monotonic()-start,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'log_bytes':(out/'run.log').stat().st_size,'last_log':logdata[-1] if logdata else None,'native_report_present':(out/'native-report.json').exists()}
    with (out/'heartbeat.jsonl').open('a') as f:f.write(json.dumps(h)+'\n')
    print(json.dumps(h),flush=True)
 record.update(exit_code=proc.returncode,timed_out=False)
except subprocess.TimeoutExpired:record.update(exit_code=None,timed_out=True)
except BaseException as exc:record.update(exit_code=None,error=type(exc).__name__+': '+str(exc))
finally:
 if proc is not None and proc.poll() is None:
  try:
   proc.terminate()
   try:proc.wait(timeout=1)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
  except BaseException as exc:record['cleanup_error']=type(exc).__name__+': '+str(exc)
 record.update(termination_status='NOT_LAUNCHED' if proc is None else 'CHILD_EXIT_CONFIRMED' if proc.poll() is not None else 'TERMINATION_UNCONFIRMED',elapsed_seconds=time.monotonic()-start,peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_sha256_after=sha(source.read_bytes()))
 nr=out/'native-report.json';record['native_status']=json.loads(nr.read_text())['status'] if nr.exists() else None
 passed=record.get('exit_code')==0 and record['termination_status']=='CHILD_EXIT_CONFIRMED' and record['source_sha256_after']==expected and record['native_status']=='SAVED_CANDIDATE_VIEW_COMPLETE';record['status']='NATIVE_VIEW_COMPLETE' if passed else 'NATIVE_VIEW_INCOMPLETE';(out/'process.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
raise SystemExit(0 if passed else 1)
