"""One bounded own-child fresh-open verification; no renderer or model mutation."""
import hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent;attempt=root/'fixed-01';out=root/'fresh-01';out.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();I=json.loads((attempt/'inputs.json').read_text())
native=json.loads((attempt/'native-report.json').read_text());asset=Path(native['saved_path']);source=Path(I['source_path']);tool=Path(I['blender_path'])
assert sha(asset.read_bytes())==native['saved_sha256'] and sha(source.read_bytes())==I['source_sha256'] and sha(tool.read_bytes())==I['blender_executable_sha256']
script=root/'verify-saved.py';compile(script.read_text(),str(script),'exec');(out/script.name).write_bytes(script.read_bytes());(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
assert len(sys.argv)==2 and sys.argv[1].strip(), 'Confirmed native window note required'
cpus=sorted(os.sched_getaffinity(0))[:2];cmd=['taskset','-c',','.join(map(str,cpus)),str(tool),'--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',str(out/script.name),'--','--attempt',str(attempt),'--output',str(out/'native-report.json')]
record={'status':'RUNNING','command':cmd,'handoff_note':sys.argv[1],'child_budget_seconds':60,'cleanup_budget_seconds':3,'cpu_affinity':cpus,'script_sha256':sha(script.read_bytes()),'asset_sha256_before':native['saved_sha256'],'source_sha256_before':I['source_sha256'],'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(out/'launch.json').write_text(json.dumps(record,indent=2)+'\n');start=time.monotonic();proc=None
env=dict(os.environ);env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
try:
 with (out/'run.log').open('xb') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
  proc.wait(timeout=60)
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
 record.update(termination_status='NOT_LAUNCHED' if proc is None else 'CHILD_EXIT_CONFIRMED' if proc.poll() is not None else 'TERMINATION_UNCONFIRMED',elapsed_seconds=time.monotonic()-start,peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),asset_sha256_after=sha(asset.read_bytes()),source_sha256_after=sha(source.read_bytes()))
 nr=out/'native-report.json';record['native_status']=json.loads(nr.read_text())['status'] if nr.exists() else None
 passed=record.get('exit_code')==0 and record['termination_status']=='CHILD_EXIT_CONFIRMED' and record['native_status']=='FIXED_FRAME_SAVED_ARTIFACT_FRESH_OPEN_PASS' and record['asset_sha256_before']==record['asset_sha256_after'] and record['source_sha256_before']==record['source_sha256_after']
 record['status']='FRESH_OPEN_COMPLETE' if passed else 'FRESH_OPEN_INCOMPLETE';(out/'process.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
raise SystemExit(0 if passed else 1)
