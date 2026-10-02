"""Own-process bounded read, no model output."""
import hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
r=Path(__file__).resolve().parent;out=r/'read-01';out.mkdir(exist_ok=False)
assert len(sys.argv)==2 and sys.argv[1].strip()
sha=lambda b:hashlib.sha256(b).hexdigest();source=Path('/workspace/scratch/a29d03198654/Maz543/testcar/outputs/cloud-va180-textured-20261001/MAZ543A_Textured.blend');original='6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266';assert sha(source.read_bytes())==original
tool=Path('/workspace/scratch/a29d03198654/maz543-tools/blender-4.5.13-linux-x64/blender');assert sha(tool.read_bytes())=='e3ce4e960a2fd3beb1f9d2299e38b3804475ccd395193013aec239a4b75bfbfe'
script=r/'read-nodes.py';compile(script.read_text(),str(script),'exec');(out/script.name).write_bytes(script.read_bytes());(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes());cpu=min(os.sched_getaffinity(0))
cmd=['taskset','-c',str(cpu),str(tool),'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','1','--python',str(out/script.name),'--',str(out/'native-report.json')]
record={'status':'RUNNING','script_sha256':sha(script.read_bytes()),'command':cmd,'handoff_note':sys.argv[1],'child_budget_seconds':45,'cleanup_budget_seconds':3,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};(out/'launch.json').write_text(json.dumps(record,indent=2)+'\n');start=time.monotonic();proc=None
env=dict(os.environ);env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
try:
 with (out/'run.log').open('xb') as log:proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);proc.wait(timeout=45)
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
 record.update(termination_status='NOT_LAUNCHED' if proc is None else 'CHILD_EXIT_CONFIRMED' if proc.poll() is not None else 'TERMINATION_UNCONFIRMED',elapsed_seconds=time.monotonic()-start,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_sha256_after=sha(source.read_bytes()),peak_child_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
 nr=out/'native-report.json';record['native_status']=json.loads(nr.read_text())['status'] if nr.exists() else None;passed=record.get('exit_code')==0 and record['termination_status']=='CHILD_EXIT_CONFIRMED' and record['source_sha256_after']==original and record['native_status']=='ACTUAL_NODE_READ_COMPLETE_NO_TIMELINE_QUALIFICATION';record['status']='READ_COMPLETE' if passed else 'READ_INCOMPLETE';(out/'process.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
raise SystemExit(0 if passed else 1)
